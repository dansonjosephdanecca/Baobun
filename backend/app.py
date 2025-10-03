from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
from typing import List, Optional
import uuid
from datetime import datetime
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import ChatMessage, ChatRequest, ChatResponse, MessageRole
from database import Database
from ollama_service import OllamaService
from search_service import SearchService

# Initialize FastAPI app
app = FastAPI(title="Bao Chat API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database()
ollama = OllamaService()
search = SearchService()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Serve frontend files
@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

# Static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    ollama_status = await ollama.check_connection()
    return {
        "status": "healthy",
        "ollama_connected": ollama_status,
        "model": ollama.model
    }

# Check and install Ollama model
@app.post("/setup/model")
async def setup_model():
    """Check if model is available and pull if needed"""
    is_available = await ollama.check_connection()
    if not is_available:
        success = await ollama.pull_model()
        return {"status": "pulled" if success else "failed", "model": ollama.model}
    return {"status": "available", "model": ollama.model}

# Get conversation history
@app.get("/conversations")
async def get_conversations():
    conversations = await db.get_all_conversations()
    return conversations

@app.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, limit: int = 50):
    messages = await db.get_conversation_history(conversation_id, limit)
    return [msg.dict() for msg in messages]

# Delete conversation
@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    await db.delete_conversation(conversation_id)
    return {"status": "deleted", "conversation_id": conversation_id}

# WebSocket endpoint for real-time chat
@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await manager.connect(websocket)

    try:
        # Send conversation history
        history = await db.get_conversation_history(conversation_id)
        await websocket.send_json({
            "type": "history",
            "messages": [msg.dict() for msg in history]
        })

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "chat":
                user_message = message_data.get("message", "")

                # Save user message
                user_msg = ChatMessage(
                    role=MessageRole.USER,
                    content=user_message,
                    timestamp=datetime.now()
                )
                await db.save_message(conversation_id, user_msg)

                # Check if search is needed
                search_results = None
                search_summary = ""

                if ollama.should_search(user_message) and message_data.get("enable_search", True):
                    # Send search status
                    await websocket.send_json({
                        "type": "status",
                        "message": "Searching the web..."
                    })

                    # Perform search
                    results, summary = await search.search_and_summarize(user_message)
                    search_results = [r.dict() for r in results]
                    search_summary = summary

                    # Send search results
                    await websocket.send_json({
                        "type": "search_results",
                        "results": search_results
                    })

                # Prepare context with search results
                context = await db.get_conversation_history(conversation_id)
                enhanced_prompt = user_message
                if search_summary:
                    enhanced_prompt = f"{user_message}\n\n{search_summary}"

                # Generate response
                await websocket.send_json({
                    "type": "status",
                    "message": "Bao is thinking..."
                })

                # Stream response from Ollama
                full_response = ""
                await websocket.send_json({
                    "type": "response_start"
                })

                async for chunk in ollama.generate_response(enhanced_prompt, context, stream=True):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "response_chunk",
                        "content": chunk
                    })

                await websocket.send_json({
                    "type": "response_end"
                })

                # Save assistant message
                assistant_msg = ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    timestamp=datetime.now(),
                    requires_search=bool(search_results),
                    search_results=search_results
                )
                await db.save_message(conversation_id, assistant_msg)

            elif message_data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Create new conversation
@app.post("/conversations")
async def create_conversation():
    conversation_id = await db.create_conversation()
    return {"conversation_id": conversation_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
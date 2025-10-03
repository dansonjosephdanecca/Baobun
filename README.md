# 🥟 Bao Chat - Your Friendly AI Assistant

<div align="center">
  <img src="frontend/assets/bao-icon.svg" width="120" height="120" alt="Bao the AI Assistant">

  *A cute, local AI chatbot running on your Raspberry Pi 400*
</div>

## 🌟 Features

- **🤖 Local AI**: Powered by Ollama and TinyLlama - no cloud required!
- **🔍 Web Search**: Searches the internet using DuckDuckGo (no API keys needed)
- **💬 Real-time Chat**: WebSocket-based chat with streaming responses
- **🎨 Bao-bun Theme**: Beautiful green and brown color scheme with cute bao-bun avatar
- **📱 Responsive**: Works on desktop, tablet, and mobile
- **🔒 Private**: All conversations stored locally on your device
- **⚡ Optimized**: Designed specifically for Raspberry Pi 400's 4GB RAM

## 🛠️ Quick Setup

### Prerequisites

- Raspberry Pi 400 (or Pi 4 with 4GB+ RAM)
- Raspberry Pi OS (64-bit) - Bookworm recommended
- Internet connection for initial setup

### One-Command Installation

```bash
git clone https://github.com/dansonjosephdanecca/Baobun.git
cd Baobun
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Install Ollama and TinyLlama model
- Set up Python environment and dependencies
- Create a systemd service for auto-start
- Configure everything for optimal Pi 400 performance

### Manual Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dansonjosephdanecca/Baobun.git
   cd Baobun
   ```

2. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama pull tinyllama
   ```

3. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run Bao Chat**
   ```bash
   python backend/app.py
   ```

## 🚀 Usage

1. **Start the application**
   ```bash
   # Option 1: Manual start
   source venv/bin/activate
   python backend/app.py

   # Option 2: Using systemd service
   sudo systemctl start baochat
   ```

2. **Access the web interface**
   - Local: http://localhost:8000
   - From other devices: http://[PI_IP_ADDRESS]:8000

3. **Start chatting with Bao!**
   - Ask questions about current events (web search enabled)
   - Have general conversations
   - Get help with various topics

## 🏗️ Architecture

### Backend (`backend/`)
- **FastAPI** - Modern Python web framework
- **WebSockets** - Real-time communication
- **SQLite** - Local conversation storage
- **Ollama Integration** - Local LLM inference
- **DuckDuckGo Search** - Web search using curl (no API keys)

### Frontend (`frontend/`)
- **Vanilla JavaScript** - Lightweight and fast
- **WebSocket Client** - Real-time chat
- **Responsive CSS** - Works on all devices
- **Bao-bun Theme** - Custom green/brown design

### Key Components

- **`app.py`** - Main FastAPI application
- **`ollama_service.py`** - Ollama/TinyLlama integration
- **`search_service.py`** - Web search using curl
- **`database.py`** - SQLite conversation management
- **`models.py`** - Pydantic data models

## 🎨 Design Philosophy

Bao is designed to be:
- **Friendly**: Warm, approachable personality
- **Helpful**: Always eager to assist
- **Private**: No data leaves your Pi
- **Efficient**: Optimized for Pi 400 hardware
- **Cute**: Bao-bun aesthetic with steamed bun charm!

## 🔧 Configuration

### Environment Variables
Create a `.env` file for custom configuration:
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=tinyllama
DATABASE_PATH=data/conversations.db
PORT=8000
```

### Model Options
While TinyLlama is recommended for Pi 400, you can try:
- `phi3:mini` - Slightly larger but more capable
- `qwen2:0.5b` - Even smaller, faster responses
- `gemma:2b` - If you have 8GB Pi model

## 📊 Performance Tips

### For Raspberry Pi 400 (4GB RAM):
- Stick with TinyLlama model
- Enable swap if needed: `sudo dphys-swapfile setup`
- Close unnecessary applications
- Use ethernet for best performance

### For Raspberry Pi 4/5 (8GB RAM):
- Try larger models like `phi3:mini`
- Better multitasking capability
- Faster response times

## 🛠️ Development

### Running in Development Mode
```bash
source venv/bin/activate

# Backend (with auto-reload)
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# Check Ollama status
curl http://localhost:11434/api/tags
```

### Project Structure
```
BaoChat/
├── backend/           # Python FastAPI backend
├── frontend/          # HTML/CSS/JS frontend
├── data/             # SQLite database storage
├── venv/             # Python virtual environment
├── setup.sh          # Installation script
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m "Add feature"`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** - For making local LLMs accessible
- **TinyLlama** - Efficient small language model
- **FastAPI** - Modern Python web framework
- **DuckDuckGo** - Privacy-focused search engine

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/dansonjosephdanecca/Baobun/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dansonjosephdanecca/Baobun/discussions)

---

<div align="center">
  <img src="frontend/assets/bao-icon.svg" width="60" height="60" alt="Bao">

  **Made with 💚 for Raspberry Pi enthusiasts**

  *Bao is ready to help! 🥟*
</div>
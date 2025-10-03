import subprocess
import asyncio
from typing import List, Optional
from bs4 import BeautifulSoup
import re
import urllib.parse
from models import SearchResult
import aiohttp
import json

class SearchService:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Safari/537.36"

    async def search_duckduckgo_curl(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search DuckDuckGo using curl command and parse HTML results"""
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        # Use curl command to fetch search results
        curl_command = [
            'curl',
            '-s',  # Silent mode
            '-L',  # Follow redirects
            '-H', f'User-Agent: {self.user_agent}',
            url
        ]

        try:
            # Run curl command
            process = await asyncio.create_subprocess_exec(
                *curl_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"Curl error: {stderr.decode()}")
                return []

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(stdout.decode('utf-8'), 'html.parser')
            results = []

            # Find search result divs
            result_divs = soup.find_all('div', class_='result__body')[:max_results]

            for div in result_divs:
                try:
                    # Extract title and URL
                    title_elem = div.find('a', class_='result__a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')

                    # Extract snippet
                    snippet_elem = div.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet[:200],  # Limit snippet length
                            source="DuckDuckGo"
                        ))
                except Exception as e:
                    print(f"Error parsing result: {e}")
                    continue

            return results

        except Exception as e:
            print(f"Search error: {e}")
            return []

    async def search_with_fallback(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search with fallback to alternative method if curl fails"""
        # Try curl method first
        results = await self.search_duckduckgo_curl(query, max_results)

        # If curl fails, try alternative lightweight search
        if not results:
            results = await self.search_lite(query, max_results)

        return results

    async def search_lite(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Lightweight search using DuckDuckGo Lite"""
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"

        curl_command = [
            'curl',
            '-s',
            '-L',
            '-H', f'User-Agent: {self.user_agent}',
            '--max-time', '10',  # 10 second timeout
            url
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *curl_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return []

            # Parse the lite HTML
            soup = BeautifulSoup(stdout.decode('utf-8'), 'html.parser')
            results = []

            # Find all links in the results
            for idx, link in enumerate(soup.find_all('a', href=True)[:max_results * 2]):
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Filter out DuckDuckGo internal links
                if href and not href.startswith('/') and 'duckduckgo.com' not in href:
                    # Try to get the next sibling for snippet
                    snippet = ""
                    next_elem = link.find_next_sibling()
                    if next_elem:
                        snippet = next_elem.get_text(strip=True)[:150]

                    results.append(SearchResult(
                        title=text[:100] if text else "No title",
                        url=href,
                        snippet=snippet,
                        source="DuckDuckGo Lite"
                    ))

                    if len(results) >= max_results:
                        break

            return results

        except Exception as e:
            print(f"Lite search error: {e}")
            return []

    def extract_key_info(self, search_results: List[SearchResult]) -> str:
        """Extract and summarize key information from search results"""
        if not search_results:
            return "No search results found."

        summary = "Based on web search:\n\n"
        for idx, result in enumerate(search_results[:3], 1):
            summary += f"{idx}. {result.title}\n"
            if result.snippet:
                summary += f"   {result.snippet}\n"
            summary += f"   Source: {result.url}\n\n"

        return summary

    async def search_and_summarize(self, query: str) -> tuple[List[SearchResult], str]:
        """Search and return both results and summary"""
        results = await self.search_with_fallback(query)
        summary = self.extract_key_info(results)
        return results, summary
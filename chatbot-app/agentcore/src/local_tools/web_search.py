"""
Local Web Search Tools — DuckDuckGo + URL Fetcher
Replaces Gateway Lambda web-search tools for local development.
"""

import logging
from strands import tool
from skill import skill

logger = logging.getLogger(__name__)


@skill(name="web-search")
@tool
def ddg_web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo. Returns relevant search results for a given query.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default 5, max 10)
    """
    try:
        from duckduckgo_search import DDGS

        max_results = min(max_results, 10)
        results = []

        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })

        if not results:
            return f"No results found for: {query}"

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. **{r['title']}**\n   URL: {r['url']}\n   {r['snippet']}")

        return "\n\n".join(formatted)

    except ImportError:
        return "Error: duckduckgo-search package not installed. Run: pip install duckduckgo-search"
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return f"Search failed: {str(e)}"


@skill(name="web-search")
@tool
def fetch_url_content(url: str, max_chars: int = 10000) -> str:
    """Fetch and extract text content from a URL. Useful for reading web pages, articles, documentation.

    Args:
        url: The URL to fetch content from
        max_chars: Maximum characters to return (default 10000)
    """
    try:
        import urllib.request
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; StrandsBot/1.0)"
        }
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")

        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... [truncated, {len(text) - max_chars} chars omitted]"

        return text if text else "No readable content found at this URL."

    except ImportError:
        return "Error: beautifulsoup4 package not installed. Run: pip install beautifulsoup4"
    except Exception as e:
        logger.error(f"URL fetch error: {e}")
        return f"Failed to fetch URL: {str(e)}"

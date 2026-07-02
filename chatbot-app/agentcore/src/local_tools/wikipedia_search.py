"""
Local Wikipedia Tools
Replaces Gateway Lambda wikipedia tools for local development.
"""

import logging
from strands import tool
from skill import skill

logger = logging.getLogger(__name__)


@skill(name="wikipedia-search")
@tool
def wikipedia_search(query: str, max_results: int = 5) -> str:
    """Search Wikipedia for articles matching a query. Returns titles and summaries.

    Args:
        query: The search query
        max_results: Maximum number of results (default 5)
    """
    try:
        import wikipediaapi

        wiki = wikipediaapi.Wikipedia(
            user_agent="StrandsAgent/1.0 (local-dev)",
            language="en"
        )

        # Use the search functionality via page suggestions
        # wikipediaapi doesn't have direct search, so we use the page directly
        page = wiki.page(query)

        if page.exists():
            summary = page.summary[:500] if len(page.summary) > 500 else page.summary
            return f"**{page.title}**\nURL: {page.fullurl}\n\n{summary}"
        else:
            # Try a broader approach
            return f"No Wikipedia article found for: {query}. Try a more specific or alternative term."

    except ImportError:
        return "Error: Wikipedia-API package not installed. Run: pip install Wikipedia-API"
    except Exception as e:
        logger.error(f"Wikipedia search error: {e}")
        return f"Wikipedia search failed: {str(e)}"


@skill(name="wikipedia-search")
@tool
def wikipedia_get_article(title: str, max_chars: int = 5000) -> str:
    """Get full Wikipedia article content by exact title.

    Args:
        title: The exact Wikipedia article title
        max_chars: Maximum characters to return (default 5000)
    """
    try:
        import wikipediaapi

        wiki = wikipediaapi.Wikipedia(
            user_agent="StrandsAgent/1.0 (local-dev)",
            language="en"
        )

        page = wiki.page(title)

        if not page.exists():
            return f"Article not found: {title}"

        text = page.text
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... [truncated, {len(text) - max_chars} chars omitted]"

        return f"**{page.title}**\nURL: {page.fullurl}\n\n{text}"

    except ImportError:
        return "Error: Wikipedia-API package not installed. Run: pip install Wikipedia-API"
    except Exception as e:
        logger.error(f"Wikipedia article error: {e}")
        return f"Failed to get article: {str(e)}"

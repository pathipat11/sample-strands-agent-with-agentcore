"""
Local ArXiv Tools
Replaces Gateway Lambda arxiv tools for local development.
"""

import logging
from strands import tool
from skill import skill

logger = logging.getLogger(__name__)


@skill(name="arxiv-search")
@tool
def arxiv_search(query: str, max_results: int = 5) -> str:
    """Search academic papers on ArXiv. Returns titles, authors, and summaries.

    Args:
        query: The search query for academic papers
        max_results: Maximum number of results (default 5, max 10)
    """
    try:
        import arxiv

        max_results = min(max_results, 10)
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = []
        for paper in client.results(search):
            authors = ", ".join([a.name for a in paper.authors[:3]])
            if len(paper.authors) > 3:
                authors += f" (+{len(paper.authors) - 3} more)"

            summary = paper.summary[:300] if len(paper.summary) > 300 else paper.summary
            summary = summary.replace("\n", " ")

            results.append(
                f"**{paper.title}**\n"
                f"Authors: {authors}\n"
                f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
                f"URL: {paper.entry_id}\n"
                f"Summary: {summary}"
            )

        if not results:
            return f"No papers found for: {query}"

        return "\n\n---\n\n".join(results)

    except ImportError:
        return "Error: arxiv package not installed. Run: pip install arxiv"
    except Exception as e:
        logger.error(f"ArXiv search error: {e}")
        return f"ArXiv search failed: {str(e)}"


@skill(name="arxiv-search")
@tool
def arxiv_get_paper(paper_id: str) -> str:
    """Get detailed information about a specific ArXiv paper by its ID.

    Args:
        paper_id: The ArXiv paper ID (e.g., '2301.07041' or full URL)
    """
    try:
        import arxiv

        # Clean up paper_id if full URL given
        if "arxiv.org" in paper_id:
            paper_id = paper_id.split("/")[-1]

        client = arxiv.Client()
        search = arxiv.Search(id_list=[paper_id])

        results = list(client.results(search))
        if not results:
            return f"Paper not found: {paper_id}"

        paper = results[0]
        authors = ", ".join([a.name for a in paper.authors])

        return (
            f"**{paper.title}**\n\n"
            f"Authors: {authors}\n"
            f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
            f"Updated: {paper.updated.strftime('%Y-%m-%d')}\n"
            f"Categories: {', '.join(paper.categories)}\n"
            f"PDF: {paper.pdf_url}\n"
            f"URL: {paper.entry_id}\n\n"
            f"**Abstract:**\n{paper.summary}"
        )

    except ImportError:
        return "Error: arxiv package not installed. Run: pip install arxiv"
    except Exception as e:
        logger.error(f"ArXiv get paper error: {e}")
        return f"Failed to get paper: {str(e)}"

"""Local tools for general-purpose tasks

Includes local replacements for Gateway Lambda tools (web search, Wikipedia,
ArXiv, Finance, Weather) plus visualization/workspace tools.
"""

from .visualization import create_visualization
from .excalidraw import create_excalidraw_diagram
from .workspace import workspace_list, workspace_read, workspace_write

# Local tool replacements for Gateway Lambda functions
from .web_search import ddg_web_search, fetch_url_content
from .wikipedia_search import wikipedia_search, wikipedia_get_article
from .arxiv_search import arxiv_search, arxiv_get_paper
from .finance import stock_quote, stock_history, stock_analysis
from .weather import get_today_weather, get_weather_forecast

__all__ = [
    'create_visualization',
    'create_excalidraw_diagram',
    'workspace_list',
    'workspace_read',
    'workspace_write',
    # Web search & URL
    'ddg_web_search',
    'fetch_url_content',
    # Wikipedia
    'wikipedia_search',
    'wikipedia_get_article',
    # ArXiv
    'arxiv_search',
    'arxiv_get_paper',
    # Finance
    'stock_quote',
    'stock_history',
    'stock_analysis',
    # Weather
    'get_today_weather',
    'get_weather_forecast',
]

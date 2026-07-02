"""
Local Finance Tools — Yahoo Finance
Replaces Gateway Lambda finance tools for local development.
"""

import logging
from strands import tool
from skill import skill

logger = logging.getLogger(__name__)


@skill(name="financial-news")
@tool
def stock_quote(symbol: str) -> str:
    """Get current stock quote and key metrics for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA')
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol.upper())
        info = ticker.info

        if not info or "regularMarketPrice" not in info:
            # Try fast_info as fallback
            fast = ticker.fast_info
            if hasattr(fast, "last_price") and fast.last_price:
                return (
                    f"**{symbol.upper()}**\n"
                    f"Price: ${fast.last_price:.2f}\n"
                    f"Market Cap: ${fast.market_cap:,.0f}\n"
                )
            return f"No data found for symbol: {symbol}"

        price = info.get("regularMarketPrice") or info.get("currentPrice", "N/A")
        prev_close = info.get("previousClose", "N/A")
        market_cap = info.get("marketCap", 0)
        pe_ratio = info.get("trailingPE", "N/A")
        week_high = info.get("fiftyTwoWeekHigh", "N/A")
        week_low = info.get("fiftyTwoWeekLow", "N/A")
        volume = info.get("volume", "N/A")
        name = info.get("shortName", symbol.upper())

        # Format market cap
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            if market_cap >= 1e12:
                mc_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                mc_str = f"${market_cap/1e9:.2f}B"
            else:
                mc_str = f"${market_cap/1e6:.2f}M"
        else:
            mc_str = "N/A"

        vol_str = f"{volume:,}" if isinstance(volume, (int, float)) else str(volume)

        return (
            f"**{name} ({symbol.upper()})**\n\n"
            f"Price: ${price}\n"
            f"Previous Close: ${prev_close}\n"
            f"Market Cap: {mc_str}\n"
            f"P/E Ratio: {pe_ratio}\n"
            f"52-Week High: ${week_high}\n"
            f"52-Week Low: ${week_low}\n"
            f"Volume: {vol_str}"
        )

    except ImportError:
        return "Error: yfinance package not installed. Run: pip install yfinance"
    except Exception as e:
        logger.error(f"Stock quote error: {e}")
        return f"Failed to get quote for {symbol}: {str(e)}"


@skill(name="financial-news")
@tool
def stock_history(symbol: str, period: str = "1mo") -> str:
    """Get historical stock price data.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        period: Time period - '1d', '5d', '1mo', '3mo', '6mo', '1y', '5y' (default '1mo')
    """
    try:
        import yfinance as yf

        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
        if period not in valid_periods:
            period = "1mo"

        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)

        if hist.empty:
            return f"No historical data found for {symbol} (period: {period})"

        # Format as table
        lines = [f"**{symbol.upper()} — Price History ({period})**\n"]
        lines.append("| Date | Open | High | Low | Close | Volume |")
        lines.append("|------|------|------|-----|-------|--------|")

        # Show max 20 rows
        df = hist.tail(20)
        for date, row in df.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            lines.append(
                f"| {date_str} | ${row['Open']:.2f} | ${row['High']:.2f} | "
                f"${row['Low']:.2f} | ${row['Close']:.2f} | {int(row['Volume']):,} |"
            )

        # Add summary
        if len(hist) > 1:
            start_price = hist.iloc[0]["Close"]
            end_price = hist.iloc[-1]["Close"]
            change = ((end_price - start_price) / start_price) * 100
            lines.append(f"\nChange over period: {change:+.2f}%")

        return "\n".join(lines)

    except ImportError:
        return "Error: yfinance package not installed. Run: pip install yfinance"
    except Exception as e:
        logger.error(f"Stock history error: {e}")
        return f"Failed to get history for {symbol}: {str(e)}"


@skill(name="financial-news")
@tool
def stock_analysis(symbol: str) -> str:
    """Get financial analysis including analyst recommendations and key financials.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol.upper())
        info = ticker.info

        if not info:
            return f"No data found for symbol: {symbol}"

        name = info.get("shortName", symbol.upper())
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        recommendation = info.get("recommendationKey", "N/A")
        target_price = info.get("targetMeanPrice", "N/A")
        revenue = info.get("totalRevenue", 0)
        profit_margin = info.get("profitMargins", 0)
        debt_equity = info.get("debtToEquity", "N/A")
        roe = info.get("returnOnEquity", 0)
        summary = info.get("longBusinessSummary", "No description available.")

        # Format revenue
        if isinstance(revenue, (int, float)) and revenue > 0:
            if revenue >= 1e9:
                rev_str = f"${revenue/1e9:.2f}B"
            else:
                rev_str = f"${revenue/1e6:.2f}M"
        else:
            rev_str = "N/A"

        lines = [
            f"**{name} ({symbol.upper()}) — Analysis**",
            "",
            f"Sector: {sector}",
            f"Industry: {industry}",
            "",
            f"**Analyst Consensus:** {recommendation}",
            f"**Target Price:** ${target_price}",
            "",
            "**Key Financials:**",
            f"- Revenue: {rev_str}",
        ]
        if isinstance(profit_margin, float):
            lines.append(f"- Profit Margin: {profit_margin*100:.1f}%")
        lines.append(f"- Debt/Equity: {debt_equity}")
        if isinstance(roe, float):
            lines.append(f"- ROE: {roe*100:.1f}%")
        lines.append("")
        lines.append(f"**Business Summary:**\n{summary[:500]}")

        result = "\n".join(lines)

        return result

    except ImportError:
        return "Error: yfinance package not installed. Run: pip install yfinance"
    except Exception as e:
        logger.error(f"Stock analysis error: {e}")
        return f"Failed to analyze {symbol}: {str(e)}"

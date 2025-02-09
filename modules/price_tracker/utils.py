from typing import Optional

def format_price(price: Optional[float]) -> str:
    """Format price with appropriate decimal places."""
    if price is None:
        return "N/A"
    
    if price < 0.01:
        return f"${price:.8f}"
    elif price < 1:
        return f"${price:.6f}"
    elif price < 1000:
        return f"${price:.4f}"
    else:
        return f"${price:,.2f}" 
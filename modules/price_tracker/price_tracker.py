import asyncio
import aiohttp
import requests
from typing import Optional
from ignis.widgets import (
    Widget,
    Label,
    Box
)
from ignis.utils import Utils
from ignis.app import IgnisApp

class PriceTracker(Widget.Box):
    """
    A widget that tracks and displays token prices from DexScreener.
    """
    
    def __init__(self, contract_id: str):
        # Create UI components first
        self.price_text = Label(
            label="Loading...",
            justify="center",
            wrap=True,
            wrap_mode="word",
            ellipsize="end"
        )
        self.price_text.add_css_class("price-value")
        
        self.symbol_text = Label(
            label="",
            justify="center",
            wrap=True,
            wrap_mode="word",
            ellipsize="end"
        )
        self.symbol_text.add_css_class("price-symbol")
        
        # Initialize parent with children
        super().__init__(
            vertical=False,
            spacing=0,
            child=[
                self.symbol_text,
                self.price_text
            ]
        )
        
        # Add CSS class to the container
        self.add_css_class("price-tracker")
        
        # Initialize other attributes
        self.contract_id = contract_id
        self.price: Optional[float] = None
        self.symbol: Optional[str] = None
        self.name: Optional[str] = None
        
        # Create poll for periodic updates (timeout in ms, callback)
        self._poll = Utils.Poll(60000, self._update_price)  # 60 seconds interval
        
    def on_map(self):
        """Called when the widget is mapped."""
        super().on_map()
        # Start initial price fetch and polling
        self._update_price(None)  # Pass None for initial call
        self._poll.start()
        
    def on_unmap(self):
        """Called when the widget is unmapped."""
        self._poll.stop()
        super().on_unmap()
        
    def _update_price(self, poll_instance=None):
        """Update the price display.
        
        Args:
            poll_instance: The Poll instance calling this method (can be None for manual calls)
        """
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{self.contract_id}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data and "pairs" in data and len(data["pairs"]) > 0:
                    pair = data["pairs"][0]
                    self.price = float(pair["priceUsd"])
                    self.symbol = pair["baseToken"]["symbol"]
                    self.name = pair["baseToken"]["name"]
                    
                    # Update UI
                    # self.symbol_text.label = f"{self.symbol} ({self.name})"
                    self.symbol_text.label = f"{self.symbol}="
                    self.price_text.label = f"${self.price:.6f}"
                else:
                    self.price_text.label = "Price unavailable"
            else:
                self.price_text.label = "Error fetching price"
                
        except Exception as e:
            print(f"Error updating price: {e}")
            self.price_text.label = "Error updating price"
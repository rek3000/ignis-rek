import os
from typing import Optional
from ignis.widgets import (
    Widget,
    Label,
    Box
)
from ignis.utils import Utils

class Battery(Widget.Box):
    """
    A widget that displays battery status and percentage.
    """
    
    def __init__(self):
        # Create UI components first
        self.percentage_text = Label(
            label="",
            justify="center",
            wrap=True,
            wrap_mode="word",
            # ellipsize="end"
        )
        self.percentage_text.add_css_class("battery-percentage")
        
        self.icon_text = Label(
            label="",
            justify="center",
            wrap=True,
            wrap_mode="word",
            # ellipsize="end"
        )
        self.icon_text.add_css_class("battery-icon")
        
        # Initialize parent with children
        super().__init__(
            vertical=False,
            spacing=0,
            child=[
                self.icon_text,
                self.percentage_text
            ]
        )
        
        # Add CSS class to the container
        self.add_css_class("battery-module")
        
        # Create poll for periodic updates
        self._poll = Utils.Poll(30000, self._update_battery)  # 30 seconds interval
        
    def on_map(self):
        """Called when the widget is mapped."""
        super().on_map()
        self._update_battery(None)  # Initial update
        self._poll.start()
        
    def on_unmap(self):
        """Called when the widget is unmapped."""
        self._poll.stop()
        super().on_unmap()
        
    def _get_battery_icon(self, percentage: int, charging: bool) -> str:
        """Get the appropriate battery icon based on percentage and charging status."""
        if charging:
            if percentage <= 20:
                return "󰢜"  # charging 20
            elif percentage <= 30:
                return "󰂆"  # charging 30
            elif percentage <= 40:
                return "󰂇"  # charging 40
            elif percentage <= 50:
                return "󰂈"  # charging 50
            elif percentage <= 60:
                return "󰢝"  # charging 60
            elif percentage <= 70:
                return "󰂉"  # charging 70
            elif percentage <= 80:
                return "󰂊"  # charging 80
            elif percentage <= 90:
                return "󰂋"  # charging 90
            else:
                return "󰂅"  # charging full
        else:
            if percentage <= 10:
                return "󰁺"  # critical
            elif percentage <= 20:
                return "󰁻"  # empty
            elif percentage <= 30:
                return "󰁼"  # low
            elif percentage <= 40:
                return "󰁽"  # medium-low
            elif percentage <= 50:
                return "󰁾"  # medium
            elif percentage <= 60:
                return "󰁿"  # medium-high
            elif percentage <= 70:
                return "󰂀"  # high
            elif percentage <= 80:
                return "󰂁"  # very high
            elif percentage <= 90:
                return "󰂂"  # almost full
            else:
                return "󰁹"  # full
    
    def _update_battery(self, poll_instance=None):
        """Update the battery display."""
        try:
            # Read battery percentage
            with open("/sys/class/power_supply/BAT1/capacity", "r") as f:
                percentage = int(f.read().strip())
            
            # Read charging status
            with open("/sys/class/power_supply/BAT1/status", "r") as f:
                status = f.read().strip()
            
            charging = status == "Charging"
            
            # Update icon and percentage
            icon = self._get_battery_icon(percentage, charging)
            self.icon_text.label = icon
            self.percentage_text.label = f"{percentage}%"
            
            # Add appropriate CSS classes
            self.remove_css_class("battery-low")
            self.remove_css_class("battery-charging")
            
            if charging:
                self.add_css_class("battery-charging")
            elif percentage <= 20:
                self.add_css_class("battery-low")
                
        except Exception as e:
            print(f"Error updating battery: {e}")
            self.icon_text.label = ""  # battery error icon
            self.percentage_text.label = "Error" 
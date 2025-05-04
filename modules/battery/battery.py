import os
import asyncio
from typing import Optional
from functools import partial
from ignis.widgets import (
    Widget,
    Label,
    Box,
    PopoverMenu,
    MenuItem,
    Button
)
from ignis.utils import Utils

class Battery(Widget.Box):
    """
    A widget that displays battery status and percentage with performance mode control.
    """
    
    def __init__(self):
        super().__init__(
            vertical=False,
            spacing=0,
        )

        # Create UI components first
        self.percentage_text = Label(
            label="",
            justify="center",
            wrap=True,
            wrap_mode="word",
        )
        self.percentage_text.add_css_class("battery-percentage")
        
        self.icon_text = Label(
            label="",
            justify="center",
            wrap=True,
            wrap_mode="word",
        )

        self.icon_text.add_css_class("battery-icon")

        # Create performance mode menu
        self.performance_menu = Widget.PopoverMenu(
            items=[
                Widget.MenuItem(
                    label="Performance",
                    on_activate=partial(self._set_power_profile, "performance"),
                ),
                Widget.MenuItem(
                    label="Balanced",
                    on_activate=partial(self._set_power_profile, "balanced"),
                ),
                Widget.MenuItem(
                    label="Power Saver",
                    on_activate=partial(self._set_power_profile, "power-saver"),
                ),
            ]
        )

        # Create a button to contain everything
        self.button = Widget.Button(
            child=Widget.Box(
                vertical=False,
                spacing=0,
                child=[
                    self.icon_text,
                    self.percentage_text,
                ]
            ),
            on_click=self._on_click
        )

        self.append(self.button)
        self.append(self.performance_menu)
        
        # Add CSS class to the container
        self.add_css_class("battery-module")
        self._is_setup = False
        
    async def setup(self):
        if self._is_setup:
            return
        await self._update_battery()
        self._is_setup = True

    async def __post_init__(self):
        await self.setup()

    def on_map(self):
        """Called when the widget is mapped."""
        super().on_map()
        asyncio.create_task(self.start_periodic_updates())
        
    def on_unmap(self):
        """Called when the widget is unmapped."""
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
    
    def _set_power_profile(self, profile, _):
        """Set the power profile using powerprofilesctl."""
        try:
            Utils.exec_sh_async(f"powerprofilesctl set {profile}")
        except Exception as e:
            print(f"Error setting power profile: {e}")

    def _on_click(self, _):
        """Show the performance mode menu when clicked."""
        self.performance_menu.popup()


    async def _read_file_async(self, filename: str):
        loop = asyncio.get_event_loop()
        with open(filename, "r") as f:
            content = await loop.run_in_executor(None, f.read)
        return content.strip()

    async def _update_battery(self):
        """Update the battery display."""
        try:
            percentage = int(await self._read_file_async("/sys/class/power_supply/BAT1/capacity"))
            status = await self._read_file_async("/sys/class/power_supply/BAT1/status")
            charging = status == "Charging"
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

    async def start_periodic_updates(self):
        while True:
            await self._update_battery()
            await asyncio.sleep(30)  # 30 seconds interval

import os
import asyncio
from typing import Optional
from functools import partial
import aiofiles
from ignis.widgets import (
    Widget,
    Label,
    Box,
    PopoverMenu,
    MenuItem, Button
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
        self.active_profile = "balanced"
        self._profile_loaded = False

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

        # Create performance mode menu items
        self.menu_items = {
            "performance": Widget.MenuItem(
                label="Performance",
                on_activate=partial(self._set_power_profile, "performance"),
            ),
            "balanced": Widget.MenuItem(
                label="Balanced",
                on_activate=partial(self._set_power_profile, "balanced"),
            ),
            "power-saver": Widget.MenuItem(
                label="Power Saver",
                on_activate=partial(self._set_power_profile, "power-saver"),
            ),
        }
        
        # Create performance mode menu
        self.performance_menu = Widget.PopoverMenu(
            items=list(self.menu_items.values())
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
        
        self.add_css_class("battery-module")
        self._is_setup = False
        
        self._update_menu_highlighting()
        
    async def _load_power_profile(self):
        """Load the current power profile asynchronously."""
        if not self._profile_loaded:
            try:
                result = await Utils.exec_sh_async("powerprofilesctl get")
                self.active_profile = result.stdout.strip()
                print(f"Loaded power profile: {self.active_profile}")
                self._profile_loaded = True
                self._update_menu_highlighting()
            except Exception as e:
                print(f"Error loading power profile: {e}")
                # Keep the default "balanced" profile

    def _update_menu_highlighting(self):
        """Update menu item highlighting based on active profile."""
        # Define the base labels
        profile_labels = {
            "performance": "Performance",
            "balanced": "Balanced", 
            "power-saver": "Power Saver"
        }
        
        # Recreate menu items with updated labels
        self.menu_items = {}
        menu_items_list = []
        
        for profile, base_label in profile_labels.items():
            # Add checkmark to active profile
            label = f"{base_label} ✓" if profile == self.active_profile else base_label
            
            menu_item = Widget.MenuItem(
                label=label,
                on_activate=partial(self._set_power_profile, profile),
            )
            
            self.menu_items[profile] = menu_item
            menu_items_list.append(menu_item)
        
        # Update the menu with new items
        self.performance_menu.items = menu_items_list

    async def setup(self):
        if self._is_setup:
            return
        await self._load_power_profile()
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
            asyncio.create_task(Utils.exec_sh_async(f"powerprofilesctl set {profile}"))
            # Update the active profile and menu highlighting
            self.active_profile = profile
            self._update_menu_highlighting()
            print(f"Power profile set to: {profile}")
        except Exception as e:
            print(f"Error setting power profile: {e}")

    def _on_click(self, _):
        """Show the performance mode menu when clicked."""
        self.performance_menu.popup()


    async def _read_file_async(self, filename: str):
        """Read file content asynchronously using aiofiles."""
        try:
            async with aiofiles.open(filename, "r") as f:
                content = await f.read()
            return content.strip()
        except FileNotFoundError:
            return ""
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            return ""

    async def _update_battery(self):
        """Update the battery display."""
        try:
            percentage = int(await self._read_file_async("/sys/class/power_supply/BAT1/capacity"))
            status = await self._read_file_async("/sys/class/power_supply/BAT1/status")
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

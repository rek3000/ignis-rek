from ignis.widgets import Widget
from ignis.services.system_tray import SystemTrayItem, SystemTrayService

import asyncio
from typing import Optional
import gi
gi.require_version('Gdk', '4.0')
gi.require_version('Gtk', '4.0')
from gi.repository import Gdk, Gtk, GLib

system_tray = SystemTrayService.get_default()

class TrayItemButton(Widget.Button):
    """
    A button widget representing a system tray item.
    
    Args:
        item: The system tray item to create a widget for
    """
    def __init__(self, item: SystemTrayItem):
        self.item = item
        self._icon = Widget.Icon(
            image=item.bind("icon"),
            pixel_size=24
        )
        
        # Create menu if available
        self._menu = None
        if item.menu:
            self._menu = item.menu.copy()
        
        # Create a box that contains both the icon and the menu
        # This ensures they're in the same container hierarchy
        self._box = Widget.Box(
            child=[
                self._icon,
                self._menu if self._menu else None
            ]
        )
        
        # Initialize the button
        super().__init__(
            child=self._box,
            tooltip_text=item.bind("tooltip"),
            on_click=self._on_click,
            on_right_click=self._on_right_click if item.menu else None,
            css_classes=["tray-item"]
        )
        
        # Connect to the removed signal
        item.connect("removed", self._on_removed)
    
    def _on_removed(self, _):
        # Clean up when the item is removed
        if self._icon.get_parent():
            self._icon.unparent()
        
        if self._menu and self._menu.get_parent():
            self._menu.unparent()
        
        if self._box.get_parent():
            self._box.unparent()
            
        # Finally unparent self
        self.unparent()
    
    def _on_click(self, _):
        # Use async version of activate
        asyncio.create_task(self.item.activate_async())
    
    def _on_right_click(self, _):
        """
        Handle right-click events by showing the menu.
        """
        if self._menu:
            # Since the menu is already in the same container, we can just call popup()
            self._menu.popup()

class TrayItem(Widget.Button):
    """
    A button widget representing a system tray item.
    """
    __gtype_name__ = "TrayItem"

    def __init__(self, item: SystemTrayItem):
        self.item = item
        
        # Create icon widget
        self._icon = Widget.Icon(
            image=item.bind("icon"),
            pixel_size=24
        )
        
        # Create menu if available
        self._menu = None
        if item.menu:
            self._menu = item.menu.copy()
        
        # Create a box that contains both the icon and the menu
        # This ensures they're in the same container hierarchy
        self._box = Widget.Box(
            child=[
                self._icon,
                self._menu if self._menu else None
            ]
        )
        
        # Initialize with the box as child
        super().__init__(
            child=self._box,
            tooltip_text=item.bind("tooltip"),
            on_click=self._on_click,
            on_right_click=self._on_right_click if item.menu else None,
            css_classes=["tray-item"]
        )
        
        self._is_setup = False 
    
    async def setup(self):
        if self._is_setup:
            return
        self.item.connect("removed", self._on_removed)
        self._is_setup = True

    def _on_removed(self, _):
        # Clean up when the item is removed
        if self._icon.get_parent():
            self._icon.unparent()
        
        if self._menu and self._menu.get_parent():
            self._menu.unparent()
        
        if self._box.get_parent():
            self._box.unparent()
            
        # Finally unparent self
        self.unparent()

    def _on_click(self, _):
        # Use async version of activate
        asyncio.create_task(self.item.activate_async())
    
    def _on_right_click(self, _):
        """
        Handle right-click events by showing the menu.
        """
        if self._menu:
            # Since the menu is already in the same container, we can just call popup()
            self._menu.popup()

class Tray(Widget.Box):
    """
    A widget that displays system tray items.
    """
    __gtype_name__ = "Tray"

    def __init__(self):
        super().__init__(
            spacing=5,
        )
        
        # Add CSS class
        self.add_css_class("system-tray")
        self._tray_items = []
        self._is_setup = False

    async def setup(self):
        if self._is_setup:
            return
        system_tray.connect("added", self._on_item_added)
        self._is_setup = True

    def __post_init__(self):
        asyncio.create_task(self.setup())

    def clear_tray_items(self):
        # Properly clean up each item before removing
        for item_widget in self._tray_items:
            # Ensure proper cleanup of each item
            if hasattr(item_widget, "_on_removed"):
                item_widget._on_removed(None)
            else:
                item_widget.unparent()
        self._tray_items.clear()

    def _on_item_added(self, service, item: SystemTrayItem):
        """
        Non-async wrapper for on_item_added that creates a task
        """
        asyncio.create_task(self.on_item_added(service, item))

    async def on_item_added(self, service, item: SystemTrayItem):
        """
        Handler for 'added' signal. Create and setup the TrayItem
        """
        tray_item_widget = TrayItem(item)
        await tray_item_widget.setup()
        self.append(tray_item_widget)
        self._tray_items.append(tray_item_widget)

def _show_menu_safely(menu, parent_widget, x=0, y=0):
    """
    Safely show a menu with proper GTK4 widget state management.
    
    Args:
        menu: The menu to show
        parent_widget: The widget that will be the parent of the menu
        x: X coordinate for the menu
        y: Y coordinate for the menu
    """
    if not menu:
        return
    
    # Ensure any previous parent relationship is cleaned up
    if menu.get_parent() and menu.get_parent() != parent_widget:
        menu.unparent()
        
    # Set the parent if needed
    if not menu.get_parent():
        menu.set_parent(parent_widget)
    
    # Use a GLib idle callback to ensure the menu is shown after the current event is processed
    def show_menu_idle():
        # Check if the widget is still valid and has a root
        if parent_widget.get_root():
            # Position the menu at the pointer or specified coordinates
            if x > 0 and y > 0:
                # Create a rectangle for positioning
                rect = Gdk.Rectangle()
                rect.x = x
                rect.y = y
                rect.width = 1
                rect.height = 1
                
                # Show the menu at the specified position
                menu.set_pointing_to(rect)
                menu.popup()
            else:
                # Just show the menu
                menu.popup()
        return False  # Remove the idle callback
    
    # Schedule the menu popup for the next idle time
    GLib.idle_add(show_menu_idle)

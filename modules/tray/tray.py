from ignis.widgets import Widget
from ignis.services.system_tray import SystemTrayItem, SystemTrayService

import asyncio
from typing import Optional

system_tray = SystemTrayService.get_default()

def tray_item(item: SystemTrayItem) -> Widget.Button:
    """
    Create a button widget for a system tray item.
    
    Args:
        item: The system tray item to create a widget for
        
    Returns:
        A Button widget representing the system tray item
    """
    # Create menu if available
    menu = item.menu.copy() if item.menu else None
    
    # Create the button widget
    button = Widget.Button(
        child=Widget.Box(
            child=[
                Widget.Icon(
                    image=item.bind("icon"),
                    pixel_size=24
                ),
                menu
            ]
        ),
        setup=lambda self: item.connect(
            "removed",
            lambda x: self.unparent()
        ),
        tooltip_text=item.bind("tooltip"),
        on_click=lambda x: item.activate(),  # Left-click: activate or show menu
        on_right_click=lambda x: menu.popup() if menu else None,
        css_classes=["tray-item"]
    )
    
    return button

class TrayItem(Widget.Button):
    """
    """
    __gtype_name__ = "TrayItem"

    def __init__(self, item: SystemTrayItem):
        self.item = item
        self._menu = item.menu.copy() if item.menu else None
        super().__init__(
            child=Widget.Box(
                child=[
                    Widget.Icon(
                        image=item.bind("icon"),
                        pixel_size=24
                        ),
                    ]
                ),
            tooltip_text=item.bind("tooltip"),
            on_click=self._on_click,
            on_right_click=self._on_right_click,
            css_classes=["tray-item"]
            ),
        self._is_setup = False 
    
    async def setup(self):
        if self._is_setup:
            return
        self.item.connect("removed", self._on_removed)
        self._is_setup = True

    def _on_removed(self, _):
        self.unparent()

    def _on_click(self, _):
        self.item.activate()

    def _on_right_click(self, _):
        if self._menu:
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

    def __port_init__(self):
        asyncio.create_task(self.setup())

    def clear_tray_items(self):
        for item_widget in self._tray_items:
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

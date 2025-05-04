from ignis.widgets import Widget
from ignis.services.system_tray import SystemTrayItem, SystemTrayService

import asyncio

system_tray = SystemTrayService.get_default()

class TrayItem(Widget.Button):
    """
    A button widget representing a system tray item.
    """
    __gtype_name__ = "TrayItem"

    def __init__(self, item: SystemTrayItem):
        self.item = item
        
        # Create menu if available
        self._menu = item.menu.copy() if item.menu else None
        
        # Initialize with box containing icon and menu
        super().__init__(
            child=Widget.Box(
                child=[
                    Widget.Icon(image=item.bind("icon"), pixel_size=24),
                    self._menu,
                ]
            ),
            tooltip_text=item.bind("tooltip"),
            on_click=self._on_click,
            on_right_click=lambda x: self._menu.popup() if self._menu else None,
            css_classes=["tray-item"]
        )
        
        # Connect to the removed signal
        item.connect("removed", lambda x: self.unparent())
    
    def _on_click(self, _):
        """
        Handle click events safely, catching DBus errors if the item doesn't support Activate.
        """
        try:
            # Try to activate the item asynchronously
            asyncio.create_task(self._safe_activate())
        except Exception:
            # If activation fails, show the menu if available
            if self._menu:
                self._menu.popup()
    
    async def _safe_activate(self):
        """
        Safely activate the item, catching DBus errors.
        """
        try:
            await self.item.activate_async()
        except Exception:
            # If activation fails, show the menu if available
            if self._menu:
                self._menu.popup()

class Tray(Widget.Box):
    """
    A widget that displays system tray items.
    """
    __gtype_name__ = "Tray"

    def __init__(self):
        super().__init__(spacing=5)
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
        self.append(tray_item_widget)
        self._tray_items.append(tray_item_widget)

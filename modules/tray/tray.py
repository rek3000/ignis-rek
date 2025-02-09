from ignis.widgets import Widget
from ignis.services.system_tray import SystemTrayItem, SystemTrayService

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

class Tray(Widget.Box):
    """
    A widget that displays system tray items.
    """
    def __init__(self):
        super().__init__(
            spacing=10,
            setup=lambda self: system_tray.connect(
                "added",
                lambda x, item: self.append(tray_item(item))
            )
        )
        
        # Add CSS class
        self.add_css_class("system-tray")

def create_tray() -> Tray:
    """
    Create a new system tray widget.
    
    Returns:
        A new Tray widget instance
    """
    return Tray()
from ignis.widgets import Widget
from ignis.services.hyprland import HyprlandService
from ignis.services.niri import NiriService

class WindowTitle(Widget.Label):
    """
    A widget that displays the title of the active window.
    Supports both Hyprland and Niri window managers.
    """
    
    def __init__(self, monitor_name: str = ""):
        # Store monitor name for Niri
        self._monitor_name = monitor_name
        
        # Get window manager services
        self.hyprland = HyprlandService.get_default()
        self.niri = NiriService.get_default()
        
        # Initialize parent with common properties
        super().__init__(
            ellipsize="end",
            max_width_chars=80
        )
        
        # Set up window manager specific bindings
        self._setup_bindings()
        
        # Add CSS class
        self.add_css_class("window-title")
    
    def _setup_bindings(self):
        """Set up the appropriate bindings based on available window manager."""
        if self.hyprland.is_available:
            self._setup_hyprland_bindings()
        elif self.niri.is_available:
            self._setup_niri_bindings()
        else:
            self.label = ""
    
    def _setup_hyprland_bindings(self):
        """Set up Hyprland-specific bindings."""
        self.label = self.hyprland.bind(
            "active_window",
            transform=lambda value: value.title
        )
    
    def _setup_niri_bindings(self):
        """Set up Niri-specific bindings."""
        # Bind visibility to active output
        self.visible = self.niri.bind(
            "active_output",
            lambda x: x["name"] == self._monitor_name
        )
        
        # Bind label to active window title
        self.label = self.niri.bind(
            "active_window",
            transform=lambda value: "" if value is None else value["title"]
        )

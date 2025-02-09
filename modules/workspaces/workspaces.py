from ignis.widgets import Widget
from ignis.services.hyprland import HyprlandService
from ignis.services.niri import NiriService

class Workspaces(Widget.EventBox):
    """
    A widget that displays and manages workspaces for Hyprland and Niri.
    """
    
    def __init__(self, monitor_name: str = ""):
        # Store monitor name for Niri
        self._monitor_name = monitor_name
        
        # Get window manager services
        self.hyprland = HyprlandService.get_default()
        self.niri = NiriService.get_default()
        
        # Initialize parent
        super().__init__(
            on_scroll_up=lambda x: self._scroll_workspaces("up"),
            on_scroll_down=lambda x: self._scroll_workspaces("down"),
            css_classes=["workspaces"],
            spacing=5,
            child=self._create_workspace_box()
        )
    
    def _create_workspace_box(self) -> Widget.Box:
        """Create the main workspace container with appropriate bindings."""
        if self.hyprland.is_available:
            return self.hyprland.bind(
                "workspaces",
                transform=lambda value: [self._create_workspace_button(i) for i in value]
            )
        elif self.niri.is_available:
            return self.niri.bind(
                "workspaces",
                transform=lambda value: [
                    self._create_workspace_button(i) 
                    for i in value 
                    if i["output"] == self._monitor_name
                ]
            )
        else:
            return Widget.Box()
    
    def _create_workspace_button(self, workspace: dict) -> Widget.Button:
        """Create a button for a single workspace."""
        if self.hyprland.is_available:
            return self._create_hyprland_button(workspace)
        elif self.niri.is_available:
            return self._create_niri_button(workspace)
        else:
            return Widget.Button()
    
    def _create_hyprland_button(self, workspace: dict) -> Widget.Button:
        """Create a Hyprland workspace button."""
        widget = Widget.Button(
            css_classes=["workspace"],
            on_click=lambda x, id=workspace["id"]: 
                self.hyprland.switch_to_workspace(id),
            child=Widget.Label(label=str(workspace["id"]))
        )
        
        if workspace["id"] == self.hyprland.active_workspace["id"]:
            widget.add_css_class("active")
            
        return widget
    
    def _create_niri_button(self, workspace: dict) -> Widget.Button:
        """Create a Niri workspace button."""
        widget = Widget.Button(
            css_classes=["workspace"],
            on_click=lambda x, id=workspace["idx"]: 
                self.niri.switch_to_workspace(id),
            child=Widget.Label(label=str(workspace["idx"]))
        )
        
        if workspace["is_active"]:
            widget.add_css_class("active")
            
        return widget
    
    def _scroll_workspaces(self, direction: str) -> None:
        """Handle workspace scrolling."""
        if self.hyprland.is_available:
            self._scroll_hyprland_workspaces(direction)
        elif self.niri.is_available:
            self._scroll_niri_workspaces(direction)
    
    def _scroll_hyprland_workspaces(self, direction: str) -> None:
        """Handle Hyprland workspace scrolling."""
        current = self.hyprland.active_workspace["id"]
        
        if direction == "up":
            target = current - 1
            self.hyprland.switch_to_workspace(target)
        else:
            target = current + 1
            if target == 11:  # Maximum workspace limit
                return
            self.hyprland.switch_to_workspace(target)
    
    def _scroll_niri_workspaces(self, direction: str) -> None:
        """Handle Niri workspace scrolling."""
        current = list(
            filter(
                lambda w: w["is_active"] and w["output"] == self._monitor_name,
                self.niri.workspaces
            )
        )[0]["idx"]
        
        if direction == "up":
            target = current + 1
            self.niri.switch_to_workspace(target)
        else:
            target = current - 1
            self.niri.switch_to_workspace(target)
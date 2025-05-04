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
        
        # Set up workspace change signals
        if self.hyprland.is_available:
            self.hyprland.connect("notify::active-workspace", lambda *_: self.update())
        elif self.niri.is_available:
            self.niri.connect("notify::workspaces", lambda *_: self.update())
    
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
        return Widget.Button(
            css_classes=["workspace"],
            on_click=lambda x, id=workspace.id: 
                self.hyprland.switch_to_workspace(id),
            child=Widget.Label(label=str(workspace.id))
        )
    
    def _create_niri_button(self, workspace: dict) -> Widget.Button:
        """Create a Niri workspace button."""
        return Widget.Button(
            css_classes=["workspace"],
            on_click=lambda x, id=workspace["idx"]: 
                self.niri.switch_to_workspace(id),
            child=Widget.Label(label=str(workspace["idx"]))
        )
    
    def update(self) -> None:
        """
        Update the active workspace CSS class.
        This function refreshes the workspace buttons to ensure the correct one has the 'active' class.
        """
        # Get all workspace buttons
        workspace_box = super().child
        if not workspace_box:
            return
            
        # Update active class for each workspace button
        for button in workspace_box:
            if not isinstance(button, Widget.Button):
                continue
                
            # Get workspace ID from the button's label
            label = button.child
            if not isinstance(label, Widget.Label):
                continue
                
            workspace_id = label.label
            if not workspace_id:
                continue
                
            try:
                workspace_id = int(workspace_id)
            except ValueError:
                continue
                
            # Update active class based on window manager
            if self.hyprland.is_available:
                is_active = workspace_id == self.hyprland.active_workspace.id
            elif self.niri.is_available:
                active_workspace = next(
                    (w for w in self.niri.workspaces if w["is_active"] and w["output"] == self._monitor_name),
                    None
                )
                is_active = active_workspace and workspace_id == active_workspace["idx"]
            else:
                is_active = False
                
            # Update CSS class
            if is_active:
                button.add_css_class("active")
            else:
                button.remove_css_class("active")
    
    def _scroll_workspaces(self, direction: str) -> None:
        """Handle workspace scrolling."""
        if self.hyprland.is_available:
            self._scroll_hyprland_workspaces(direction)
        elif self.niri.is_available:
            self._scroll_niri_workspaces(direction)
        
        # Update active workspace after scrolling
        self.update()
    
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
        active_workspace = next(
            (w for w in self.niri.workspaces if w["is_active"] and w["output"] == self._monitor_name),
            None
        )
        
        if not active_workspace:
            return
            
        current = active_workspace["idx"]
        
        if direction == "up":
            target = current + 1
            self.niri.switch_to_workspace(target)
        else:
            target = current - 1
            self.niri.switch_to_workspace(target)

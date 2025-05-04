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
            # Listen for active workspace changes
            self.hyprland.connect("notify::active-workspace", lambda *_: self.update())
            # Also listen for workspace list changes (added/removed workspaces)
            self.hyprland.connect("notify::workspaces", lambda *_: self.update())
            # Listen for monitor changes which can affect active workspaces
            self.hyprland.connect("notify::monitors", lambda *_: self.update())
            # Listen for special workspace changes
            for monitor in self.hyprland.monitors:
                monitor.connect("notify::special-workspace-id", lambda *_: self.update())
                monitor.connect("notify::special-workspace-name", lambda *_: self.update())
        elif self.niri.is_available:
            self.niri.connect("notify::workspaces", lambda *_: self.update())
    
    def _create_workspace_box(self) -> Widget.Box:
        """Create the main workspace container with appropriate bindings."""
        if self.hyprland.is_available:
            box = self.hyprland.bind(
                "workspaces",
                transform=lambda value: [self._create_workspace_button(i) for i in value]
            )
            
            # Add special workspaces if they exist
            self._add_special_workspaces(box)
            
            return box
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
            
    def _add_special_workspaces(self, box: Widget.Box) -> None:
        """Add special workspace buttons to the workspace box."""
        if not self.hyprland.is_available:
            return
            
        # Check each monitor for special workspaces
        for monitor in self.hyprland.monitors:
            if monitor.special_workspace_id and monitor.special_workspace_name:
                # Create a special workspace button
                special_button = self._create_special_workspace_button(
                    monitor.special_workspace_id, 
                    monitor.special_workspace_name,
                    monitor.name
                )
                box.append(special_button)
                
    def _create_special_workspace_button(self, workspace_id: str, workspace_name: str, monitor_name: str) -> Widget.Button:
        """Create a button for a special workspace."""
        # Create a container box for the workspace label and monitor indicator
        container = Widget.Box(
            spacing=2,
            css_classes=["workspace-container", "special-workspace"]
        )
        
        # Use a special label for special workspaces
        label_text = f"S:{workspace_name}" if workspace_name else "S"
        container.append(Widget.Label(label=label_text))
        
        # Add monitor indicator
        monitor_indicator = Widget.Label(
            label=str(monitor_name),
            css_classes=["monitor-indicator", "minimal"]
        )
        container.append(monitor_indicator)
        
        return Widget.Button(
            css_classes=["workspace", "special"],
            on_click=lambda x: self.hyprland.send_command(f"dispatch togglespecialworkspace {workspace_name}"),
            child=container
        )
    
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
        # Create a container box for the workspace label and monitor indicator
        container = Widget.Box(
            spacing=2,
            css_classes=["workspace-container"]
        )
        
        # Add workspace number label
        workspace_id = workspace.id if hasattr(workspace, 'id') else ''
        container.append(Widget.Label(label=str(workspace_id)))
        
        # Add monitor indicator if monitor information is available
        if hasattr(workspace, "monitor"):
            monitor_indicator = Widget.Label(
                label=str(workspace.monitor),
                css_classes=["monitor-indicator", "minimal"]
            )
            container.append(monitor_indicator)
        
        return Widget.Button(
            css_classes=["workspace"],
            on_click=lambda x, id=workspace_id: 
                self.hyprland.switch_to_workspace(id),
            child=container
        )
    
    def _create_niri_button(self, workspace: dict) -> Widget.Button:
        """Create a Niri workspace button."""
        # Create a container box for the workspace label and monitor indicator
        container = Widget.Box(
            spacing=2,
            css_classes=["workspace-container"]
        )
        
        # Add workspace number label
        container.append(Widget.Label(label=str(workspace["idx"])))
        
        # Add monitor indicator
        if "output" in workspace and workspace["output"]:
            # Extract just the monitor number or identifier
            monitor_id = workspace["output"].split("-")[-1] if "-" in workspace["output"] else workspace["output"]
            monitor_indicator = Widget.Label(
                label=str(monitor_id),
                css_classes=["monitor-indicator", "minimal"]
            )
            container.append(monitor_indicator)
        
        return Widget.Button(
            css_classes=["workspace"],
            on_click=lambda x, id=workspace["idx"]: 
                self.niri.switch_to_workspace(id),
            child=container
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
        
        # Get the currently active workspace ID
        active_workspace_id = None
        active_special_workspace = False
        
        if self.hyprland.is_available:
            # For Hyprland, get the active workspace ID directly from the service
            if hasattr(self.hyprland, 'active_workspace'):
                active_workspace_id = getattr(self.hyprland.active_workspace, 'id', None)
            
            # Check if any monitor has an active special workspace
            for monitor in self.hyprland.monitors:
                if monitor.special_workspace_id and monitor.focused:
                    active_special_workspace = True
            
        elif self.niri.is_available:
            # For Niri, find the active workspace on the current monitor
            active_workspace = next(
                (w for w in self.niri.workspaces if 
                 (w.get("is_active") or w.get("focused", False)) and 
                 w.get("output") == self._monitor_name),
                None
            )
            
            if active_workspace:
                active_workspace_id = active_workspace.get("idx")
        
        # Update active class for each workspace button
        for button in workspace_box:
            if not isinstance(button, Widget.Button):
                continue
                
            # Check if this is a special workspace button
            is_special = "special" in button.css_classes
            
            # Handle special workspaces differently
            if is_special:
                if active_special_workspace:
                    button.add_css_class("active")
                else:
                    button.remove_css_class("active")
                continue
                
            # Get workspace ID from the button's label
            # The structure is now Button -> Box (container) -> Label (first child)
            container = button.child
            if not isinstance(container, Widget.Box):
                continue
                
            # Get the first child which is the workspace label
            for child in container:
                if isinstance(child, Widget.Label):
                    label = child
                    break
            else:
                continue
                
            workspace_id = label.label
            if not workspace_id:
                continue
                
            try:
                workspace_id = int(workspace_id)
            except ValueError:
                continue
                
            # Update CSS class based on whether this workspace is the active one
            is_active = workspace_id == active_workspace_id
                
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

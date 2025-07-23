from ignis.widgets import Widget
from ignis.services.hyprland import HyprlandService
from ignis.services.niri import NiriService
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib

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
        
        # Initialize update debounce timer
        self._update_timeout_id = None
        self._update_delay_ms = 10  # Reduced from 50ms to 10ms for faster response
        self._last_update_time = 0
        
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
            self.hyprland.connect("notify::active-workspace", lambda *_: self.update(immediate=True))
            # Also listen for workspace list changes (added/removed workspaces)
            self.hyprland.connect("notify::workspaces", lambda *_: self.update())
            # Listen for monitor changes which can affect active workspaces
            self.hyprland.connect("notify::monitors", lambda *_: self.update())
            # Listen for special workspace changes
            for monitor in self.hyprland.monitors:
                monitor.connect("notify::special-workspace-id", lambda *_: self.update())
                monitor.connect("notify::special-workspace-name", lambda *_: self.update())
        elif self.niri.is_available:
            self.niri.connect("notify::workspaces", lambda *_: self.update(immediate=True))
    
    def _create_workspace_box(self) -> Widget.Box:
        """Create the main workspace container with appropriate bindings."""
        # for workspace in self.hyprland.workspaces:
        #     print(workspace.id)
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
        
        # Use a simple 'S' label without stars
        label_text = "S"
        container.append(Widget.Label(label=label_text))
        
        # We're removing the monitor indicator for special workspaces as requested
        
        # Return a button with no click handler
        return Widget.Button(
            css_classes=["workspace", "special", "fancy-special", "non-clickable"],
            child=container
        )
    
    def _create_workspace_button(self, workspace: dict) -> Widget.Button:
        """Create a button for a single workspace."""
        if self._monitor_name != workspace.monitor:
            return Widget.Button()
        if self.hyprland.is_available:
            return self._create_hyprland_button(workspace)
        elif self.niri.is_available:
            return self._create_niri_button(workspace)
    
    def _create_hyprland_button(self, workspace: dict) -> Widget.Button:
        """Create a Hyprland workspace button."""
        # Create a container box for the workspace label and monitor indicator
        container = Widget.Box(
            spacing=2,
            css_classes=["workspace-container"]
        )
        
        # Add workspace number label - handle special case for sticky workspaces (negative IDs)
        workspace_id = workspace.id if hasattr(workspace, 'id') else ''
        # print("curr mor", workspace.monitor)
        
        # Check if this is a special workspace (negative ID)
        if isinstance(workspace_id, int) and workspace_id < 0:
            # This is a special workspace, show it as 'S' instead of negative number
            label_text = "S"
            container.append(Widget.Label(label=label_text))
            # Skip adding monitor indicator for special workspaces
            css_classes = ["workspace", "special", "fancy-special", "non-clickable"]
            
            # Return a button with no click handler for special workspaces
            return Widget.Button(
                css_classes=css_classes,
                child=container
            )
        else:
            # Regular workspace
            container.append(Widget.Label(label=str(workspace_id)))
            
            # Add monitor indicator if monitor information is available
            if hasattr(workspace, "monitor"):
                monitor_indicator = Widget.Label(
                    label=str(workspace.monitor),
                    css_classes=["monitor-indicator", "minimal"]
                )
                container.append(monitor_indicator)
            
            # Return a normal button with click handler for regular workspaces
            return Widget.Button(
                css_classes=["workspace"],
                on_click=lambda x, id=workspace_id: 
                    self._switch_workspace_and_update(id),
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
    
    def update(self, immediate=False) -> None:
        """
        Update the active workspace CSS class.
        This function refreshes the workspace buttons to ensure the correct one has the 'active' class.
        Uses an adaptive debounce mechanism to prevent rapid consecutive updates.
        
        Args:
            immediate: If True, update immediately without debouncing (for direct user actions)
        """
        # For direct user actions, update immediately
        if immediate:
            if self._update_timeout_id is not None:
                try:
                    GLib.source_remove(self._update_timeout_id)
                except GLib.Error:
                    pass  # Handle case where timer ID is no longer valid
                self._update_timeout_id = None
            self._do_update()
            return
            
        # Cancel any pending update
        if self._update_timeout_id is not None:
            try:
                GLib.source_remove(self._update_timeout_id)
            except GLib.Error:
                pass  # Handle case where timer ID is no longer valid
            self._update_timeout_id = None
            
        # Schedule a new update with debounce
        # Using standard timeout_add as timeout_add_full isn't available
        self._update_timeout_id = GLib.timeout_add(
            self._update_delay_ms, 
            self._do_update_wrapper
        )
    
    def _do_update_wrapper(self, *args) -> bool:
        """
        Wrapper for _do_update that catches any exceptions to prevent UI freezes.
        Returns False to ensure the timeout doesn't repeat.
        """
        try:
            return self._do_update()
        except Exception as e:
            print(f"Error in workspace update: {e}")
            self._update_timeout_id = None
            return False
    
    def _do_update(self) -> bool:
        """
        Perform the actual workspace update.
        Returns False to ensure the timeout doesn't repeat.
        """
        # Clear the timeout ID since we're now running the update
        self._update_timeout_id = None
        
        # Get all workspace buttons
        workspace_box = super().child
        if not workspace_box:
            return False
        
        # Get the currently active workspace ID
        active_workspace_id = None
        # Remove debug print that could cause performance issues
        # for monitor in self.hyprland.monitors:
        #    print("monitor", monitor.name)
        
        if self.hyprland.is_available:
            # For Hyprland, get the active workspace ID directly from the service
            if hasattr(self.hyprland, 'active_workspace'):
                active_workspace_id = getattr(self.hyprland.active_workspace, 'id', None)
            
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
            
            # Skip setting active status for special workspaces
            if is_special:
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
                
        # Return False to ensure the timeout doesn't repeat
        return False
    
    def _scroll_workspaces(self, direction: str) -> None:
        """Handle workspace scrolling."""
        if self.hyprland.is_available:
            self._scroll_hyprland_workspaces(direction)
        elif self.niri.is_available:
            self._scroll_niri_workspaces(direction)
        
        # Update active workspace after scrolling - use immediate update for user actions
        self.update(immediate=True)
    
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

    def _switch_workspace_and_update(self, workspace_id):
        """Switch to workspace and immediately update UI."""
        try:
            if self.hyprland.is_available:
                self.hyprland.switch_to_workspace(workspace_id)
            elif self.niri.is_available:
                self.niri.switch_to_workspace(workspace_id)
            
            # Force immediate update for direct user actions
            self.update(immediate=True)
        except Exception as e:
            print(f"Error switching workspace: {e}")
            # Try to recover by forcing an update
            GLib.timeout_add(100, lambda: self.update(immediate=True))

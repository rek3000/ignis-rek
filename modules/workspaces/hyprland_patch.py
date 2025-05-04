"""
Monkey patch for Hyprland service to fix the issue with special workspaces.
This module patches the __on_event_received method to handle empty workspace IDs.
"""

from ignis.services.hyprland import HyprlandService

# Store the original method
original_on_event_received = HyprlandService._HyprlandService__on_event_received

def patched_on_event_received(self, event):
    """
    Patched version of __on_event_received that handles empty workspace IDs.
    """
    try:
        # Call the original method
        original_on_event_received(self, event)
    except ValueError as e:
        # If the error is about converting an empty string to int, just ignore it
        if "invalid literal for int() with base 10: ''" in str(e):
            print("Ignoring empty workspace ID in event:", event)
        else:
            # Re-raise other ValueError exceptions
            raise e

# Apply the patch
HyprlandService._HyprlandService__on_event_received = patched_on_event_received
print("Applied Hyprland service patch for special workspaces")

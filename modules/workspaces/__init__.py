from .workspaces import Workspaces
# Import the patch to fix Hyprland special workspace handling
try:
    from . import hyprland_patch
except ImportError:
    pass

__all__ = ["Workspaces"]
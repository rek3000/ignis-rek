import asyncio
import time
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.services.hyprland import HyprlandService
from functools import partial


class PowerMenu(Widget.Button):
    def __init__(self):
        self.hyprland = HyprlandService.get_default()

        self.menu = Widget.PopoverMenu(
            items=[
                Widget.MenuItem(
                    label="Lock",
                    on_activate=partial(self._exec_command, "hyprlock"),
                ),
                Widget.Separator(),
                Widget.MenuItem(
                    label="Suspend",
                    on_activate=partial(self._exec_with_confirmation, "systemctl suspend", "Suspend", "Are you sure you want to suspend the system?"),
                ),
                Widget.MenuItem(
                    label="Hibernate",
                    on_activate=partial(self._exec_with_confirmation, "systemctl hibernate", "Hibernate", "Are you sure you want to hibernate the system?"),
                ),
                Widget.Separator(),
                Widget.MenuItem(
                    label="Reboot",
                    on_activate=partial(self._exec_with_confirmation, "systemctl reboot", "Reboot", "Are you sure you want to reboot the system?"),
                ),
                Widget.MenuItem(
                    label="Shutdown",
                    on_activate=partial(self._exec_with_confirmation, "systemctl poweroff", "Shutdown", "Are you sure you want to shutdown the system?"),
                ),
                Widget.Separator(),
                Widget.MenuItem(
                    label="Logout",
                    enabled=self.hyprland.is_available,
                    on_activate=partial(self._exec_with_confirmation, "loginctl kill-session $XDG_SESSION_ID", "Logout", "Are you sure you want to logout?"),
                ),
            ]
        )

        super().__init__(
            child=Widget.Box(
                child=[
                    Widget.Icon(image="system-shutdown-symbolic", pixel_size=20),
                    self.menu,
                ]
            ),
            on_click=self._on_menu_click,
        )

        self.add_css_class("power-menu")

    def _on_menu_click(self, _):
        self.menu.popup()

    def _exec_command(self, command, _):
        Utils.exec_sh(command)
    
    def _exec_with_confirmation(self, command, action_name, message, _):
        """Execute command after showing confirmation dialog"""
        # Create a confirmation window with unique namespace
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        confirmation_window = Widget.Window(
            namespace=f"power-confirmation-{action_name.lower()}-{timestamp}",
            layer="overlay",
            popup=True,
            kb_mode="exclusive",
            css_classes=["confirmation-window"],
            # anchor=["top", "bottom", "left", "right"],
            exclusivity="ignore",
            child=Widget.CenterBox(
                center_widget=Widget.Box(
                    orientation="vertical",
                    spacing=20,
                    css_classes=["confirmation-dialog"],
                    child=[
                        Widget.Label(
                            label=f"Confirm {action_name}",
                            css_classes=["confirmation-title"]
                        ),
                        Widget.Label(
                            label=message,
                            css_classes=["confirmation-message"]
                        ),
                        Widget.Box(
                            orientation="horizontal",
                            spacing=10,
                            homogeneous=True,
                            css_classes=["confirmation-buttons"],
                            child=[
                                Widget.Button(
                                    label="Cancel",
                                    css_classes=["cancel-button"],
                                    on_click=lambda _: self._close_confirmation(confirmation_window),
                                ),
                                Widget.Button(
                                    label=action_name,
                                    css_classes=["confirm-button", "destructive-action"],
                                    on_click=lambda _: self._confirm_and_execute(confirmation_window, command),
                                ),
                            ]
                        )
                    ]
                )
            )
        )
        confirmation_window.show()
    
    def _close_confirmation(self, window):
        """Close the confirmation window"""
        window.close()
    
    def _confirm_and_execute(self, window, command):
        """Close confirmation window and execute the command"""
        window.close()
        try:
            # Add a small delay to let UI settle before executing power commands
            asyncio.create_task(self._delayed_execute(command))
        except Exception as e:
            print(f"Error executing power command: {e}")
    
    async def _delayed_execute(self, command):
        """Execute command with a small delay to let UI settle"""
        await asyncio.sleep(0.5)
        await Utils.exec_sh_async(command)

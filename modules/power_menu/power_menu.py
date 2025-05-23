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
                    on_activate=partial(self._exec_command, "systemctl suspend"),
                ),
                Widget.MenuItem(
                    label="Hibernate",
                    on_activate=partial(self._exec_command, "systemctl hibernate"),
                ),
                Widget.Separator(),
                Widget.MenuItem(
                    label="Reboot",
                    on_activate=partial(self._exec_command, "systemctl reboot"),
                ),
                Widget.MenuItem(
                    label="Shutdown",
                    on_activate=partial(self._exec_command, "systemctl poweroff"),
                ),
                Widget.Separator(),
                Widget.MenuItem(
                    label="Logout",
                    enabled=self.hyprland.is_available,
                    on_activate=partial(self._exec_command, "loginctl kill-session $XDG_SESSION_ID"),
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

from ignis.widgets import Widget
from ignis.services.notifications import NotificationService
from ignis.app import IgnisApp

app = IgnisApp.get_default()
notifications = NotificationService.get_default()

class NotificationIcon(Widget.Box):
    __gtype_name__ = "NotificationIcon"

    def __init__(self):
        self.button = Widget.Button(
            child=Widget.Box(
                child=[
                    Widget.Label(
                        label="󰂚",
                        css_classes=["notification-bell"],
                    ),
                    Widget.Label(
                        label=notifications.bind(
                            "notifications",
                            lambda value: str(len(value))
                        ),
                        visible=notifications.bind(
                            "notifications",
                            lambda value: len(value) > 0
                        ),
                        css_classes=["notification-count"],
                    ),
                ],
            ),
            on_click=self._toggle_notification_center,
            css_classes=["notification-button"],
        )

        super().__init__(
            css_classes=["notification-icon", "system-tray"],
            child=[self.button],
        )

        # Connect to window state changes
        app.connect("window-added", self._on_window_state_changed)
        app.connect("window-removed", self._on_window_state_changed)

    def _on_window_state_changed(self, app, window_name=None):
        if window_name == "ignis_CONTROL_CENTER":
            if "ignis_CONTROL_CENTER" in app.windows:
                self.button.add_css_class("active")
            else:
                self.button.remove_css_class("active")

    def _toggle_notification_center(self, button):
        """Toggle the notification center"""
        app.toggle_window("ignis_CONTROL_CENTER")

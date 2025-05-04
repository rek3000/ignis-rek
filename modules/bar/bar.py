import datetime
import asyncio
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.services.notifications import NotificationService
from ignis.services.mpris import MprisService, MprisPlayer

from modules import (
    PriceTracker,
    Battery,
    Tray,
    Workspaces,
    WindowTitle,
    Volume,
    VolumeSlider,
    VolumeRevealer,
    PowerMenu,
    NotificationIcon,
)

mpris = MprisService.get_default()


def mpris_title(player: MprisPlayer) -> Widget.Box:
    return Widget.Box(
        spacing=10,
        setup=lambda self: player.connect(
            "closed",
            lambda x: self.unparent(),  # remove widget when player is closed
        ),
        child=[
            Widget.Icon(image="audio-x-generic-symbolic"),
            Widget.Label(
                ellipsize="end",
                max_width_chars=20,
                label=player.bind("title"),
            ),
        ],
    )


def media() -> Widget.Box:
    return Widget.Box(
        spacing=10,
        child=[
            Widget.Label(
                label="",
                visible=mpris.bind("players", lambda value: len(value) == 0),
            )
        ],
        setup=lambda self: mpris.connect(
            "player-added", lambda x, player: self.append(mpris_title(player))
        ),
    )

def clock() -> Widget.Label:
    # poll for current time every second
    return Widget.Label(
        css_classes=["clock"],
        label=Utils.Poll(
            1_000, lambda self: datetime.datetime.now().strftime("%H:%M")
        ).bind("output"),
    )


def price_tracker() -> Widget.Box:
    return Widget.Box(
        child=[
            # PriceTracker("b5w7qrbhbdu2jehgvrhbw7xgmtkc4i4fbj4gs9udwldm"),
            # PriceTracker("fe5d1suzpldryy6f87lgacrbukstrx9jsmg1a1bpsplt")
        ],
        spacing=10,
    )


def left(monitor_name: str) -> Widget.Box:
    return Widget.Box(
        child=[Workspaces(monitor_name), WindowTitle(monitor_name)], spacing=10
    )


def center() -> Widget.Box:
    return Widget.Box(
        child=[
            Widget.Separator(vertical=True, css_classes=["middle-separator"]),
        ],
        spacing=10,
    )


async def right() -> Widget.Box:
    battery_widget = Battery()
    await battery_widget.setup()

    tray_widget = Tray()
    await tray_widget.setup()

    return Widget.Box(
        child=[
            # price_tracker(),
            tray_widget,
            battery_widget,
            # Volume(),
            # VolumeSlider(),
            VolumeRevealer(),
            NotificationIcon(),
            clock(),
            PowerMenu(),
        ],
        spacing=10,
    )


class Bar(Widget.Window):
    __gtype_name__ = "Bar"

    def __init__(self, monitor_id: int = 0):
        self.monitor_id = monitor_id
        self.monitor_name = None

        super().__init__(
            namespace=f"ignis_bar_{monitor_id}",
            monitor=monitor_id,
            anchor=["left", "bottom", "right"],
            exclusivity="exclusive",
            child=Widget.CenterBox(
                css_classes=["bar"],
                start_widget=None,
                center_widget=None,
                end_widget=None,
            ),
        )
    async def setup(self):
        self.monitor_name = Utils.get_monitor(self.monitor_id).get_connector()  # type: ignore
        start_widget = left(self.monitor_name)
        center_widget = center()
        end_widget = await right()

        self.child.start_widget = start_widget
        self.child.center_widget = center_widget
        self.child.end_widget = end_widget

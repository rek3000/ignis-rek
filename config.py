import datetime
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.app import IgnisApp
from ignis.services.audio import AudioService
from ignis.services.hyprland import HyprlandService
from ignis.services.notifications import NotificationService
from ignis.services.mpris import MprisService, MprisPlayer

from modules import NotificationPopup, PriceTracker, Battery, Tray, Workspaces, WindowTitle

app = IgnisApp.get_default()

app.apply_css(f"{Utils.get_current_dir()}/style.scss")

audio = AudioService.get_default()
hyprland = HyprlandService.get_default()
notifications = NotificationService.get_default()
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
                label="No media players",
                visible=mpris.bind("players", lambda value: len(value) == 0),
            )
        ],
        setup=lambda self: mpris.connect(
            "player-added", lambda x, player: self.append(mpris_title(player))
        ),
    )

def current_notification() -> Widget.Label:
    return Widget.Label(
        ellipsize="end",
        max_width_chars=60,
        label=notifications.bind(
            "notifications", lambda value: value[-1].summary if len(value) > 0 else None
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


def speaker_volume() -> Widget.Box:
    return Widget.Box(
        child=[
            Widget.Icon(
                image=audio.speaker.bind("icon_name"), style="margin-right: 5px;"
            ),
            Widget.Label(
                label=audio.speaker.bind("volume", transform=lambda value: str(value))
            ),
        ]
    )

def speaker_slider() -> Widget.Scale:
    return Widget.Scale(
        min=0,
        max=100,
        step=1,
        value=audio.speaker.bind("volume"),
        on_change=lambda x: audio.speaker.set_volume(x.value),
        css_classes=["volume-slider"],
    )


def logout() -> None:
    if hyprland.is_available:
        Utils.exec_sh_async("hyprctl dispatch exit 0")
    elif niri.is_available:
        Utils.exec_sh_async("niri msg action quit")
    else:
        pass


def power_menu() -> Widget.Button:
    menu = Widget.PopoverMenu(
        items=[
            Widget.MenuItem(
                label="Lock",
                on_activate=lambda x: Utils.exec_sh_async("hyprlock"),
            ),
            Widget.Separator(),
            Widget.MenuItem(
                label="Suspend",
                on_activate=lambda x: Utils.exec_sh_async("loginctl suspend"),
            ),
            Widget.MenuItem(
                label="Hibernate",
                on_activate=lambda x: Utils.exec_sh_async("loginctl hibernate"),
            ),
            Widget.Separator(),
            Widget.MenuItem(
                label="Reboot",
                on_activate=lambda x: Utils.exec_sh_async("loginctl reboot"),
            ),
            Widget.MenuItem(
                label="Shutdown",
                on_activate=lambda x: Utils.exec_sh_async("loginctl poweroff"),
            ),
            Widget.Separator(),
            Widget.MenuItem(
                label="Logout",
                enabled=hyprland.is_available or niri.is_available,
                on_activate=lambda x: logout(),
            ),
        ]
    )
    return Widget.Button(
        child=Widget.Box(
            child=[Widget.Icon(image="system-shutdown-symbolic", pixel_size=20), menu]
        ),
        on_click=lambda x: menu.popup(),
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
        child=[
                Workspaces(monitor_name),
                WindowTitle(monitor_name)
                ], spacing=10
    )

def center() -> Widget.Box:
    return Widget.Box(
        child=[
            current_notification(),
            # Widget.Separator(vertical=True, css_classes=["middle-separator"]),
            # media(),
        ],
        spacing=10,
    )


def right() -> Widget.Box:
    return Widget.Box(
        child=[
            price_tracker(),
            Tray(),
            Battery(),
            speaker_volume(),
            speaker_slider(),
            clock(),
            power_menu(),
        ],
        spacing=10,
    )


def bar(monitor_id: int = 0) -> Widget.Window:
    monitor_name = Utils.get_monitor(monitor_id).get_connector()  # type: ignore
    return Widget.Window(
        namespace=f"ignis_bar_{monitor_id}",
        monitor=monitor_id,
        anchor=["left", "top", "right"],
        exclusivity="exclusive",
        child=Widget.CenterBox(
            css_classes=["bar"],
            start_widget=left(monitor_name),  # type: ignore
            center_widget=center(),
            end_widget=right(),
        ),
    )


# this will display bar on all monitors

for i in range(Utils.get_n_monitors()):
    NotificationPopup(i)

for i in range(Utils.get_n_monitors()):
    bar(i)

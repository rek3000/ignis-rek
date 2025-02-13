import datetime
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.app import IgnisApp
from ignis.services.notifications import NotificationService
# from ignis.services.mpris import MprisService, MprisPlayer

from modules import (
    NotificationPopup,
    Bar,
    ControlCenter
)

app = IgnisApp.get_default()
app.apply_css(f"{Utils.get_current_dir()}/style.scss")

notifications = NotificationService.get_default()

ControlCenter()

for i in range(Utils.get_n_monitors()):
    NotificationPopup(i)

for i in range(Utils.get_n_monitors()):
    Bar(i)

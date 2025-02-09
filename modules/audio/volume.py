from ignis.widgets import Widget
from ignis.services.audio import AudioService


class Volume(Widget.Box):
    def __init__(self):
        self.audio = AudioService.get_default()
        self._setup_bindings()

        super().__init__(
            vertical=False, spacing=0, child=[self.icon, self.label_volume]
        )

        self.add_css_class("volume")

    def _setup_bindings(self):
        self.icon = Widget.Icon(
            image=self.audio.speaker.bind("icon_name"), style="margin-right: 5px;"
        )
        self.label_volume = Widget.Label(
            label=self.audio.speaker.bind("volume", transform=lambda value: str(value))
        )


class VolumeSlider(Widget.Scale):
    def __init__(self):
        self.audio = AudioService.get_default()
        self._setup_bindings()

        super().__init__(
            min=0,
            max=100,
            step=1,
            value=self.volume,
            on_change=self._on_volume_change,
        )

        self.add_css_class("volume-slider")

    def _setup_bindings(self):
        self.volume = self.audio.speaker.bind("volume")

    def _on_volume_change(self, slider):
        (self.audio.speaker.set_volume(slider.value),)

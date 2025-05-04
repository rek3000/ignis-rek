from ignis.widgets import Widget
from ignis.services.audio import AudioService
from gi.repository import Gtk


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


class VolumeRevealer(Widget.Box):
    def __init__(self):
        self.volume = Volume()
        self._slider = VolumeSlider()
        self._revealer = Widget.Revealer(
            child=self._slider,
            reveal_child=False,
            transition_type="slide_left",
            transition_duration=500
        )
        
        super().__init__(
            vertical=False,
            spacing=5,
            child=[
                self.volume,
                self._revealer
            ]
        )
        
        self.add_css_class("volume-revealer")
        self._setup_hover_events()
        
    def _setup_hover_events(self):
        # Connect events after widget is realized
        self.connect("realize", self._on_realize)
        
    def _on_realize(self, widget):
        # Use Gtk.EventControllerMotion for hover detection
        motion_controller = Gtk.EventControllerMotion.new()
        self.add_controller(motion_controller)
        motion_controller.connect("enter", self._on_hover_enter)
        motion_controller.connect("leave", self._on_hover_leave)
        
    def _on_hover_enter(self, controller, x, y):
        self._revealer.set_reveal_child(True)
        
    def _on_hover_leave(self, controller):
        self._revealer.set_reveal_child(False)

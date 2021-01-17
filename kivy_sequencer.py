import os

# os.environ['KIVY_WINDOW'] = 'sdl2'
# os.environ['KIVY_GL_BACKEND'] = 'sdl2'
# USES KIVYTEST36 VENV

# 1. install system dependencies for kivy
# 2. pip install Cython==0.27.3
# 3. pip install git+https://github.com/kivy/kivy.git@master

import kivy

# kivy.require("1.10.0")
import time
from pyo import *
from random import sample
from random import uniform
from string import ascii_lowercase
from kivy.app import App
from kivy.utils import get_color_from_hex
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

# this is so seqgridwidget can be resized without crashing
# this does not affect the filebrowser scrolling when loading/saving a file
from scrollview_edit import ScrollView

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recyclelayout import RecycleLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.animation import Animation
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader, TabbedPanelItem
from kivy.properties import (
    ObjectProperty,
    StringProperty,
    NumericProperty,
    ListProperty,
)
from kivy.uix.behaviors import DragBehavior
from kivy.graphics import Color
from kivy.graphics import Rectangle, Ellipse, Line
from kivy.config import Config

Config.set("graphics", "width", "1920")
Config.set("graphics", "height", "1080")
Config.write()
from kivy.core.window import Window

Window.size = (2000, 1500)

from kivy.clock import Clock
from functools import partial

from file_dialog import *
from file_save_loader import FileSystem
from aengine_thread import AudioEngine, AudioMixer

import theme

from seq_widget_edit import SeqGridWidget


APPNAME = "Sequencer"
BASE_DIR = "sounds/"
INF = float("inf")


class TimingBar(GridLayout):  # configured in sequencer.kv
    pass


class NumericInput(GridLayout):
    value = NumericProperty(0)
    min = NumericProperty(-INF)
    max = NumericProperty(INF)
    step = NumericProperty(1)
    # text = StringProperty()
    def valchange(self, id, value):
        print("value change type: {}, value: {}".format(id, value))
        app = App.get_running_app()
        if id == "BPB":
            app.root.sgr.grid.set_beats_per_bar(value)


class SequencerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio_engine = AudioEngine()
        self.audio_mixer = AudioMixer()
        self.timing_bar = TimingBar()
        self.seq_grid_widget = SeqGridWidget()
        self.file_loader = FileLoader()
        self.file_system = FileSystem()

        self.audio_engine.start()

        self.bpm = 120
        self.ticks = 4
        self.metro_val = (60000 / self.bpm / self.ticks) * 0.001
        self.loop = False
        self.current_sound = ""
        self.tracks = []  # PUT THIS IN AENGINE CLASS
        self.inc = 0
        self.sample_filename_list = []
        path = os.path.dirname(os.path.abspath(__file__))
        for file in os.listdir(path + "/sounds/"):
            if file.endswith(".wav"):
                self.sample_filename_list.append(file)


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


class Transport(BoxLayout):
    def button_about(self):
        print("about pressed")
        cont = GridLayout(cols=1)
        about_txt = (
            "{appname}\n" "Created on 6/23/18 \nby Sam H." "".format(appname=APPNAME)
        )
        cont.add_widget(Label(text=about_txt))

        popup = Popup(
            title="About {}".format(APPNAME),
            content=cont,
            size_hint=(None, None),
            size=(400, 400),
        )
        popup.open()

    # Options audio output selector callback
    # this handles the dynamic buttons
    def audio_opts_button_callback(self, instance):
        print("but was clicked", instance.text)
        app = App.get_running_app()
        app.root.ae.set_output(4)

    def bpm_text(self, instance):
        print("text was entered")
        print(instance.text)
        app = App.get_running_app()
        app.root.m.setTime((60000 / int(instance.text) / 4) * 0.001)

    def button_loop(self, button):
        print("loop")
        app = App.get_running_app()
        # app.root.sgr.loop = True
        if button.state == "down":
            print("down")
            # app.root.sgr.loop = True
            app.root.sgr.loop_bars.loop_func(True)
        else:
            # app.root.sgr.loop = False
            app.root.sgr.loop_bars.loop_func(False)
            print("up")

    def button_open_project(self):
        print("project opened")
        app = App.get_running_app()
        app.root.file_loader.show_load()

    def button_save_project(self):
        print("project saved")
        app = App.get_running_app()
        app.root.file_loader.show_save()

    def button_options(self):
        print("options pressed")
        app = App.get_running_app()
        cont = GridLayout(cols=1)
        # retrieve audio outputs / soundcards from audioengine class
        out_list = app.root.ae.get_outputs()
        print(out_list)

        # combine out_list, add to output selector
        for x, y in zip(*out_list):
            # intentional error to remember where left off
            b = Button(id="{}".format(y), text="{} {}".format(x, y))
            b.bind(on_press=self.audio_opts_button_callback)
            cont.add_widget(b)
        for x in self.children:
            print(x)

        tp = TabbedPanel(do_default_tab=False)

        # audio tab
        th_audio = TabbedPanelItem(text="Audio")
        th_audio.content = GridLayout()
        th_audio.add_widget(cont)

        # files tab
        th_files = TabbedPanelItem(text="Files")
        th_files.add_widget(Button(text="files tab content"))
        tp.add_widget(th_audio)
        tp.add_widget(th_files)

        popup = Popup(
            title="Options", content=tp, size_hint=(None, None), size=(800, 800)
        )
        popup.open()

    def button_play(self):
        print("play pressed")
        app = App.get_running_app()
        app.root.m.play()

    def button_stop(self):
        print("stop pressed")
        app = App.get_running_app()
        from ipdb import set_trace

        set_trace()
        app.root.ae.m.stop()


# Filename lister on left
class Row(Button):
    # button pressed
    def button_pressed(self):
        app = App.get_running_app()
        selected_sound = self.text
        path = "sounds/" + selected_sound
        app.root.audio_engine.playsound(path)
        app.root.seq_grid_widget.current_sound = BASE_DIR + selected_sound
        app.root.current_sound = BASE_DIR + selected_sound


class FilenameLister(RecycleView):
    pass


class StepPanelScroll(ScrollView):
    pass


class StepPanel_grid_base(GridLayout):
    def button_pressed(self, *args):
        print("buttonpressed")


class StepRowPanel(GridLayout):
    pass


class PlayheadControlBar(GridLayout):
    pass


class SequencerApp(App):  # by 'magic' it loads sequencer.kv
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.TRACK_COUNT = kwargs.get("TRACK_COUNT") or 26
        self.STEP_COUNT = kwargs.get("STEP_COUNT") or 16
        self.title = APPNAME

    def build(self):
        sequencer_layout = SequencerLayout()
        sequencer_layout_grid = GridLayout(cols=1)
        transport = self._get_transport(sequencer_layout.timing_bar)
        mixer_base, file_list = self._get_mixer_base_and_file_list()
        step_base = self._get_step_base(sequencer_layout.seq_grid_widget)

        sequencer_layout_grid.add_widget(transport)
        sequencer_layout_grid.add_widget(step_base)
        sequencer_layout_grid.add_widget(mixer_base)

        sequencer_layout.add_widget(file_list)
        sequencer_layout.add_widget(sequencer_layout_grid)

        return sequencer_layout

    @staticmethod
    def _get_transport(timing_bar):
        transport = Transport()
        transport.size = (200, 80)
        timing_bar.size_hint_x = 0.2
        timing_bar.ids.step.text = "arstrsts"
        transport.add_widget(timing_bar)
        return transport

    def _get_mixer_base_and_file_list(self):
        mixer_base = ScrollView(
            size_hint=(1, None), size=(200, 400), do_scroll_y=False, do_scroll_x=True
        )

        mixer_panel_grid, file_list = self._get_mixer_panel_grid_and_file_list()
        mixer_base.add_widget(mixer_panel_grid)
        return mixer_base, file_list

    def _get_mixer_panel_grid_and_file_list(self):
        # mixer_panel_grid
        mixer_panel_grid = GridLayout(
            rows=1, padding=10, spacing=10, size_hint=(None, 1)
        )
        mixer_panel_grid.bind(minimum_width=mixer_panel_grid.setter("width"))

        # Effects box
        effects_box = BoxLayout(orientation="vertical")
        effects_box.add_widget(Label(text="Reverb"))
        effects_box.add_widget(Label(text="Echo"))
        effects_box.add_widget(Label(text="Delay"))
        effects_box.add_widget(Label(text="Distortion"))

        # Vertical buttons in mixer_panel_grid
        anothergrid = GridLayout(cols=1, size_hint_x=None, width=200)
        anothergrid.canvas.add(Color(*theme.about_button))
        anothergrid.canvas.add(Rectangle(pos=anothergrid.pos, size=anothergrid.size))
        anothergrid.bind(minimum_width=anothergrid.setter("width"))
        anothergrid.add_widget(Slider(orientation="vertical"))
        anothergrid.add_widget(effects_box)

        mixer_panel_grid.add_widget(anothergrid)

        # File name lister on left
        file_list = FilenameLister()
        file_list.size_hint_x = 0.13

        sample_filename_list = []
        path = os.path.dirname(os.path.abspath(__file__))
        for file in os.listdir(path + "/sounds"):
            if file.endswith(".wav"):
                sample_filename_list.append(file)
                file_list.data.insert(0, {"value": file})

        # Add number of mixer panels per track added
        for i in range(self.TRACK_COUNT):
            label = Label(
                text="Mix Panel \n" + str(sample_filename_list[i]),
                height=220,
                width=150,
                size_hint_x=None,
            )
            mixer_panel_grid.add_widget(label)
        return mixer_panel_grid, file_list

    @staticmethod
    def _get_step_base(seq_grid_widget):
        step_base = ScrollView(size_hint=(1, 1), do_scroll_y=True, do_scroll_x=True)
        step_base.bar_width = 20
        step_base.scroll_type = ["bars"]
        step_base.add_widget(seq_grid_widget)
        return step_base


seq_app = SequencerApp()
seq_app.run()

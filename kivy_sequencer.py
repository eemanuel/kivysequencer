import os

from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.slider import Slider
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

import theme
from aengine_thread import AudioMixer
from file_dialog import FileLoader
from file_save_loader import FileSystem
from pyo import Server, SfPlayer
from scrollview_edit import ScrollView
from seq_widget_edit import SeqGridWidget

Config.set("graphics", "width", "1920")
Config.set("graphics", "height", "1080")
Config.write()

Window.size = (2000, 1500)

APPNAME = "Sequencer"
BASE_DIR = "sounds/"


class TimingBar(GridLayout):  # configured in sequencer.kv
    pass


class NumericInput(GridLayout):
    value = NumericProperty(0)
    min = NumericProperty(-99999)
    max = NumericProperty(99999)
    step = NumericProperty(1)

    def change_value(self, id_value, value):
        app = App.get_running_app()
        if id_value == "BPB":
            app.root.seq_grid_widget.grid.set_beats_per_bar(value)


class Transport(BoxLayout):
    def __init__(self, server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = App.get_running_app()
        self.server = server

    def button_about(self):
        cont = GridLayout(cols=1)
        about_txt = f"{APPNAME}\nCreated on 6/23/18 \nby Sam H."
        cont.add_widget(Label(text=about_txt))
        popup = Popup(
            title=f"About {APPNAME}",
            content=cont,
            size_hint=(None, None),
            size=(400, 400),
        )
        popup.open()

    def audio_opts_button_callback(self, instance):
        self.app.root.audio_engine.set_output(4)

    def bpm_text(self, instance):
        self.app.root.metro.setTime((60000 / int(instance.text) / 4) * 0.001)

    def button_loop(self, button):
        if button.state == "down":
            self.app.root.seq_grid_widget.loop_bars.loop_func(True)
        else:
            self.app.root.seq_grid_widget.loop_bars.loop_func(False)

    def button_open_project(self):
        self.app.root.file_loader.show_load()

    def button_save_project(self):
        self.app.root.file_loader.show_save()

    def button_options(self):
        cont = GridLayout(cols=1)
        # retrieve audio outputs / soundcards from audioengine class
        out_list = self.app.root.audio_engine.get_outputs()

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
        self.server.start()

    def button_stop(self):
        self.server.stop()


class Row(Button):
    def button_pressed(self):
        app = App.get_running_app()
        selected_sound = self.text
        path = "sounds/" + selected_sound
        app.root.play_sound(path)
        app.root.seq_grid_widget.current_sound = BASE_DIR + selected_sound
        app.root.current_sound = BASE_DIR + selected_sound


class FilenameLister(RecycleView):
    pass


class StepPanelScroll(ScrollView):
    pass


class SequencerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server = Server()
        self.audio_mixer = AudioMixer()
        self.timing_bar = TimingBar()
        self.seq_grid_widget = SeqGridWidget()
        self.file_loader = FileLoader()
        self.file_system = FileSystem()

        self.server.boot().start()

        self.sample_filename_list = []
        path = os.path.dirname(os.path.abspath(__file__))
        for file in os.listdir(path + "/sounds/"):
            if file.endswith(".wav"):
                self.sample_filename_list.append(file)

    @staticmethod
    def play_sound(path):
        sf = SfPlayer(path)
        sf.out()
        print("----------------")


class SequencerApp(App):  # by 'magic' it loads sequencer.kv
    def build(self):
        sequencer_layout = SequencerLayout()
        sequencer_layout_grid = GridLayout(cols=1)
        transport = self._get_transport(sequencer_layout)
        mixer_base, file_list = self._get_mixer_base_and_file_list()
        step_base = self._get_step_base(sequencer_layout.seq_grid_widget)

        sequencer_layout_grid.add_widget(transport)
        sequencer_layout_grid.add_widget(step_base)
        sequencer_layout_grid.add_widget(mixer_base)

        sequencer_layout.add_widget(file_list)
        sequencer_layout.add_widget(sequencer_layout_grid)

        return sequencer_layout

    @staticmethod
    def _get_transport(sequencer_layout):
        transport = Transport(server=sequencer_layout.server)
        transport.size = (200, 80)
        timing_bar = sequencer_layout.timing_bar
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
        sample_filename_list.sort()

        for file in sample_filename_list:
            label = Label(
                text="Mix Panel \n" + file, height=220, width=150, size_hint_x=None
            )
            mixer_panel_grid.add_widget(label)

        sample_filename_list.sort(reverse=True)
        for file in sample_filename_list:
            file_list.data.insert(0, {"value": file})

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

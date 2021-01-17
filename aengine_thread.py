from pyo import Metro, Server, SfPlayer, Sine, LFO, Delay, Biquadx
from multiprocessing import Process
import random
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget
from random import uniform


class AudioEngine(Process):
    def __init__(self, pitch=5):
        super().__init__()
        self.server = Server()
        self.metro = None
        self.sf_player = None

        self.daemon = True
        self.sr = 44100
        self.num_channels = 2
        self.buffer_size = 512
        self.duplex = 0
        self.pitch = pitch

    def start(self):
        self.server.deactivateMidi()
        self.server.boot().start()
        self.metro = Metro(0.0125)
        self.metro.play()

    def start_metro(self):
        self.metro.play()

    def stop_metro(self):
        self.metro.stop()

    def playsound(self, filename):
        self.sf_player = SfPlayer(filename, mul=0.3).mix(2).out()


class AudioItem(Widget):
    def __init__(self, filename, volume, pan, velocity, pos, size):
        super(AudioItem, self).__init__()
        self.filename = filename
        self.volume = volume
        self.pan = pan
        self.effects = []
        # vocoder, delay, low pass, high pass, band pass, reverb, distort, bitcrusher, chorus
        # freq shift, flanger, phaser, 1band eq, 3band eq, graphic eq, compressor, wahwah
        self.velocity = velocity
        self.pos = pos
        self.size = size
        self.color = (0.4, uniform(0.3, 1), uniform(0.3, 1))

        self.sf = SfPlayer(self.filename, mul=0.3).stop()
        self.sf2 = self.sf.mix(2).out()

        if random.randint(0, 1) == 1:
            self.sine = Sine(freq=[0.2, 0.50], mul=1000, add=1500)
            self.lf2 = LFO([0.13, 0.41], sharp=0.7, type=1, mul=0.4, add=0.4)
            self.fx1 = Delay(self.sf2, delay=self.lf2, feedback=0.5, mul=0.4).out()
            self.f = Biquadx(self.fx1, freq=self.sine, q=5, type=0)
        Color(*self.color)
        self.shape = Rectangle(pos=self.pos, size=self.size)

    def play(self):
        self.sf.play()

    def setfn(self, path):
        self.sf.setPath(path)

    def set_pos(self, x, y):
        self.pos = [x, y]


class AudioMixer(object):
    def __init__(self):
        self.tracks = []
        self.fn = None

    def add_track(self, fn):
        self.fn = fn
        self.tracks.append(AudioItem(self.fn, 0, 0, 0))

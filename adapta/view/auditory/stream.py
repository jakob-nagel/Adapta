import pyaudio as pa
from pyqtgraph.Qt import QtCore

from adapta.util import singleton, use_settings, Threadable


class Stream_(pa.Stream):
    sample_rate = int
    bit_width = int
    num_channels = int

    _FORMAT = {8: pa.paInt8, 16: pa.paInt16, 24: pa.paInt24, 32: pa.paInt32}

    def __init__(self):
        self._pyaudio = pa.PyAudio()

        super().__init__(self._pyaudio,
                         rate=self.sample_rate,
                         channels=self.num_channels,
                         format=self._FORMAT[self.bit_width],
                         output=True)

    def __del__(self):
        self.close()
        self._pyaudio.terminate()

    def play(self, audio):
        self.start_stream()
        self.write(audio.tobytes())

    def pause(self):
        self.stop_stream()


@singleton
@use_settings
class Stream(Threadable, Stream_):
    sig_request = QtCore.Signal()

    def play(self, audio):
        super().play(audio)
        self.sig_request.emit()

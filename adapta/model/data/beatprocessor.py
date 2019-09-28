from madmom.features import DBNDownBeatTrackingProcessor, RNNDownBeatProcessor
from madmom.processors import SequentialProcessor
from pyqtgraph.Qt import QtCore

from adapta.util import use_settings, Threadable


@use_settings
class BeatProcessor(SequentialProcessor):
    def __init__(self, todo, results):
        preprocessor = RNNDownBeatProcessor()
        processor = DBNDownBeatTrackingProcessor(
            self.beats_per_bar,
            fps=100,
            transition_lambda=self.transition_lambda)
        sequence = (preprocessor, processor, lambda x: x[:, 0])
        super().__init__(sequence)

        self._todo = todo
        self._results = results

    def run(self):
        while True:
            tasks = self._todo.get()
            for name, audio in tasks:
                print('job started')
                beats = self.process(audio)
                self._results.put((name, beats))
                print('job done')


class Notifier(Threadable):
    sig_send = QtCore.Signal(str, object)

    def __init__(self, results):
        super().__init__()
        self._results = results

    def run(self):
        while True:
            name, beats = self._results.get()
            print('got something')
            self.sig_send.emit(name, beats)
            print('signal sent')

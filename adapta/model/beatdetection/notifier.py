from pyqtgraph.Qt import QtCore

from adapta.util import Threadable


class Notifier(Threadable):
    """Class watching BeatProcessor and sending notifications whenever new
    beats have been detected.

    """

    """ Signals """
    sig_send = QtCore.Signal(str, object)

    def __init__(self, results):
        super().__init__()
        self._results = results

    def run(self):
        while True:
            name, beats = self._results.get()
            self.sig_send.emit(name, beats)

# from functools import partial
import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore

from adapta.util import use_settings


@use_settings
class Cursor(pg.InfiniteLine):
    def __init__(self, plot, max_x):
        super().__init__(0, 90, pg.mkPen(self.color, width=self.width), False, (0, max_x))
        plot.addItem(self)

        """
        samples_per_move = (self.settings.playback.sample_rate *
                            self.settings.controls.winding_dist)
        self._timer_fast_forward = QtCore.QTimer(self)
        self._timer_fast_forward.timeout.connect(
            partial(self.move, samples_per_move))
        self._timer_rewind = QtCore.QTimer(self)
        self._timer_rewind.timeout.connect(
            partial(self.move, -samples_per_move)
        )
        """

    def move(self, dx):
        self.setValue(self.value() + dx)

    """
    @property
    def sample_index(self):
        return self._sample_index

    def start_fast_forward(self):
        self._timer_fast_forward.start(
            1000 / self.settings.controls.winding_freq)

    def start_rewind(self):
        self._timer_rewind.start(1000 / self.settings.controls.winding_freq)

    def stop_winding(self):
        self._timer_fast_forward.stop()
        self._timer_rewind.stop()
    """

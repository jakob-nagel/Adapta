# from functools import partial
import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore

from adapta.util import use_settings


@use_settings
class Cursor(pg.InfiniteLine):
    """ Settings """
    # cursor color
    color = str
    # cursor with in pixels
    width = int

    def __init__(self, plot, max_x):
        super().__init__(0, 90, pg.mkPen(self.color, width=self.width), False, (0, max_x))
        plot.addItem(self)

    def move(self, dx):
        self.setValue(self.value() + dx)

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

from adapta.util import use_settings
from adapta.view.visual import SpecialItem


@use_settings
class TrackItem:
    """Class plotting a single track of the mix onto the plot.

    Parameters
    ----------
    plot : :class:`Plot`
        The plot onto which the track will be plottet.
    x : numpy array
        The x data of the track samples.
    y : numpy array
        The y data of the track samples.
    deck : int
        The index of the deck in which to plot the track.
    name : optional
        The name of the track.

    """

    """ Settings """
    # ratio of item size to space between items in percent
    outer_scale = int
    # ratio of waveform size to item size in percent
    inner_scale = int
    # enable waveform antialiasing
    antialiasing = bool

    def __init__(self, plot, x, y, deck, name=None):
        # calculate properties
        outer_scale = self.outer_scale / 100
        inner_scale = self.inner_scale / 100 * outer_scale
        pos_x = x[0]
        width = x[-1] - pos_x
        pos_y = -outer_scale + deck * 2
        height = outer_scale * 2

        # draw background rectangle
        rectangle = QtGui.QGraphicsRectItem(pos_x, pos_y, width, height)
        rectangle.setPen(pg.mkPen('w', width=1))
        rectangle.setBrush(pg.mkBrush('r'))
        plot.addItem(rectangle)

        # draw waveform
        item = SpecialItem(
            x,
            y * inner_scale + deck * 2,
            pen=pg.mkPen('w', width=1),
            antialias=self.antialiasing
        )
        plot.addItem(item)

        # draw name if provided
        if name is not None:
            text = pg.TextItem(name, anchor=(0, 1), color='w')
            text.setPos(pos_x, pos_y + height)
            plot.addItem(text)

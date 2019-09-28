import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

from adapta.view.visual import Cursor, TimeAxis, TrackItem
from adapta.util import singleton


@singleton
class Plot(pg.PlotWidget):
    """Class providing the plot of the audio data for the app.

    Parameters
    ----------
    parent : :class:`QGraphicsItem`
        The parent widget of the plot.

    """

    sig_mouse_clicked = QtCore.Signal(float)

    def __init__(self):
        # initialize plot widget
        super().__init__(axisItems={'bottom': TimeAxis(orientation='bottom')})
        self.setDownsampling(auto=True)
        self.setClipToView(True)
        self.hideAxis('left')
        self.setMenuEnabled(False)
        self.hideButtons()
        self._cursor = None

        self.scene().sigMouseClicked.connect(self.mouse_clicked)

    def mouse_clicked(self, evt):
        if evt.button() == 1:
            x = self.getViewBox().mapSceneToView(evt.pos()).x()
            self.sig_mouse_clicked.emit(x)

    def update(self, mix):
        """Updates the plot according to the properties of the mix to plot.

        """

        mix.lock()

        # clear the currently depicted plot
        self.clear()

        tracks = [track for track in mix.tracks.items() if track[1].position +
                  track[1].num_segments <= mix.num_segments]
        if len(tracks) > 0:
            # get maximum absolute sample value for normalization
            max_value = max(np.abs(track[1].audio).max() for track in tracks)

            tracks = sorted(tracks, key=lambda x: x[1].position)

            decks = []
            for name, track in tracks:
                # sort tracks in 'smallest' decks possible
                deck = 0
                while True:
                    if deck >= len(decks):
                        # use a new deck
                        decks.append(track.position + track.num_segments)
                        break
                    elif track.position > decks[deck]:
                        decks[deck] = track.position + track.num_segments
                        break
                    deck += 1

                x_offset = mix.times[track.position]
                # mix audio to mono and normalize it
                y = track.display / max_value
                # calculate sample rates for x
                sample_rates = np.empty(y.size)
                for i in range(track.num_segments):
                    sample_rate = track.num_samples(
                        i) / mix.length(track.to_global(i))
                    start = track.sample_indeces[i]
                    stop = track.sample_indeces[i + 1]
                    sample_rates[start:stop] = 1 / sample_rate
                x = np.cumsum(sample_rates)
                # draw the track
                TrackItem(self, x + x_offset, y, deck, name)

            # add the cursor
            self._cursor = Cursor(self, mix.times[-1])

        mix.unlock()

    def move_cursor(self, dx):
        if self._cursor is not None:
            self._cursor.move(dx)

    def move_cursor_to(self, x):
        if self._cursor is not None:
            self._cursor.setValue(x)

import enum
import numpy as np
from pyqtgraph.Qt import QtCore

from adapta.model.playback import Buffer
from adapta.util import round_, singleton, use_settings, Threadable


class State(enum.Enum):
    blocking = 0
    scheduled = 1
    ignoring = 2
    awaiting = 3


@singleton
@use_settings
class Player(Threadable):
    """Class controlling the mix playback. Reponsible for requesting mix
    samples to be computed and passing them to an output unit.

    """

    """ Settings """
    # output sample rate in Hz
    sample_rate = int
    # number of output channels
    num_channels = int
    # jump to 'containing' or 'nearest' segment upon click on plot
    jump_to = str
    # playback position update frequency in Hz
    update_freq = int

    """ Signals """
    sig_request = QtCore.Signal(int)
    sig_play = QtCore.Signal(object)
    sig_state = QtCore.Signal(object)
    sig_position = QtCore.Signal(object)

    def __init__(self):
        super().__init__()
        self._buffer = Buffer()
        self._index = 0
        self._position = 0
        self._instate = State.blocking
        self._outstate = State.blocking

    @property
    def samples_per_chunk(self):
        """Number of samples per chunk to send."""
        return round_(self.sample_rate / self.update_freq * self.num_channels)

    @property
    def position(self):
        """Playback position."""
        return self._position

    @property
    def playing(self):
        """True iff currently playing back."""
        return (self._outstate == State.awaiting or
                self._outstate == State.scheduled)

    def update(self, mix):
        """Update with new mix."""
        self._mix = mix
        self.stop()

    def toggle_play(self):
        """Toggle playback."""
        if self._outstate == State.blocking:
            self._play()
        else:
            self._outstate = State.blocking
        self._emit_state()

    def _play(self):
        """Start playback."""
        if self._buffer.filled >= self.samples_per_chunk:
            self._send()
        else:
            self._outstate = State.scheduled

    def send_samples(self):
        """Send samples to output unit."""
        if self._outstate == State.awaiting:
            self._outstate = State.blocking
            self._send()

    def _send(self):
        """Send samples to play back."""
        if (self._outstate == State.blocking):
            self._outstate = State.awaiting
            samples = self._buffer.pop(self.samples_per_chunk)
            self.sig_play.emit(samples)
            self._position += samples.size // self.num_channels
            self._emit_position()
            self._request()

    def _request(self):
        """Request next mix segment to be computed."""
        self._mix.lock()
        if (self._instate == State.blocking and
                self._index < self._mix.num_segments):
            num_samples = self._mix.num_samples(
                self._index) * self.num_channels
            if num_samples <= self._buffer.free:
                self._instate = State.awaiting
                self.sig_request.emit(self._index)
                self._index += 1
        self._mix.unlock()

    def receive(self, data):
        """Receive computed mix samples."""
        if self._instate == State.awaiting:
            self._buffer.put(data.ravel())
            if self._outstate == State.scheduled:
                self._outstate = State.blocking
                self._play()
        self._instate = State.blocking
        self._request()

    def _reset(self, index):
        """Reset computed samples and move to specific playback position."""
        self._mix.lock()
        self._index = index
        self._position = self._mix.sample_indeces[index]
        self._buffer.clear()
        if self._instate == State.awaiting:
            self._instate = State.ignoring
        if self._outstate == State.awaiting:
            self._outstate = State.scheduled
        self._emit_position()
        self._emit_state()
        self._request()
        self._mix.unlock()

    def stop(self):
        """Stop playback and reset to start of mix."""
        self._outstate = State.blocking
        self._reset(0)

    def jump(self, sample_index):
        """Jump to specific playback position."""
        self._mix.lock()
        index = np.searchsorted(
            self._mix.sample_indeces, sample_index, 'right')
        if index > 0:
            if index > self._mix.num_segments or self.jump_to == 'containing':
                index -= 1
            else:
                mean = self._mix.sample_indeces[index - 1: index + 1].mean()
                if sample_index <= mean:
                    index -= 1
        self._reset(index)
        self._mix.unlock()

    def next_track(self):
        """Jump to start of next track."""
        self._mix.lock()
        index = np.searchsorted(self._mix.sample_indeces,
                                self._position, 'right') - 1
        positions = sorted(
            set(map(lambda track: track.position, self._mix.tracks.values())))
        index = np.searchsorted(positions, index, 'right')
        if index < len(positions):
            index = positions[index]
            self._reset(index)
        self._mix.unlock()

    def previous_track(self):
        """Jump to start of nearest previous track."""
        self._mix.lock()
        index = np.searchsorted(self._mix.sample_indeces,
                                self._position, 'right') - 1
        positions = sorted(
            set(map(lambda track: track.position, self._mix.tracks.values())))
        index = np.searchsorted(positions, index) - 1
        index = max(index, 0)
        index = positions[index]
        self._reset(index)
        self._mix.unlock()

    def _emit_position(self):
        """Send playback position."""
        self.sig_position.emit(lambda: self.position)

    def _emit_state(self):
        """Send playback state."""
        self.sig_state.emit(lambda: self.playing)

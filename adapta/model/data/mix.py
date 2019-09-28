import json
from madmom.io import audio
import numpy as np
import os
from pyqtgraph.Qt import QtCore

from adapta.model.data import Audio, Track
from adapta.model.automation import parse, Tempo
from adapta.util import round_, int_, singleton, use_settings, Threadable


@singleton
@use_settings
class Mix(Threadable):
    """Class representing a whole mix.

    Parameters
    ----------
    path : str, optional
        The path to the json file determining the properties of the mix.

    """

    sample_rate = int
    bit_width = int
    num_channels = int

    sig_loaded = QtCore.Signal(object)
    sig_updated = QtCore.Signal(object)
    sig_segment = QtCore.Signal(object)
    sig_request_beats = QtCore.Signal(object)

    def __init__(self):
        super().__init__()
        self._tracks = {}

    def load(self, path):
        """Creates mix from the given json file.

        Parameters
        ----------
        path : str
            The path to the json file determining the properties of the mix.

        """

        self.lock()

        # load the json file
        with open(path) as jsonfile:
            mix = json.load(jsonfile)

        # allow file paths relative to mix file
        os.chdir(os.path.dirname(os.path.abspath(path)))

        # update the tracks of the mix
        self._tracks.clear()
        self._todo = []
        for name, params in mix['tracks'].items():
            track = Track(self, params)
            self._tracks[name] = track
            if not track.initialized:
                self._todo.append((name, track))

        self._todo.sort(key=lambda x: x[1].position)
        todo = [(name, track._params['audio']) for name, track in self._todo]
        self.sig_request_beats.emit(todo)

        self._automation = parse(mix['automation'])
        self._tempo = Tempo(self)

        self.sig_loaded.emit(self)
        self.update()
        self.unlock()

    def receive_beats(self, track, beats):
        self._tracks[track].init(beats)
        self.update()

    def update(self):
        self.lock()
        # load the tempo of the mix
        # and calculate the beat positions
        automation = self._automation['Tempo']
        index = None
        for i in range(len(automation)):
            track = self._tracks[automation[i][1]]
            if not track.initialized:
                index = i
                break
            is_constant = len(
                automation[i]) < 4 or automation[i][3] == 'constant'
            if not is_constant and i + 1 < len(automation):
                next_track = self._tracks[automation[i + 1][1]]
                if not next_track.initialized:
                    index = i
                    break
        automation = automation[:index]

        self._times = self._tempo(automation)
        self._times.setflags(write=False)

        # calculate corresponding sample indeces
        self._sample_indeces = round_(self._times * self.sample_rate)
        self._sample_indeces.setflags(write=False)

        self.sig_updated.emit(self)
        self.unlock()

    @property
    def tracks(self):
        """Dictionary holding references to the tracks of the mix."""
        return {name: track for name, track in self._tracks.items() if
                track.initialized}

    @property
    def times(self):
        """Reference to beat positions."""
        return self._times

    @property
    def sample_indeces(self):
        """Reference to beat sample indeces."""
        return self._sample_indeces

    @property
    def num_segments(self):
        """Total number of segments of the mix."""
        if hasattr(self, '_times'):
            candidates = [track.position for name, track in self._todo
                          if not track.initialized]
            candidates.append(self._times.size - 1)
            return min(candidates)
        return 0

    def length(self, start, stop=None):
        """Calculates the length of the specified segments in seconds.

        Parameters
        ----------
        start : int
            The segment index of the start of the segment range.
        stop : int, optional
            The segment index of the stop of the segment range.

        Returns
        -------
        float
            The length of the specified segment range in seconds.

        """

        if stop is None:
            stop = start + 1
        return self._times[stop] - self._times[start]

    def num_samples(self, start, stop=None):
        """Calculates the number of samples of the specified segments.

        Parameters
        ----------
        start : int
            The segment index of the start of the segment range.
        stop : int, optional
            The segment index of the stop of the segment range.

        Returns
        -------
        int
            The number of samples of the specified segment range.

        """

        if stop is None:
            stop = start + 1
        return self._sample_indeces[stop] - self._sample_indeces[start]

    def segment(self, index):
        """Fetches the audio from all tracks for the specified segment, and
        mixes and time stretches the audio into one audio segment.

        Parameters
        ----------
        index: int
            The index of the segment.

        Returns
        -------
        :class: `Audio`
            The mixed and time stretched audio.

        """

        if index >= self.num_segments:
            return np.empty(0, dtype=int_(self.bit_width))

        num_samples = self.num_samples(index)
        # prepare resulting array
        shape = self.num_samples(index)
        if self.num_channels > 1:
            shape = (shape, self.num_channels)
        result = np.zeros(shape, dtype=np.float_).view(Audio)
        result.sample_rate = self.sample_rate

        def mix(track):
            """Time stretches a specified track.

            Parameters
            ----------
            track: :class: `Track`
                The track to be mixed and time stretched.

            Returns
            -------
            :class: `Audio`
                The mixed and time stretched audio of the specified track.

            """

            # fetch the audio segment from the track
            segment = track.segments(index, local=False)

            # time stretching
            if num_samples != segment.num_samples:
                if self.use_resampling:
                    ratio = num_samples / segment.num_samples
                    segment = segment.resample(ratio * self.sample_rate)
                else:
                    import pyrubberband as pyrb
                    ratio = segment.num_samples / num_samples
                    stretched = np.apply_along_axis(
                        lambda x: pyrb.time_stretch(x, segment.sample_rate,
                                                    ratio),
                        0, segment)
                    stretched = stretched.view(Audio)
                    stretched.sample_rate = segment.sample_rate
                    return stretched

            return segment

        # time stretch the fetched segments of each track
        tracks = [track for track in self._tracks.values()
                  if track.available(index, local=False)]
        for segment in map(mix, tracks):
            min_length = min(segment.num_samples, result.num_samples)
            result[:min_length] += segment[:min_length]

        # limit the resulting values
        result = result.clip(-1.0, 1.0)

        # rescale audio to required format
        result = result.rescale(int_(self.bit_width))
        return result

    def send_segment(self, index):
        self.sig_segment.emit(self.segment(index))

    def render(self, path):
        """Writes the whole mix to a file.

        Parameters
        ----------
        path : str
            Path to the output file.

        """

        # fetch and concatenate all segments
        segments = []
        for i in range(self.num_segments):
            segment = self.segment(i)
            segments.append(segment)
        mix = np.concatenate(segments)

        # write to file
        audio.write_wave_file(mix, path, self.sample_rate)

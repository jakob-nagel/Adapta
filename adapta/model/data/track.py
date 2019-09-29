import numpy as np
import os

from adapta.model.data import Audio
from adapta.model.automation import parse, Equalizer, Volume
from adapta.util import (
    load_beats, round_, time_to_bpm, time_to_seconds, use_settings)


@use_settings
class Track:
    """Container class representing audio tracks. A track object stores the
    audio signal and beat positions of an audio track.

    Parameters
    ----------
    audio : :class:`Audio`
        The data to initialize the audio with.
    beats : str
        The file specifying the beat positions.
    volume : float, optional
        The volume of the audio in decibel.
    position : int, optional
        The position of the track in the beat grid.
    start : int, optional
        The beat index of the beat the track starts with.
    stop : int, optional
        The beat index of the beat the track ends with.

    """

    """ Settings """
    # display audio with effects applied
    display_automation = bool

    def __init__(self, mix, params):
        self._mix = mix
        params['audio'] = os.path.abspath(params['audio'])
        self._position = params.pop('position', 0)
        beats = params.pop('beats', None)
        self._params = params
        if beats is not None:
            times = load_beats(beats)
            self.init(times)

    def init(self, times):
        self._init(times, **self._params)

    def _init(self,
              times,
              audio,
              automation=None,
              start=None,
              length=None,
              volume=None):
        if start is None:
            start = 0
        else:
            if isinstance(start, str):
                start = time_to_seconds(start)
            index = np.searchsorted(times, start, 'right')
            if index > 0:
                mean = times[index - 1: index + 1].mean()
                if start <= mean:
                    index -= 1
            start = index

        stop = None if length is None else start + length + 1

        times = times[start:stop]
        # initialize audio
        self._audio = Audio(audio,
                            sample_rate=self._mix.sample_rate,
                            num_channels=self._mix.num_channels,
                            start=times[0],
                            stop=times[-1],
                            gain=volume,
                            dtype=np.float_)
        self._disp = self._audio
        # store local times
        self._times = times - times[0]
        self._times.setflags(write=False)
        # initialize other attributes
        self._sample_indeces = round_(self.times * self.audio.sample_rate)
        self._sample_indeces.setflags(write=False)

        if automation is not None:
            automation = parse(automation)
            if 'Volume' in automation:
                volume = Volume(self)
                self._audio = volume(automation['Volume'])
            if 'Equalizer' in automation:
                equalizer = Equalizer(self)
                self._audio = equalizer(automation['Equalizer'])
        self._audio.setflags(write=False)
        if self.display_automation:
            self._disp = self._audio

    @property
    def initialized(self):
        return hasattr(self, '_audio')

    @property
    def audio(self):
        """Reference to audio of the track."""
        return self._audio

    @property
    def display(self):
        if self._disp.num_channels > 1:
            self._disp = self._disp.remix(1)
        return self._disp

    @property
    def times(self):
        """Reference to local beat positions."""
        return self._times

    @property
    def sample_indeces(self):
        """Reference to local beat sample indeces."""
        return self._sample_indeces

    @property
    def position(self):
        """Global position of the track."""
        return self._position

    @property
    def num_segments(self):
        """Number of segments the track encompasses."""
        return self._times.size - 1

    @property
    def bpm(self):
        return time_to_bpm(np.diff(self._times).mean())

    def to_local(self, index):
        """Convert global to local segment index."""
        return index - self._position

    def to_global(self, index):
        """Convert local to global segment index."""
        return index + self._position

    def length(self, start, stop=None, local=True):
        """Calculates the length of the specified segments in seconds.

        Parameters
        ----------
        start : int
            The segment index of the start of the segment range.
        stop : int, optional
            The segment index of the stop of the segment range.
        local : bool, optional
            Flag determining whether local or global indeces are provided.

        Returns
        -------
        float
            The length of the specified segment range in seconds.

        """

        if stop is None:
            stop = start + 1
        if not local:
            start = self.to_local(start)
            stop = self.to_local(stop)
        return self._times[stop] - self._times[start]

    def num_samples(self, start, stop=None, local=True):
        """Calculates the number of samples of the specified segments.

        Parameters
        ----------
        start : int
            The segment index of the start of the segment range.
        stop : int, optional
            The segment index of the stop of the segment range.
        local : bool, optional
            Flag determining whether local or global indeces are provided.

        Returns
        -------
        int
            The number of samples of the specified segment range.

        """

        if stop is None:
            stop = start + 1
        if not local:
            start = self.to_local(start)
            stop = self.to_local(stop)
        return self._sample_indeces[stop] - self._sample_indeces[start]

    def available(self, start, stop=None, local=True):
        """Checks if the specified segments are available.

        Parameters
        ----------
        start : int
            The segment index of the start of the segment range.
        stop : int, optional
            The segment index of the stop of the segment range.
        local : bool, optional
            Flag determining whether local or global indeces are provided.

        Returns
        -------
        bool
            True iff all segments of the specified range are available.

        """

        if stop is None:
            stop = start + 1
        if not local:
            start = self.to_local(start)
            stop = self.to_local(stop)
        return self.initialized and 0 <= start and stop <= self.num_segments

    def segments(self, start, stop=None, local=True):
        """Fetches the specified segments of the track.

        Parameters
        ----------
        start : int
            The segment index of the start of the segment range.
        stop : int, optional
            The segment index of the stop of the segment range.
        local : bool, optional
            Flag determining whether local or global indeces are provided.

        Returns
        -------
        :class:`Audio`
            The audio to be played in the specified segment range.

        """

        if stop is None:
            stop = start + 1
        if not local:
            start = self.to_local(start)
            stop = self.to_local(stop)
        start_index = self._sample_indeces[start]
        stop_index = self._sample_indeces[stop]
        return self._audio[start_index:stop_index]

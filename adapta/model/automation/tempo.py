import numpy as np

from adapta.model.automation import Automation
from adapta.util import bpm_to_time


class Tempo(Automation):
    """Class for interpreting tempo specification.

    """

    class Node(Automation.Node):
        @property
        def source_bpm(self):
            """Original bpm."""
            if self._master is None:
                return self._values
            return self._master.bpm

        def values(self, master, tempo):
            if master in self._parent.tracks:
                self._master = self._parent.tracks[master]
                if tempo[-1] == '%':
                    factor = 1 + float(tempo[:-1]) / 100
                    return self.source_bpm * factor
                else:
                    try:
                        return float(tempo)
                    except ValueError:
                        return self.source_bpm
            else:
                self._master = None
                return float(tempo)

        def process(self, target):
            ratios = self._transition(target) / self.source_bpm

            if self._master is None:
                time = bpm_to_time(self._values)
                return np.tile(time, self.num_chunks(target)) / ratios

            start = self._master.to_local(self._index)
            stop = self._master.to_local(target._index + 1)
            lengths = np.diff(self._master.times[start:stop])
            return lengths / ratios

    @property
    def num_segments(self):
        return max(track.position + track.num_segments
                   for track in self._parent._tracks.values()
                   if track.initialized)

    def argtypes(self):
        return str, str

    def process(self, values):
        times = np.empty(values.size + 1)
        times[0] = 0.0
        times[1:] = np.cumsum(values)
        return times

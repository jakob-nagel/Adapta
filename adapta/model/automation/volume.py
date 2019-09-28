import numpy as np

from adapta.model.automation import PerSampleAutomation
from adapta.util import db_to_ratio


class Volume(PerSampleAutomation):
    def argtypes(self):
        return float

    def process(self, values):
        factors = db_to_ratio(values)
        num_channels = self._parent.audio.num_channels
        if num_channels > 1:
            factors = np.tile(factors, (num_channels, 1)).T
        return self._parent.audio * factors

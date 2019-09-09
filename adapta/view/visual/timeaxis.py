import pyqtgraph as pg

from adapta.util.functions import seconds_to_time
from adapta.util.settings import use_settings


@use_settings
class TimeAxis(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setScale(2)

    def tickStrings(self, values, scale, spacing):
        strings = super().tickStrings(values, scale, spacing)
        if self.in_minutes:
            return list(map(lambda x: seconds_to_time(float(x)), strings))
        return strings

    def tickSpacing(self, minVal, maxVal, size):
        levels = super().tickSpacing(minVal, maxVal, size)
        if maxVal - minVal > 100:
            return list(map(lambda x: (0.3 * x[0], x[1]), levels))
        return levels
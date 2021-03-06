import pyqtgraph as pg

from adapta.util import seconds_to_time, use_settings


@use_settings
class TimeAxis(pg.AxisItem):
    """Custom plot time axis to offer the <minutes:seconds> label format.

    """

    """ Settings """
    # label time in <minutes:seconds> format
    in_minutes = bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setScale(2)

    def tickStrings(self, values, scale, spacing):
        """Strings to display at ticks."""
        strings = super().tickStrings(values, scale, spacing)
        if self.in_minutes:
            return list(map(lambda x: seconds_to_time(float(x)), strings))
        return strings

    def tickSpacing(self, minVal, maxVal, size):
        """Spacing between ticks."""
        levels = super().tickSpacing(minVal, maxVal, size)
        if maxVal - minVal > 100:
            return list(map(lambda x: (0.3 * x[0], x[1]), levels))
        return levels

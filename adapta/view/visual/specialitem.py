import math
import numpy as np
import pyqtgraph as pg

from adapta.util import use_settings


@use_settings
class SpecialItem(pg.PlotDataItem):
    """A special kind of PlotDataItem. It pre-downsamples its data in order to
    enhance the downsampling performance. Additionally, its x data is not
    required to be equidistant anymore for downsampling and clipping.

    Parameters
    ----------
    See http://www.pyqtgraph.org/documentation/graphicsItems/plotdataitem.html.
    resolution : float, optional
        The minimum number of samples plotted per pixel.
    ratio : int, optional
        The ratio determining how many samples are discarded in each
        downsampling step.
    depth : int, optional
        The number of downsampling steps.

    """

    """ Settings """
    # number of samples per pixel
    resolution = float
    # frame size per downsampling step
    ratio = int
    # number of downsampling steps
    depth = int

    def __init__(self, *args, **kwargs):
        self.downsampled = None
        super().__init__(*args, **kwargs)

    def setData(self, *args, **kwargs):
        """Sets updates the data of this item. Additionally pre-downsamples
        the data.

        Parameters
        ----------
        See
        http://www.pyqtgraph.org/documentation/graphicsItems/plotdataitem.html.

        """

        super().setData(*args, **kwargs)
        diff = np.diff(self.xData)
        self.min_sample_rate = 1 / diff.max()
        self.max_y = self.yData.max()
        self.min_y = self.yData.min()
        self.updateDownsampled()

    def updateDownsampled(self):
        """Calculates the downsampled data for multiple downsampling steps.

        """

        y = self.yData
        self.downsampled = [y]
        # two values are calculated per frame
        # therefore use double ratio
        frame_size = self.ratio * 2
        for _ in range(self.depth):
            # calculate frames
            # and get max and min per frame
            num_frames = y.size // frame_size
            extrema = np.empty((num_frames, 2))
            y_reshaped = (y[:num_frames * frame_size]
                          .reshape((num_frames, frame_size)))
            extrema[:, 0] = y_reshaped.max(axis=1)
            extrema[:, 1] = y_reshaped.min(axis=1)
            y = extrema.reshape(num_frames * 2)
            self.downsampled.append(y)

    def getData(self):
        """Provides the x and y data stored in this item.

        Returns
        -------
        tuple
            The x and y data.

        """

        # if no data is stored yet, return nothing
        if self.xData is None:
            return (None, None)

        # check if display data needs to be updated
        if self.xDisp is None:
            x, y = self.xData, self.yData
            # use downsampling if the corresponding flag is set
            if self.opts['autoDownsample'] and self.downsampled is not None:
                x, y = self._downsample()
            # clip if the corresponding flag is set
            if self.opts['clipToView']:
                x, y = self._clip(x, y)
            # update display data
            self.xDisp = x
            self.yDisp = y
        return self.xDisp, self.yDisp

    def _downsample(self):
        """Provides the required downsampled x and y data.

        Returns
        -------
        tuple
            The required downsampled x and y data.

        """

        # calculate how many samples would plotted per pixel
        num_samples = (self.viewRect().right() -
                       self.viewRect().left()) * self.min_sample_rate
        samples_per_pixel = num_samples / self.getViewBox().width()
        # calculate the minimum depth required
        # to satisfy the resolution parameter
        depth = int(math.log(samples_per_pixel /
                             self.resolution, self.ratio))
        depth = np.clip(depth, 0, len(self.downsampled) - 1)
        # fetch the corresponding downsampled x and y
        y = self.downsampled[depth]
        sample_rate = self.yData.size // y.size
        x = self.xData[::sample_rate][:y.size]
        return x, y

    def _clip(self, x, y):
        """Clips the provided x and y data to the current view.

        Parameters
        ----------
        x : numpy array
            The x data.
        y : numpy array
            The y data.

        Returns
        -------
        tuple
            The clipped x and y data.

        """

        rect = self.viewRect()
        # check if the data is in the view at all
        if (rect.left() > x[-1]
                or rect.right() < x[0]
                or rect.top() > self.max_y
                or rect.bottom() < self.min_y):
            return [], []
        # calculate sample indeces
        first_sample = np.searchsorted(x, rect.left())
        last_sample = np.searchsorted(x, rect.right())
        return x[first_sample: last_sample], y[first_sample:last_sample]

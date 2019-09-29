import numpy as np
from warnings import warn

from adapta.util import int_, round_, use_settings


@use_settings
class Buffer:
    """Class representing a one-dimensional buffer data structure with an index
    for reading and an index for writing. Values are stored and returned in a
    first-in, first-out fashion.

    Parameters
    ----------
    shape : tuple
        The shape of the buffer.
    dtype : nump dtype, optional
        The data type of the buffer values.

    """

    """ Settings """
    # audio bit width in bit
    bit_width = int
    # buffer capacity in MB
    size = int
    # output warnings
    warnings = bool

    def __init__(self):
        size = self.size * 1024 ** 2 * 8
        shape = round_(size / self.bit_width)
        dtype = int_(self.bit_width)

        self._index = 0
        self._filled = 0
        # initialize managed space
        self._buffer = np.empty(shape, dtype=dtype)

    @property
    def capacity(self):
        """Number of values the buffer can store."""
        return self._buffer.shape[0]

    @property
    def filled(self):
        """Number of values stored in the buffer."""
        return self._filled

    @property
    def free(self):
        """Number of values that can be stored until the buffer is full."""
        return self.capacity - self._filled

    def clear(self):
        """Clears the buffer."""
        self._filled = 0

    def pop(self, num_values):
        """Reads and removes a number of values from the buffer.

        Parameters
        ----------
        num_values : int
            The number of values to pop.

        Returns
        -------
        numpy array
            An array representing the popped values.

        """

        # pop as much as possible
        if num_values > self.filled:
            if self.warnings:
                warn('more requested values than available buffer values')
            num_values = self.filled
        # calculate new index
        next_index = self._index + num_values
        if next_index >= self.capacity:
            # new index needs to be adjusted to the beginning of the buffer
            next_index -= self.capacity
            # implicit copy
            result = np.concatenate(
                (self._buffer[self._index:], self._buffer[:next_index]))
        else:
            # explicit copy
            result = self._buffer[self._index:next_index].copy()
        # update indexes
        self._index = next_index
        self._filled -= num_values

        return result

    def put(self, array):
        """Filles the buffer with new values.

        Parameters
        ----------
        array : numpy array
            The new values.

        Returns
        -------
        numpy array
            The values that did not fit due to the buffer's capacity.

        """

        num_values = array.shape[0]
        if num_values > self.free:
            # fill as much as possible
            # store values that could not be stored
            if self.warnings:
                warn('more new values than free buffer space')
            result = array[self.free:]
            array = array[:self.free]
            num_values = self.free
        else:
            result = np.array([], dtype=array.dtype)
        # calculate indexes
        index = (self._index + self.filled) % self.capacity
        next_index = index + num_values
        if next_index >= self.capacity:
            # new index needs to be adjusted to beginning of buffer
            next_index -= self.capacity
            split_at = num_values - next_index
            # implicit copy
            self._buffer[index:] = array[:split_at]
            self._buffer[:next_index] = array[split_at:]
        else:
            # implicit copy
            self._buffer[index:next_index] = array
        # update index
        self._filled += num_values

        return result

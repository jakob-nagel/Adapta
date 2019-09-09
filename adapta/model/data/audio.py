from madmom.audio import signal
import numpy as np

from adapta.util.functions import int_, intmax, round_


class Audio(signal.Signal):
    """Class representing an audio signal. Inherits its core functionality from
    madmom's Signal class, but adds convenience functions.

    Parameters
    ----------
    data : numpy array, str or file handle
        Signal data or file name or file handle.
    sample_rate : int, optional
        Desired sample rate of the signal [Hz], or 'None' to return the
        signal in its original rate.
    num_channels : int, optional
        Reduce or expand the signal to `num_channels` channels, or 'None'
        to return the signal with its original channels.
    start : float, optional
        Start position [seconds].
    stop : float, optional
        Stop position [seconds].
    norm : bool, optional
        Normalize the signal to maximum range of the data type.
    gain : float, optional
        Adjust the gain of the signal [dB].
    dtype : numpy data type, optional
        The data is returned with the given dtype. If 'None', it is returned
        with its original dtype, otherwise the signal gets rescaled. Integer
        dtypes use the complete value range, float dtypes the range [-1, +1].

    Notes
    -----
    For further documentation consult
    https://madmom.readthedocs.io/en/latest/modules/audio/signal.html.

    """

    def __new__(cls, data, *args, **kwargs):
        # convert data to Audio class if necessary
        data = super().__new__(cls, data, *args, **kwargs)
        if not isinstance(data, Audio):
            data = data.view(cls)
        return data

    @property
    def bit_width(self):
        """Number of bits representing each sample value."""
        return self.dtype.itemsize * 8

    def index_to_time(self, index):
        """Converts a sample index to the according local time of the signal.

        Parameters
        ----------
        index : int
            The sample index.

        Returns
        -------
        float
            Local time in seconds.

        """

        return index / self.sample_rate

    def time_to_index(self, time):
        """Converts a local time point to the according sample index.

        Parameters
        ----------
        time : float
            The local time in seconds.

        Returns
        -------
        int
            The sample index.

        """

        return round_(time * self.sample_rate)

    def remix(self, num_channels):
        """Changes the number of channels this audio signal uses.

        Parameters
        ----------
        num_channels : int
            The new number of channels.

        Returns
        -------
        :class:`Signal`
            A remixed copy of this signal.

        """

        return Audio(self, num_channels=num_channels)

    def resample(self, sample_rate):
        """Resamples this audio signal.

        Parameters
        ----------
        sample_rate : int
            The new sample rate in Hertz.

        Returns
        -------
        :class:`Signal`
            A resampled copy of this signal.

        """

        return Audio(self, sample_rate=sample_rate)

    def rescale(self, dtype):
        """Converts the data type of this audio signal to another type, while
        keeping data values equivalent.

        Parameters
        ----------
        dtype : numpy dtype
            The new data type. It needs to be a signed integer or float.

        Raises
        ------
        ValueError
            Raised if the new data type is incompatible with the current one.

        Returns
        -------
        :class:`Audio`
            An equivalent copy of this signal with the new data type.

        """

        # create a copy of this audio signal
        audio = Audio(self)

        # check if current type is an unsigned integer type
        if np.issubdtype(audio.dtype, np.unsignedinteger):
            # convert to equivalent signed integer type
            audio -= round_(intmax(audio.dtype) / 2)
            audio = audio.astype(int_(audio.bit_width))

        def match(current, future):
            """Checks if current and future data types are of specific type
            categories.

            Parameters
            ----------
            current : numpy type
                Type category checked for current data type.
            future : numpy type
                Type category checked for future data type.

            Returns
            -------
            bool
                True if and only if both current and future data types match
                the provided categories.

            """

            return (np.issubdtype(audio.dtype, current)
                    and np.issubdtype(dtype, future))

        # check how to convert
        if match(np.floating, np.floating):
            # float to float
            return audio.astype(dtype)
        if match(np.signedinteger, np.signedinteger):
            # int to int
            shift_bits = np.dtype(dtype).itemsize * 8 - audio.bit_width
            if shift_bits > 0:
                return np.left_shift(audio.astype(dtype), shift_bits)
            else:
                return np.right_shift(audio, shift_bits).astype(dtype)
        if match(np.floating, np.signedinteger):
            # float to int
            return (audio * intmax(dtype)).astype(dtype)
        if match(np.signedinteger, np.floating):
            # int to float
            return (audio / intmax(audio.dtype)).astype(dtype)

        # no match found
        raise ValueError("incompatible dtypes")

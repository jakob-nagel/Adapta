import math
import numpy as np
from scipy import signal

from adapta.model.data.audio import Audio
from adapta.model.data.automation import Automation
from adapta.util.functions import db_to_ratio


class Equalizer(Automation):
    def __init__(self, parent):
        super().__init__(parent)
        self.f_c = [1000, 8000]
        self.f_s = parent.audio.sample_rate
        self.reset_delays()

    @staticmethod
    def intermediate(f_s, f_c, G, Q=None):
        if Q is None:
            Q = 1 / math.sqrt(2)

        A = math.sqrt(math.pow(10, G / 20))
        omega_c = 2 * math.pi * f_c / f_s
        S = math.sin(omega_c)
        C = math.cos(omega_c)
        beta = math.sqrt(A) / Q
        return A, S, C, beta

    @staticmethod
    def low_shelf(A, S, C, beta):
        Ap = A + 1
        Am = A - 1
        gamma = beta * S

        b_0 = A * (Ap - Am*C + gamma)
        b_1 = 2 * A * (Am - Ap*C)
        b_2 = A * (Ap - Am*C - gamma)
        a_0 = Ap + Am*C + gamma
        a_1 = -2 * (Am + Ap*C)
        a_2 = Ap + Am*C - gamma

        return np.divide((b_0, b_1, b_2, a_0, a_1, a_2), a_0)

    @staticmethod
    def high_shelf(A, S, C, beta):
        Ap = A + 1
        Am = A - 1
        gamma = beta * S

        b_0 = A * (Ap + Am*C + gamma)
        b_1 = -2 * A * (Am + Ap*C)
        b_2 = A * (Ap + Am*C - gamma)
        a_0 = Ap - Am*C + gamma
        a_1 = 2 * (Am - Ap*C)
        a_2 = Ap - Am*C - gamma

        return np.divide((b_0, b_1, b_2, a_0, a_1, a_2), a_0)

    def reset_delays(self):
        shape = [2, 2]
        if self._parent.audio.num_channels > 1:
            shape.append(self._parent.audio.num_channels)
        self.zi = np.zeros(shape)

    def apply_filter(self, array, gain_bass, gain_mid, gain_treble):
        gain_bass -= gain_mid
        gain_treble -= gain_mid
        low = Equalizer.low_shelf(
            *Equalizer.intermediate(self.f_s, self.f_c[0], gain_bass))
        high = Equalizer.high_shelf(
            *Equalizer.intermediate(self.f_s, self.f_c[1], gain_treble))
        filter = np.row_stack((low, high))
        array = array * db_to_ratio(gain_mid)
        result, self.zi = signal.sosfilt(filter, array, 0, self.zi)
        return result

    def argtypes(self):
        return float, float, float

    def process(self, values):
        result = np.empty(self._parent.audio.shape, dtype=np.float_)
        for i in range(len(values)):
            start, stop = self._parent.sample_indeces[i:i+2]
            gains = values[i]
            result[start:stop] = self.apply_filter(
                self._parent.audio[start:stop], *gains)
        result = result.view(Audio)
        result.sample_rate = self.f_s
        return result

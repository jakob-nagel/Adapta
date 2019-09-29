import copy
import csv
import numpy as np

from adapta.util import expspace, isarray


def parse(path):
    """Read and parse an automation specification.

    """

    with open(path) as file:
        reader = csv.reader(file,
                            delimiter=' ',
                            quotechar='"',
                            quoting=csv.QUOTE_MINIMAL,
                            skipinitialspace=True)
        lines = [line for line in reader if len(line) > 0]

    feature_indeces = [i for i in range(len(lines)) if len(lines[i]) == 1]
    feature_indeces.append(len(lines))

    result = {}
    for i in range(len(feature_indeces) - 1):
        start = feature_indeces[i]
        stop = feature_indeces[i + 1]
        feature = lines[start][0]
        params = lines[start + 1:stop]
        result[feature] = params
    return result


class Automation:
    """Abstract base class for audio effect automation.

    """

    class Node:
        """Base class for audio effect specification mapping.

        """

        def __init__(self, parent, index, transition, *args):
            self._parent = parent
            self._index = index
            self._transition = getattr(self, transition)
            self._values = self.values(*args)
            if isarray(self._values) and len(self._values) == 1:
                self._values = self._values[0]

        def num_chunks(self, target):
            """Number of units to the next node.

            """

            return target._index - self._index

        # optional overwrite methods

        def values(self, *args):
            """Get stored parameters.

            """

            return args

        def process(self, target):
            """Process parameters up to next node.

            """

            return self._transition(target)

        # transition functions

        def constant(self, target):
            """Constant interpolation."""
            shape = self.num_chunks(target)
            if isarray(self._values):
                shape = (shape, 1)
            return np.tile(self._values, shape)

        def linear(self, target):
            """Linear interpolation."""
            return np.linspace(self._values, target._values,
                               self.num_chunks(target), False)

        def leftexp(self, target):
            """Left-bending exponential interpolation."""
            return expspace(self._values, target._values, 5,
                            self.num_chunks(target))

        def rightexp(self, target):
            """Right-bending exponential interpolation."""
            return expspace(self._values, target._values, -5,
                            self.num_chunks(target))

    def __init__(self, parent):
        self._parent = parent

    def __call__(self, params):
        """Process the whole audio effect mapping."""
        if len(params) == 0:
            return self.process(np.empty(0))

        nodes = []
        for param in params:
            index = int(param[0])
            if len(param) == self.num_args:
                transition = param[-1]
                param = param[1:-1]
            else:
                transition = 'constant'
                param = param[1:]
            argtypes = self.argtypes()
            if not isarray(argtypes):
                argtypes = (argtypes, )
            param = [f(x) for f, x in zip(argtypes, param)]
            nodes.append(self.Node(self._parent, index, transition, *param))
        if nodes[-1]._index < self.num_segments:
            nodes.append(copy.copy(nodes[-1]))
            nodes[-1]._index = self.num_segments

        results = []
        for i in range(len(nodes) - 1):
            results.append(nodes[i].process(nodes[i + 1]))
        results = np.concatenate(results)
        return self.process(results)

    def argtypes(self):
        """Determines the datatypes and number of the string input parameters.
        """
        return ()

    @property
    def num_args(self):
        """Number of expected parameters per node."""
        if isarray(self.argtypes()):
            return len(self.argtypes()) + 2
        return 3

    @property
    def num_segments(self):
        """Number of segments of the parent mix or track."""
        return self._parent.num_segments

    def process(self, values):
        """Interprete and process the nodes."""
        return values


class PerSampleAutomation(Automation):
    """Class changing Automation to apply audio effects on each parent sample
    rather than each parent segment.

    """

    class Node(Automation.Node):
        def num_chunks(self, target):
            return self._parent.num_samples(self._index, target._index)

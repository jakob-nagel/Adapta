import copy
import csv
import numpy as np

from adapta.util import expspace, isarray


def parse(path):
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
    class Node:
        def __init__(self, parent, index, transition, *args):
            self._parent = parent
            self._index = index
            self._transition = getattr(self, transition)
            self._values = self.values(*args)
            if isarray(self._values) and len(self._values) == 1:
                self._values = self._values[0]

        def num_chunks(self, target):
            return target._index - self._index

        # optional overwrite methods

        def values(self, *args):
            return args

        def process(self, target):
            return self._transition(target)

        # transition functions

        def constant(self, target):
            shape = self.num_chunks(target)
            if isarray(self._values):
                shape = (shape, 1)
            return np.tile(self._values, shape)

        def linear(self, target):
            return np.linspace(self._values, target._values,
                               self.num_chunks(target), False)

        def leftexp(self, target):
            return expspace(self._values, target._values, 5,
                            self.num_chunks(target))

        def rightexp(self, target):
            return expspace(self._values, target._values, -5,
                            self.num_chunks(target))

    def __init__(self, parent):
        self._parent = parent

    def __call__(self, params):
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
        return ()

    @property
    def num_args(self):
        if isarray(self.argtypes()):
            return len(self.argtypes()) + 2
        return 3

    @property
    def num_segments(self):
        return self._parent.num_segments

    def process(self, values):
        return values


class PerSampleAutomation(Automation):
    class Node(Automation.Node):
        def num_chunks(self, target):
            return self._parent.num_samples(self._index, target._index)

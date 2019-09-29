from madmom.features import DBNDownBeatTrackingProcessor, RNNDownBeatProcessor
from madmom.processors import SequentialProcessor

from adapta.util import use_settings


@use_settings
class BeatProcessor(SequentialProcessor):
    """ Settings """
    # assumed number of beats per bar
    beats_per_bar = int
    # constant tempo likelihood
    transition_lambda = 400

    def __init__(self, todo, results):
        preprocessor = RNNDownBeatProcessor()
        processor = DBNDownBeatTrackingProcessor(
            self.beats_per_bar,
            fps=100,
            transition_lambda=self.transition_lambda)
        sequence = (preprocessor, processor, lambda x: x[:, 0])
        super().__init__(sequence)

        self._todo = todo
        self._results = results

    def run(self):
        while True:
            tasks = self._todo.get()
            for name, audio in tasks:
                print('job started')
                beats = self.process(audio)
                self._results.put((name, beats))
                print('job done')

from pyqtgraph.Qt import QtCore


class Threadable(QtCore.QObject):
    """Base class providing a simple multithreading interface.

    """

    def __init__(self, *args):
        super().__init__()
        self._mutex = QtCore.QMutex(QtCore.QMutex.Recursive)

    def __del__(self):
        if hasattr(self, '_thread'):
            self._thread.quit()

    def create_thread(self):
        self._thread = QtCore.QThread()
        self.moveToThread(self._thread)
        self._thread.start()
        return self._thread

    def lock(self):
        self._mutex.lock()

    def unlock(self):
        self._mutex.unlock()

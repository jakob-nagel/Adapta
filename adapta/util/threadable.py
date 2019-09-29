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
        """Create own thread."""
        self._thread = QtCore.QThread()
        self.moveToThread(self._thread)
        self._thread.start()
        return self._thread

    def lock(self):
        """Disable access from other sources."""
        self._mutex.lock()

    def unlock(self):
        """Enable access from other sources."""
        self._mutex.unlock()

from multiprocessing import Process, Queue
from pyqtgraph.Qt import QtWidgets
import sys

from adapta.controller import Window
from adapta.model.beatdetection import BeatProcessor, Notifier
from adapta.model.data import Mix
from adapta.model.playback import Player
from adapta.util import load
from adapta.view.auditory import Stream
from adapta.view.visual import Plot


def connect(from_, to, adapter=None):
    if adapter is None:
        from_.connect(to)
    else:
        from_.connect(lambda *args: to(adapter(*args)))


def main(*args):
    if len(args) == 0:
        args = sys.argv[1:]

    if len(args) >= 1:
        load(args[0])

    todo = Queue()
    results = Queue()
    processor = BeatProcessor(todo, results)
    process = Process(target=processor.run, daemon=True)
    process.start()

    app = QtWidgets.QApplication(args)

    notifier = Notifier(results)
    notifier.create_thread()

    Mix().create_thread()
    Stream().create_thread()

    Window().insert_widget(Plot())
    Window().show()

    # Window
    # menu
    connect(Window().sig_open, Window().show_open_dialog)
    connect(Window().sig_load, Mix().load)
    connect(Window().sig_render, Window().show_render_dialog)
    connect(Window().sig_exit, app.quit)
    # buttons
    connect(Window().sig_toggle_play, Player().toggle_play)
    connect(Window().sig_stop, Player().stop)
    connect(Window().sig_skip_forward, Player().next_track)
    connect(Window().sig_skip_backward, Player().previous_track)
    # other
    connect(Window().sig_render_to, Mix().render)

    # Mix
    connect(Mix().sig_loaded, Window().enable_controls)
    connect(Mix().sig_loaded, Player().update)
    connect(Mix().sig_segment, Player().receive)

    connect(Mix().sig_request_beats, todo.put_nowait)
    connect(Mix().sig_request_beats, notifier.run)
    connect(notifier.sig_send, Mix().receive_beats)

    connect(Mix().sig_updated, Player()._request)
    connect(Mix().sig_updated, Plot().update)

    # Player
    connect(Player().sig_request, Mix().send_segment)
    connect(Player().sig_play, Stream().play)
    connect(Player().sig_position, Plot().move_cursor_to,
            lambda x: x() / Mix().sample_rate)
    connect(Player().sig_state, Stream().pause)
    connect(Player().sig_state, Window().set_play_icon, lambda x: not x())

    # Stream
    connect(Stream().sig_request, Player().send_samples)

    # Plot
    connect(Plot().sig_mouse_clicked, Player().jump,
            lambda x: x*Mix().sample_rate)

    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())

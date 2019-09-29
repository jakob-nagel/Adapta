import pkg_resources as pkg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from adapta.util import singleton, use_settings


@singleton
@use_settings
class Window(QtWidgets.QMainWindow):
    """Class providing the central window of the application.

    """

    """ Settings """
    # size of all buttons but the play button
    button_size = tuple
    # size of play butotn
    play_button_size = tuple
    # size of all icons but the play icon
    icon_size = int
    # size of play icon
    play_icon_size = int
    # initial window size
    start_with_size = tuple
    # initial window maximized
    start_maximized = bool

    """ Signals """
    sig_open = QtCore.Signal()
    sig_render = QtCore.Signal()
    sig_exit = QtCore.Signal()
    sig_skip_backward = QtCore.Signal()
    sig_stop = QtCore.Signal()
    sig_toggle_play = QtCore.Signal()
    sig_skip_forward = QtCore.Signal()
    sig_load = QtCore.Signal(str)
    sig_render_to = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.load_icons()
        self.init_ui()

    def load_icons(self):
        """Prepares the icons for the playback buttons.

        """

        icon_names = ['skip_forward', 'pause', 'play', 'skip_backward', 'stop']
        self._icons = {}
        for name in icon_names:
            icon = QtGui.QIcon(pkg.resource_filename(
                'adapta.resources', name + '.svg'))
            self._icons[name] = icon

    def init_ui(self):
        """Creates the ui of the window.

        """

        # create central widget
        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)

        # create menubar
        menu = self.menuBar().addMenu('File')
        act_open = menu.addAction('Open')
        act_render = menu.addAction('Render')
        menu.addSeparator()
        act_exit = menu.addAction('Exit')

        act_open.triggered.connect(self.sig_open.emit)
        act_render.triggered.connect(self.sig_render.emit)
        act_exit.triggered.connect(self.sig_exit.emit)

        # create buttons
        btn_skip_backward = QtWidgets.QPushButton(self)
        btn_stop = QtWidgets.QPushButton(self)
        btn_toggle_play = QtWidgets.QPushButton(self)
        btn_skip_forward = QtWidgets.QPushButton(self)

        self._btn_toggle_play = btn_toggle_play

        btn_skip_backward.setIcon(self._icons['skip_backward'])
        btn_stop.setIcon(self._icons['stop'])
        btn_toggle_play.setIcon(self._icons['play'])
        btn_skip_forward.setIcon(self._icons['skip_forward'])

        btn_skip_backward.setShortcut(QtCore.Qt.Key_Left)
        btn_stop.setAutoRepeat(False)
        btn_stop.setShortcut(QtCore.Qt.Key_Up)
        btn_toggle_play.setAutoRepeat(False)
        btn_toggle_play.setShortcut(QtCore.Qt.Key_Space)
        btn_skip_forward.setShortcut(QtCore.Qt.Key_Right)

        buttons = [btn_skip_backward, btn_stop,
                   btn_toggle_play, btn_skip_forward]

        for button in buttons:
            if button == btn_toggle_play:
                button.setIconSize(QtCore.QSize(
                    self.play_icon_size, self.play_icon_size))
                button.setFixedSize(*self.play_button_size)
            else:
                button.setIconSize(QtCore.QSize(
                    self.icon_size, self.icon_size))
                button.setFixedSize(*self.button_size)

        btn_skip_forward.clicked.connect(self.sig_skip_forward)
        btn_stop.clicked.connect(self.sig_stop.emit)
        btn_toggle_play.clicked.connect(self.sig_toggle_play.emit)
        btn_skip_backward.clicked.connect(self.sig_skip_backward)

        # create layouts
        lyt_controls = QtWidgets.QHBoxLayout()
        for button in buttons:
            lyt_controls.addWidget(button)
        lyt_controls.addStretch(1)

        lyt_main = QtWidgets.QVBoxLayout()
        lyt_main.addLayout(lyt_controls)

        widget.setLayout(lyt_main)

        self._lyt_main = lyt_main

        # create list of items that are deactivated until a mix is loaded
        self._disabled = [act_render] + buttons
        for item in self._disabled:
            item.setEnabled(False)

        # show window
        self.resize(*self.start_with_size)
        if self.start_maximized:
            self.setWindowState(self.windowState() | QtCore.Qt.WindowMaximized)
        self.setWindowTitle('AdAPTA')

    def insert_widget(self, widget, position=0):
        """Adds a widget to the window.

        """

        self._lyt_main.insertWidget(position, widget)

    def show_open_dialog(self):
        """Opens a file dialog to load a file to update the mix with.

        """

        # open the file dialog
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open', filter='*.json')
        # if a file has been specified, update mix, processor and player
        if path:
            self.sig_load.emit(path)

    def show_render_dialog(self):
        """Opens a file dialog to render the mix to a file.

        """

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Render', filter='*.wav')
        if path:
            self.sig_render_to.emit(path)

    def enable_controls(self):
        """Enables the playback controls.

        """

        for item in self._disabled:
            item.setEnabled(True)

    def set_play_icon(self, show_play=True):
        """Updates the icon of the play/pause button.

        """

        icon = 'play' if show_play else 'pause'
        self._btn_toggle_play.setIcon(self._icons[icon])

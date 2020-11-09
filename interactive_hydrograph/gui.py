import sys, os, time
from PyQt5 import QtGui, QtCore
from PyQt5 import QtWidgets as QtW

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavTool
import matplotlib.pyplot as plt

from interactive_hydrograph import hdf5_reader


class _RadioButtons(QtW.QWidget):
    """Widget for specifying model types."""

    def __init__(self, radio_options: list, *args, **kwargs):
        super(_RadioButtons, self).__init__(*args, **kwargs)
        self._options = radio_options
        self.widgets = dict()
        self._value = None
        self._construct()

    def _reset(self):
        self.widgets = dict()
        self._value = None
        for name, widget in self.widgets.items():
            widget.setChecked(False)

    def _construct(self):
        self._reset()
        layout = QtW.QVBoxLayout()
        for name in self._options:
            radio = QtW.QRadioButton(name)
            self.widgets[name] = radio
            # Connect to action
            radio.toggled.connect(self._toggle_selected)
            layout.addWidget(radio)
        self.setLayout(layout)

    def _toggle_selected(self, value):
        if value:
            r = self.sender()
            if r.isChecked() is True:
                self._value = r.text()

    @property
    def value(self):
        return self._value

    def set_value(self, which):
        self.widgets[which].setChecked(True)


class _NamedEntries(QtW.QWidget):
    """Widget for entering the required info for the head file reader."""

    def __init__(self, entry_names: list, *args, **kwargs):
        super(_NamedEntries, self).__init__(*args, **kwargs)

        self.widgets = dict()
        self._options = entry_names
        self._construct()

    def _construct(self):
        layout = QtW.QFormLayout()
        for name in self._options:
            entry = QtW.QLineEdit()
            self.widgets[name] = entry
            layout.addRow(name, entry)

        self.setLayout(layout)

    @property
    def value(self):
        return {name: widget.text() for name, widget in self.widgets.items()}

    def set_value(self, entry_values):
        for name, widget in self.widgets.items():
            widget.setText(str(entry_values[name]))


class _StackedNamedEntries(QtW.QStackedWidget):
    """Widget for entering the required info for the head file reader for
    multiple model types."""

    def __init__(self, required_entries: dict, *args, **kwargs):
        super(_StackedNamedEntries, self).__init__(*args, **kwargs)
        self._options = required_entries
        self.widgets = dict()
        self._construct()

    def _construct(self):
        layout = QtW.QVBoxLayout()
        for key_name, en in self._options.items():
            widget = _NamedEntries(entry_names=en)
            self.widgets[key_name] = widget
            self.addWidget(widget)

        layout.addWidget(self)
        self.setLayout(layout)

    def update_from_radio(self):
        radio = self.sender()
        if radio.isChecked() is True:
            self.set_value(which=radio.text())

    @property
    def value(self):
        active_entry = self.currentWidget()
        return active_entry.value

    def set_value(self, which: str, entry_values: dict = None):
        self.setCurrentWidget(self.widgets[which])
        if entry_values:
            self.widgets[which].set_value(entry_values)


class RadioControlledEntry(QtW.QWidget):
    """Widget for selecting a model type, and entering in the needed info for
    the head file reader."""

    def __init__(self, required_entries: dict, *args, **kwargs):
        super(RadioControlledEntry, self).__init__(*args, **kwargs)
        self._entry_options = required_entries
        self._radio_options = list(required_entries.keys())
        self.widgets = dict()
        self._construct()

    def _construct(self):
        self.widgets['radio'] = _RadioButtons(
            radio_options=self._radio_options
        )
        self.widgets['entry'] = _StackedNamedEntries(
            required_entries=self._entry_options
        )

        # Change the action for the radio buttons
        for name in self._radio_options:
            radio = self.widgets['radio'].widgets[name]
            radio.toggled.connect(self._toggle_selected)

        layout = QtW.QVBoxLayout()
        for name, widget in self.widgets.items():
            layout.addWidget(widget)
        self.setLayout(layout)

    def _toggle_selected(self, value):
        if value:
            radio = self.sender()
            if radio.isChecked() is True:
                self.widgets['entry'].set_value(radio.text())

    @property
    def value(self):
        return {k: v.value for k, v in self.widgets.items()}

    def set_value(self, which: str, entry_values: dict = None):
        self.widgets['radio'].set_value(which)
        if entry_values:
            self.widgets['entry'].set_value(which, entry_values)


class MatplotlibFigure(QtW.QWidget):
    def __init__(self, *args, **kwargs):
        super(MatplotlibFigure, self).__init__(*args, **kwargs)
        self.figure = plt.figure()
        self.canvas = FigCanvas(self.figure)
        self.toolbar = NavTool(self.canvas, self)

        layout = QtW.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, x, y):
        self.clf()
        ax = self.figure.add_subplot(111)
        ax.plot(x, y, '-')
        self.canvas.draw()

    def clf(self):
        self.figure.clear()


class FileFinder(QtW.QWidget):
    """Used to get a file as user input."""

    def __init__(self, file_types: str = None, directory: str = None,
                 *args, **kwargs):
        super(FileFinder, self).__init__(*args, **kwargs)
        self.setMinimumWidth(300)

        if file_types:
            file_types = 'All Files (*)'
        if not directory:
            directory = os.curdir

        self._value = None
        self.ft_str = file_types
        self.ft_options = file_types.split(';;')
        self.directory = directory
        self.widgets = dict()
        self._construct()

    def _construct(self):
        # region Widgets
        self.widgets['button'] = QtW.QPushButton('Find Head File')
        self.widgets['entry'] = QtW.QLineEdit()
        self.widgets['button'].clicked.connect(self.find_file)
        # endregion Widgets

        # region Layout
        layout = QtW.QHBoxLayout()
        for name, widget in self.widgets.items():
            layout.addWidget(widget)
        self.setLayout(layout)
        # endregion Layout

    def find_file(self, remember_new_dir=True):
        """Creates prompt."""
        file_name, _ = QtW.QFileDialog.getOpenFileName(
            parent=self,
            caption='Find Head File',
            directory=self.directory,
            filter=self.ft_str,
            initialFilter=self.selected_type
        )
        if file_name:
            self.set_value(file_name)

    @property
    def selected_type(self):
        """Returns the selected file type to be used in the window."""
        if self._value:
            ext = os.path.splitext(self._value)[-1]
            for file_type in self.ft_options:
                if ext in file_type:
                    return file_type
        return 'All Files (*)'

    @property
    def value(self):
        return self.widgets['entry'].text()

    def set_value(self, file_path: str):
        self.widgets['entry'].setText(file_path)
        self._value = file_path
        self.directory = file_path


class UserInputWindow(QtW.QWidget):
    def __init__(self, radio_requirements: dict, additional_requirements: dict,
                 button_text: str = 'Go', *args, **kwargs):
        super(UserInputWindow, self).__init__(*args, **kwargs)
        self._radio_opitons = radio_requirements
        self._entry_options = additional_requirements
        self._button_text = button_text
        self.widgets = dict()
        self._construct()

    def _construct(self):
        self.widgets['file_finder'] = FileFinder(
            file_types='HDF File (*.h5);;OUT File(*.out);;All Files (*)'
        )

        self.widgets['radio_entry'] = RadioControlledEntry(
            required_entries=self._radio_opitons
        )

        self.widgets['stacked_entry'] = _StackedNamedEntries(
            required_entries=self._entry_options
        )

        self.button = QtW.QPushButton(self._button_text)

        radios = self.widgets['radio_entry'].widgets['radio'].widgets
        for name, radio in radios.items():
            radio.toggled.connect(
                self.widgets['stacked_entry'].update_from_radio
            )

        layout = QtW.QVBoxLayout()
        for name, widget in self.widgets.items():
            layout.addWidget(widget)
        layout.addWidget(self.button)
        self.setLayout(layout)

    @property
    def value(self):
        return {k: v.value for k, v in self.widgets.items()}

    def set_value(self, file_path: str, which: str, radio_values: dict = None,
                  other_values: dict = None):
        self.widgets['file_finder'].set_value(file_path)
        self.widgets['radio_entry'].set_value(which, radio_values)
        self.widgets['stacked_entry'].set_value(which, other_values)


class MainWindow(QtW.QDialog):
    def __init__(self, all_requirements: dict, parent=None,
                 defaults: dict = None):
        super(MainWindow, self).__init__(parent)
        self.all_req = all_requirements
        self.array_cache = dict()
        self.threadpool = QtCore.QThreadPool()
        self.x, self.y = 0, 0

        self.setWindowTitle('Interactive Hydrograph Viewer')
        self.setWindowIcon(QtGui.QIcon('..\icon.png'))

        self.canvas = MatplotlibFigure()
        self.user_input_window = UserInputWindow(
            radio_requirements=all_requirements['size'],
            additional_requirements=all_requirements['location']
        )
        button = self.user_input_window.button
        button.disconnect()
        button.clicked.connect(self.go)

        layout = QtW.QHBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.user_input_window)
        self.setLayout(layout)

    def set_value(self, file_path: str, which: str, radio_values: dict = None,
                  other_values: dict = None):
        self.canvas.clf()
        self.user_input_window.set_value(
            file_path, which, radio_values, other_values
        )

    def go(self):
        self.load_data()
        self.plot()

    def plot(self):
        self.canvas.plot(self.x, self.y)

    def load_data(self):
        if self.file not in self.array_cache:
            print("loading from cache")
            self.array_cache[self.file] = hdf5_reader.get_array(
                file=self.file,
                model=self.model,
                **self.details
            )
        print("getting series")
        self.x, self.y = hdf5_reader.array_to_series(
            array=self.array_cache[self.file],
            model=self.model,
            **self.selection
        )

    @property
    def file(self):
        return os.path.abspath(self.user_input_window.value['file_finder'])

    @property
    def model(self):
        return self.user_input_window.value['radio_entry']['radio']

    @property
    def details(self):
        return self.user_input_window.value['radio_entry']['entry']

    @property
    def selection(self):
        return self.user_input_window.value['stacked_entry']


class ProgressWindow(QtW.QWidget):
    def __init__(self, text, *args, **kwargs):
        super(ProgressWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle(text)
        self.load_bar = QtW.QProgressBar()
        self.load_bar.setMinimumWidth(300)
        self.load_bar.setRange(0, 0)
        layout = QtW.QVBoxLayout()
        layout.addWidget(self.load_bar)
        self.setLayout(layout)

    def finish(self):
        self.load_bar.setRange(0, 100)
        self.load_bar.setValue(100)
        time.sleep(0.1)
        self.close()


class WorkerThread(QtCore.QRunnable):
    def __init__(self, fn, *args, **kwargs):
        print("Init worker")
        super(WorkerThread, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.loading = ProgressWindow('Running...')

    @QtCore.pyqtSlot()
    def run(self):
        print('Run')
        #self.loading.show()
        print("Loading")
        self.fn(*self.args, **self.kwargs)
        print("Finished")
        #self.loading.finish()


if __name__ == '__main__':
    # creating apyqt5 application
    app = QtW.QApplication(sys.argv)

    # creating a window object
    requirements = {
        'models': ['MODFLOW', 'IWFM'],
        'size': {
            'MODFLOW': ['Model Rows', 'Model Columns', 'Model Layers'],
            'IWFM': ['Model Elements', 'Model Layers']
        },
        'location': {
            'MODFLOW': ['Row', 'Column'],
            'IWFM': ['Element']
        }
    }
    main = MainWindow(all_requirements=requirements)
    main.set_value(
        file_path=r'D:\_ProjectWork\_Python\_modules\interactive_hydrograph\assets\HIST_CURR.h5',
        which='MODFLOW',
        radio_values={
            'Model Rows': 353, 'Model Columns': 206,
            'Model Layers': 4},
        other_values={'Row': 200, 'Column': 180}
    )

    # showing the window
    main.show()

    # loop
    sys.exit(app.exec_())

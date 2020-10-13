import sys
import os
from PyQt5 import QtGui
from PyQt5 import QtWidgets as QtW
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavTool
import matplotlib.pyplot as plt

from interactive_hydrograph import hdf5_reader


class _RadioWidget(QtW.QWidget):
    """Widget for specifying model types."""

    def __init__(self, radio_options: list, *args, **kwargs):
        super(_RadioWidget, self).__init__(*args, **kwargs)
        self.radio_dict = dict()
        self.user_input = None

        layout = QtW.QVBoxLayout()
        for name in radio_options:
            radio = QtW.QRadioButton(name)
            self.radio_dict[name] = radio
            # Connect to action
            radio.toggled.connect(self.set_selected)
            layout.addWidget(radio)

        self.setLayout(layout)

    def set_selected(self, value):
        r = self.sender()
        if r.isChecked() is True:
            self.user_input = r.text()


class _NamedEntries(QtW.QWidget):
    """Widget for entering the required info for the head file reader."""

    def __init__(self, entry_names: list, *args, **kwargs):
        super(_NamedEntries, self).__init__(*args, **kwargs)
        layout = QtW.QFormLayout()
        self.entries = dict()

        for name in entry_names:
            entry = QtW.QLineEdit()
            self.entries[name] = entry
            layout.addRow(name, entry)

        self.setLayout(layout)

    @property
    def user_input(self):
        return {name: widget.text() for name, widget in self.entries.items()}


class _StackedNamedEntries(QtW.QStackedWidget):
    """Widget for entering the required info for the head file reader for
    multiple model types."""

    def __init__(self, required_entries: dict, *args, **kwargs):
        super(_StackedNamedEntries, self).__init__(*args, **kwargs)
        self.stacked_entries = dict()

        layout = QtW.QVBoxLayout()
        for key_name, en in required_entries.items():
            widget = _NamedEntries(entry_names=en)
            self.stacked_entries[key_name] = widget
            self.addWidget(widget)

        layout.addWidget(self)
        self.setLayout(layout)

    def update_requirements(self, key_name):
        self.setCurrentWidget(self.stacked_entries[key_name])

    def update_from_radio(self):
        radio = self.sender()
        if radio.isChecked() is True:
            self.update_requirements(radio.text())

    @property
    def user_input(self):
        active_entry = self.currentWidget()
        return active_entry.user_input


class RadioControlledEntry(QtW.QWidget):
    """Widget for selecting a model type, and entering in the needed info for
    the head file reader."""

    def __init__(self, required_entries: dict, *args, **kwargs):
        super(RadioControlledEntry, self).__init__(*args, **kwargs)
        self.required_entries = required_entries
        self.radio_options = list(required_entries.keys())

        self.radio = _RadioWidget(
            radio_options=self.radio_options
        )
        self.stacked_entry = _StackedNamedEntries(
            required_entries=required_entries
        )

        # Change the action for the radio buttons
        for name in self.radio_options:
            radio = self.radio.radio_dict[name]
            radio.toggled.connect(self.update_stacked_entries)

        layout = QtW.QVBoxLayout()
        layout.addWidget(self.radio)
        layout.addWidget(self.stacked_entry)
        self.setLayout(layout)

    def update_stacked_entries(self, value):
        radio = self.sender()
        if radio.isChecked() is True:
            self.stacked_entry.update_requirements(radio.text())

    @property
    def user_input(self):
        return self.radio.user_input, self.stacked_entry.user_input


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
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(x, y, '-')
        self.canvas.draw()


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

        self.user_input = None
        self.ft_str = file_types
        self.ft_options = file_types.split(';;')
        self.directory = directory

        # region Widgets
        self.button = QtW.QPushButton('Find Head File')
        self.entry = QtW.QLineEdit()
        self.button.clicked.connect(self.find_file)
        # endregion Widgets

        # region Layout
        layout = QtW.QHBoxLayout()
        layout.addWidget(self.entry)
        layout.addWidget(self.button)
        self.setLayout(layout)
        # endregion Layout

    @property
    def selected_type(self):
        """Returns the selected file type to be used in the window."""
        if self.user_input:
            ext = os.path.splitext(self.user_input)[-1]
            for file_type in self.ft_options:
                if ext in file_type:
                    return file_type
        return 'All Files (*)'

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
            self.entry.setText(file_name)
            self.user_input = file_name
            self.directory = file_name


class UserInputWindow(QtW.QWidget):
    def __init__(self, radio_requirements: dict, additional_requirements: dict,
                 button_text: str = 'Go', *args, **kwargs):
        super(UserInputWindow, self).__init__(*args, **kwargs)

        self.file_finder = FileFinder(
            file_types='HDF File (*.h5);;OUT File(*.out);;All Files (*)'
        )

        self.model_selection = RadioControlledEntry(
            required_entries=radio_requirements
        )

        self.additional_inputs = _StackedNamedEntries(
            required_entries=additional_requirements
        )

        self.button = QtW.QPushButton(button_text)

        radios = self.model_selection.radio.radio_dict
        for name, radio in radios.items():
            radio.toggled.connect(
                self.additional_inputs.update_from_radio
            )

        layout = QtW.QVBoxLayout()
        layout.addWidget(self.file_finder)
        layout.addWidget(self.model_selection)
        layout.addWidget(self.additional_inputs)
        layout.addWidget(self.button)

        self.setLayout(layout)

    @property
    def user_input(self):
        file = self.file_finder.user_input
        name, details = self.model_selection.user_input
        additional = self.additional_inputs.user_input
        return file, name, details, additional


class MainWindow(QtW.QDialog):
    def __init__(self, all_requirements: dict, parent=None):
        super(MainWindow, self).__init__(parent)
        self.all_req = all_requirements
        self.array_cache = dict()

        self.setWindowTitle('Interactive Hydrograph Viewer')
        self.setWindowIcon(QtGui.QIcon('..\icon.png'))

        self.canvas = MatplotlibFigure()
        self.user_input_window = UserInputWindow(
            radio_requirements=all_requirements['size'],
            additional_requirements=all_requirements['location']
        )

        button = self.user_input_window.button
        button.disconnect()
        button.clicked.connect(self.plot)

        layout = QtW.QHBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.user_input_window)
        self.setLayout(layout)

    def plot(self):
        file, model, details, additional = self.user_input_window.user_input

        if file not in self.array_cache:
            self.array_cache[file] = hdf5_reader.get_array(
                file=file,
                model=model,
                **details
            )

        x, y = hdf5_reader.array_to_series(
            array=self.array_cache[file],
            model=model,
            **additional
        )

        self.canvas.plot(x, y)


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

    # showing the window
    main.show()

    # loop
    sys.exit(app.exec_())

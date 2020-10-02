import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from interactive_hydrograph import hdf5_reader


class _ModelRadioWidget(QtWidgets.QWidget):
    """Widget for specifying model types."""

    def __init__(self, model_options: list, *args, **kwargs):
        super(_ModelRadioWidget, self).__init__(*args, **kwargs)
        self.selected = None
        layout = QtWidgets.QVBoxLayout()

        for model_name in model_options:
            setattr(self, model_name, QtWidgets.QRadioButton(model_name))
            radio = getattr(self, model_name)
            radio.toggled.connect(self.set_selected)
            layout.addWidget(radio)

        self.setLayout(layout)

    def set_selected(self, value):
        r = self.sender()
        if r.isChecked() is True:
            self.selected = r.text()
            self.selected = r.text()


class _ModelRequirementEntries(QtWidgets.QWidget):
    """Widget for entering the required info for the head file reader."""

    def __init__(self, model_requirements: dict, *args, **kwargs):
        super(_ModelRequirementEntries, self).__init__(*args, **kwargs)
        layout = QtWidgets.QFormLayout()
        for req in model_requirements:
            w = QtWidgets.QLineEdit()
            setattr(self, req, w)
            layout.addRow(req, w)

        self.setLayout(layout)


class _MultipleModelRequirementEntries(QtWidgets.QStackedWidget):
    """Widget for entering the required info for the head file reader for
    multiple model types."""

    def __init__(self, model_requirements: dict, *args, **kwargs):
        super(_MultipleModelRequirementEntries, self).__init__(*args, **kwargs)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.requirement_values = dict()

        for model_name, requirements in model_requirements.items():
            w = _ModelRequirementEntries(requirements)
            setattr(self, model_name, w)
            self.addWidget(w)

        self.main_layout.addWidget(self)
        self.setLayout(self.main_layout)

    def update_requirements(self, model_name):
        self.setCurrentWidget(getattr(self, model_name))


class ModelTypeSelection(QtWidgets.QWidget):
    """Widget for selecting a model type, and entering in the needed info for
    the head file reader."""

    def __init__(self, model_requirements: dict, *args, **kwargs):
        super(ModelTypeSelection, self).__init__(*args, **kwargs)

        self.req = model_requirements
        self.opt = list(model_requirements.keys())
        self.selector = _ModelRadioWidget(self.opt)
        self.entry = _MultipleModelRequirementEntries(
            model_requirements=model_requirements
        )

        # Change the action for the radio buttons
        for model in self.opt:
            radio_button = getattr(self.selector, model)
            radio_button.toggled.connect(self.set_selected)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.selector)
        layout.addWidget(self.entry)
        self.setLayout(layout)

    def set_selected(self, value):
        r = self.sender()
        if r.isChecked() is True:
            self.entry.update_requirements(r.text())


class MatplotlibFigure(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(MatplotlibFigure, self).__init__(*args, **kwargs)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, x, y):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(x, y, '-')
        self.canvas.draw()


class HeadFileFinder(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(HeadFileFinder, self).__init__(*args, **kwargs)
        self.button = QtWidgets.QPushButton('Find Head File')
        self.entry = QtWidgets.QLineEdit()
        self.button.clicked.connect(self.find_file)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.entry)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def find_file(self):
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Find Head File',
            '',
            'HDF File (*.h5);;All Files (*)',
            options=options
        )
        if file_name:
            self.entry.setText(file_name)


class LocationSelection(QtWidgets.QStackedWidget):
    def __init__(self, model_requirements, *args, **kwargs):
        super(LocationSelection, self).__init__(*args, **kwargs)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.requirement_values = dict()

        for model_name, requirements in model_requirements.items():
            w = _ModelRequirementEntries(requirements)
            setattr(self, model_name, w)
            self.addWidget(w)

        self.main_layout.addWidget(self)
        self.setLayout(self.main_layout)

    def update_requirements(self, model_name):
        self.setCurrentWidget(getattr(self, model_name))


class DataEntry(QtWidgets.QWidget):
    def __init__(self, all_requirements: dict, *args, **kwargs):
        super(DataEntry, self).__init__(*args, **kwargs)
        self.setFixedWidth(300)

        self.file_finder = HeadFileFinder()
        self.model_selection = ModelTypeSelection(
            model_requirements=all_requirements['size']
        )
        self.location_selection = LocationSelection(
            model_requirements=all_requirements['location']
        )
        self.plot_button = QtWidgets.QPushButton('Get Hydrograph')
        self.plot_button.clicked.connect(self.plot)

        # Change the action associated with the radio buttons
        for model in all_requirements['models']:
            radio_button = getattr(self.model_selection.selector, model)
            radio_button.toggled.connect(self.set_selected)

        # create a Vertical Box layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.model_selection)
        layout.addWidget(self.file_finder)
        layout.addWidget(self.location_selection)
        layout.addWidget(self.plot_button)
        self.setLayout(layout)

    def plot(self):
        raise NotImplementedError("Cannot plot without canvas.")

    def set_selected(self, value):
        r = self.sender()
        if r.isChecked() is True:
            self.model_selection.selected = r.text()
            self.model_selection.entry.update_requirements(r.text())
            self.location_selection.update_requirements(r.text())


class MainWindow(QtWidgets.QDialog):
    def __init__(self, all_requirements: dict, parent=None):
        super(MainWindow, self).__init__(parent)
        self.all_req = all_requirements
        self.array_cache = dict()

        self.setWindowTitle('Interactive Hydrograph Viewer')
        self.canvas = MatplotlibFigure()
        self.source = DataEntry(all_requirements=all_requirements)
        self.source.plot_button.disconnect()
        self.source.plot_button.clicked.connect(self.plot)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.source)

        self.setLayout(layout)

    def plot(self):
        model = self.source.model_selection.selector.selected
        file = self.source.file_finder.entry.text()
        model_size_w = self.source.model_selection.entry.currentWidget()
        loc_sel_w = self.source.location_selection.currentWidget()

        if file not in self.array_cache:
            data_details = dict()
            for requirement in self.all_req['size'][model]:
                val = getattr(model_size_w, requirement).text()
                data_details[requirement] = val

            self.array_cache[file] = hdf5_reader.get_array(
                file=file,
                model=model,
                **data_details
            )

        request = dict()
        for requirement in self.all_req['location'][model]:
            val = getattr(loc_sel_w, requirement).text()
            request[requirement] = val

        x, y = hdf5_reader.array_to_series(
            array=self.array_cache[file],
            model=model,
            **request
        )

        self.canvas.plot(x, y)


if __name__ == '__main__':
    # creating apyqt5 application
    app = QtWidgets.QApplication(sys.argv)

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

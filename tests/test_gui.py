import unittest

from PyQt5 import QtCore, QtGui, QtWidgets
from interactive_hydrograph import gui


def ask_success():
    result = input("Did that work as expected? [y]/n:\n")
    if result == '':
        result = 'y'
    return result[0].lower()


class TestsGUI(unittest.TestCase):
    def test_radio_buttons(self):
        app = QtWidgets.QApplication([])
        window = gui._ModelRadioWidget(
            model_options=['MODFLOW', 'IWFM']
        )
        window.show()
        app.exec_()
        self.assertEqual(ask_success(), 'y')

    def test_model_requirement_entry(self):
        app = QtWidgets.QApplication([])
        window = gui._MultipleModelRequirementEntries(
            model_requirements={
                'MODFLOW': ['Rows', 'Columns', 'Layers'],
                'IWFM': ['Elements', 'Layers']
            }
        )
        window.show()
        app.exec_()
        self.assertEqual(ask_success(), 'y')

    def test_model_type_selection(self):
        app = QtWidgets.QApplication([])
        window = gui.ModelTypeSelection(
            model_requirements={
                'MODFLOW': ['Rows', 'Columns', 'Layers'],
                'IWFM': ['Elements', 'Layers']
            }
        )
        window.show()
        app.exec_()
        self.assertEqual(ask_success(), 'y')


if __name__ == '__main__':
    unittest.main()

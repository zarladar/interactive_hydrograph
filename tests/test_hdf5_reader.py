import unittest
from interactive_hydrograph import hdf5_reader


class TestsHDF5(unittest.TestCase):
    def setUp(self) -> None:
        self.head_file = r'..\assets\HIST_CURR.h5'
        self.heads = hdf5_reader.get_4d_array(
            file=self.head_file,
            rows=353,
            cols=206,
            lays=4
        )

    def test_array_size(self):
        self.assertEqual(
            self.heads.shape,
            (420, 4, 353, 206)
        )


if __name__ == '__main__':
    unittest.main()

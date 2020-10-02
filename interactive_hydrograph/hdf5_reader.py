import h5py
import numpy as np


def get_4d_array(file, rows, cols, lays, **kwargs):
    h5 = h5py.File(file, 'r')
    rows, cols, lays = int(rows), int(cols), int(lays)

    heads_2d = np.array(h5['/Datasets/Head/Values'])
    heads_4d = heads_2d[..., np.newaxis, np.newaxis]

    periods = heads_4d.shape[0]

    heads_4d = heads_4d.reshape((periods, lays, rows, cols))
    return heads_4d


def get_series(array, row, col):
    y = array[:, :, int(row), int(col)]
    x = range(y.shape[0])
    return x, y


def get_array(file: str, model: str, **kwargs):
    readers = {
        'MODFLOW': get_4d_array,
    }
    mapping = {
        'MODFLOW': {
            'Model Rows': 'rows',
            'Model Columns': 'cols',
            'Model Layers': 'lays'
        }
    }
    if model not in readers:
        raise NotImplementedError(f"Model type {model} not supported yet.")

    kwargs = {mapping[model][key]: value for key, value in kwargs.items()}
    return readers[model](file=file, **kwargs)


def array_to_series(array, model, **kwargs):
    readers = {
        'MODFLOW': get_series,
    }
    mapping = {
        'MODFLOW': {
            'Row': 'row',
            'Column': 'col',
        }
    }
    if model not in readers:
        raise NotImplementedError(f"Model type {model} not supported yet.")

    kwargs = {mapping[model][key]: value for key, value in kwargs.items()}

    return readers[model](array=array, **kwargs)

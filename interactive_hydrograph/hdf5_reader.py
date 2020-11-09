import os
import re
import json

import h5py
import numpy as np
import pandas as pd


def get_4d_array(file, rows, cols, lays, **kwargs):
    h5 = h5py.File(file, 'r')
    rows, cols, lays = int(rows), int(cols), int(lays)

    heads_2d = np.array(h5['/Datasets/Head/Values'])
    heads_4d = heads_2d[..., np.newaxis, np.newaxis]

    periods = heads_4d.shape[0]

    heads_4d = heads_4d.reshape((periods, lays, rows, cols))
    return heads_4d


def get_series(array, row, col):
    y = array[:, :, int(row) - 1, int(col) - 1]
    x = range(y.shape[0])
    return x, y


def iwfm_get_array(file, elements, **kwargs):
    return None

    cache = os.path.join(r'..\assets', 'file_cache_map.json')
    temp_head = check_cache(cache, file)
    if not os.path.exists(temp_head):
        create_formatted_iwfm_head_file(file, temp_head)
        add_to_cache(cache, file, temp_head)

    df = pd.read_csv(temp_head, sep='\s+')
    return df


def add_to_cache(cache_file, head_file, temp_head_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as CACHE_FILE:
            cache = json.load(CACHE_FILE)
    else:
        cache = dict()

    cache[head_file] = temp_head_file

    with open(cache_file, 'w') as CACHE_FILE:
        json.dump(cache, CACHE_FILE, indent=4)


def check_cache(cache_file, head_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as CACHE_FILE:
            cache = json.load(CACHE_FILE)
    else:
        cache = dict()
    if head_file in cache:
        return cache[head_file]
    else:
        base = os.path.basename(head_file)
        name, ext = os.path.splitext(base)
        return os.path.join(r'..\assets', name + '_edited' + ext)


def create_formatted_iwfm_head_file(src, dst):
    time_str = None
    layer = 0
    with open(src, 'r') as FILE, open(dst, 'w') as TEMP_HED:
        for line in FILE:
            if 'TIME' in line:
                line = line.replace('*', '').strip(' ').strip('\n')
                TEMP_HED.write(line + '   LAYER\n')
            elif '*' in line:
                pass
            else:
                line = line.strip(' ').strip('\n')
                line_list = re.split('\s+', line)
                if '/' in line_list[0]:  # Is a date
                    time_str = line_list[0]
                    layer = 0
                else:
                    line = time_str + '         ' + line
                layer += 1
                line = line + '   ' + str(layer) + '\n'
                TEMP_HED.write(line)


def iwfm_get_series(array, element):
    return list(range(1000)), list(range(1000))


def get_array(file: str, model: str, **kwargs):
    readers = {
        'MODFLOW': get_4d_array,
        'IWFM': iwfm_get_array
    }
    mapping = {
        'MODFLOW': {
            'Model Rows': 'rows',
            'Model Columns': 'cols',
            'Model Layers': 'lays'
        },
        'IWFM': {
            'Model Elements': 'elements',
            'Model Layers': 'lays',
        }
    }
    if model not in readers:
        raise NotImplementedError(f"Model type {model} not supported yet.")

    kwargs = {mapping[model][key]: value for key, value in kwargs.items()}
    reader = readers[model]
    result = reader(file=file, **kwargs)
    return result


def array_to_series(array, model, **kwargs):
    readers = {
        'MODFLOW': get_series,
        'IWFM': iwfm_get_series
    }
    mapping = {
        'MODFLOW': {
            'Row': 'row',
            'Column': 'col',
        },
        'IWFM': {
            'Element': 'element'
        }
    }
    if model not in readers:
        raise NotImplementedError(f"Model type {model} not supported yet.")
    kwargs = {mapping[model][key]: value for key, value in kwargs.items()}
    return readers[model](array=array, **kwargs)

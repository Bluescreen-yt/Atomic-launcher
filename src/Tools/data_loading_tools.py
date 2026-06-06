"""Utilities to load and save JSON configuration/data files.

This module provides two simple helpers used across the launcher to
load persisted configuration (with a fallback to defaults) and to save
data back to disk. The functions are intentionally small and dependency
free (beyond the standard library) so they can be used by other
startup components.
"""

import json
from os import makedirs
from os.path import exists, dirname

from settings import *


def load_data(data_path, default_data):
    """Load JSON data from `data_path` or return `default_data`.

    If the file exists but contains invalid JSON the function will log a
    message, overwrite the file with `default_data` and return the default.
    """

    if exists(data_path):
        with open(data_path, 'r') as save_file:
            try:
                return json.load(save_file)
            except json.JSONDecodeError:
                print('Save file is corrupted.\nCreating a new one with default data!')

    # If the file is missing or invalid, create it with default content
    save_data(default_data, data_path)
    return default_data


def save_data(data, save_path):
    """Write `data` as JSON to `save_path`, creating parent directories.

    Uses `indent=4` for readable files that are convenient for manual edits.
    """

    makedirs(dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as save_file:
        json.dump(data, save_file, indent=4)
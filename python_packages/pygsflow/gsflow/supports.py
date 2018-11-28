import os


def _get_file_abs(control_file=None, fn = None):
    control_folder = os.path.dirname(control_file)
    abs_file = os.path.abspath(os.path.join(control_folder, fn))
    return abs_file

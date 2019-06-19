#By Adam P. Ashcraft / SEA

import csv
import functools
import json
import time


PLUGINS = dict()


class Tools:

    def __init__(self):
        pass

    def csv_pull_key(self, csv_path, key_index):
        """Pull key from .csv file to array by index"""
        with open(csv_path, 'r') as data_file:
            reader = csv.reader(data_file, delimiter=',')
            keys = [str(col[key_index]) for col in reader]
        return keys

    def csv_writer(self, save_path, data):
        """Write 2D array to .csv file by row"""
        with open(save_path, 'w') as file:
            writer = csv.writer(file)
            for line in data:
                writer.writerow(line)

    def dict_writer(self, save_path, data):
        """Write dictionary to csv"""
        with open(save_path, 'w') as file:
            writer = csv.writer(file, dialect='excel')
            for k, v in data.items():
                writer.writerow([k, v])

    def text_writer(self, save_path, data):
        """Writes data to .txt file"""
        with open(save_path, 'w') as file:
            for item in data:
                file.write("{}\n".format(item))

    def json_writer(self, save_path, data, indent=4):
        """Writes data to .json file"""
        with open(save_path, 'w') as file:
            json.dump(data, file, indent=indent)

    def json_key_gen(self, save_path):
        with open(save_path, 'r') as file:
            data = json.load(file)
            keys = [item for item in data.keys()]
            return set(keys)


def timer(func):
    """Return function run time"""
    """Based closely on code from realpython.com"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"Finished {func.__name__!r} in {run_time:.4f} secs")
        return run_time
    return wrapper_timer


def debug(func):
    """Print the function signature and return value"""
    """Based closely on code from realpython.com"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")
        return value
    return wrapper_debug


def slow_down(_func=None, *, rate=1):
    """Slow down the decorated function by a set time"""
    """Based closely on code from realpython.com"""
    def decorator_slow_down(func):
        @functools.wraps(func)
        def wrapper_slow_down(*args, **kwargs):
            time.sleep(rate)
            return func(*args, **kwargs)
        return wrapper_slow_down

    if _func is None:
        return decorator_slow_down
    else:
        return decorator_slow_down(_func)


def register(func):
    """Register a function as a plug-in"""
    """Based closely on code from realpython.com"""
    PLUGINS[func.__name__] = func
    return func


def count_calls(func):
    """Count whenever a function is called"""
    """Based closely on code from realpython.com"""
    @functools.wraps(func)
    def wrapper_count_calls(*args, **kwargs):
        wrapper_count_calls.num_calls += 1
        print(f"Call {wrapper_count_calls.num_calls} of {func.__name__!r}")
        return func(*args, **kwargs)
    wrapper_count_calls.num_calls = 0
    return wrapper_count_calls


def singleton(cls):
    """Make a class a Singleton class (only one instance)"""
    """Based closely on code from realpython.com"""
    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton
    wrapper_singleton.instance = None
    return wrapper_singleton

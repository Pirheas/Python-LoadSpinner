"""
Thread safe Loading Spinner
"""

import os
import sys
from threading import Thread, RLock
from time import time, sleep


class LoadSpinnerException(Exception):
    """
    Exception raised when trying to start or stop a LoadSpinner
    At start when:
        - Another LoadSPinner is already running
    At stop when:
        - Not any LoadSpinner running currently
        - This LoadSpinner object is not the one running currently
    """
    pass


class ListStream:
    """
    Class used to bufferize output strings
    """
    def __init__(self):
        self.queue = []

    def write(self, sti):
        """
        Append a string to the buffer
        :param sti: String to bufferize
        """
        self.queue.append(sti)

    def flush(self):
        """
        Do nothing (had to be implemented to be compatible with buffers)
        :return: None
        """
        pass


class AbstractSpinner:
    """
    Base class for spinners
    """
    @staticmethod
    def get_chars():
        """
        Returns a string containing the list of chars used for the loading animation
        """
        raise NotImplementedError()

    def get_iterator(self):
        """
        Retrun an iterator that yield chars for the loading animation
        """
        chars = self.get_chars()
        if not isinstance(chars, str) or len(chars) <= 0:
            raise Exception('"get_chars()" must return a non-empty string')
        while True:
            for char in chars:
                yield char

class BarSpinner(AbstractSpinner):
    """
    Classic load spinner with bars
    """
    @staticmethod
    def get_chars():
        return '|/-\\'


class StarSpinner(AbstractSpinner):
    """
    Load spinner with 2 char: '°*'
    """
    @staticmethod
    def get_chars():
        return '°*'

class LoadSpinner:
    """
    Load spinner, show a text and an animation.
    """
    _running_lock = RLock()
    _running = False

    VERY_FAST = 20
    FAST = 16
    NORMAL = 12
    SLOW = 8
    VERY_SLOW = 4
    STDOUT_STANDARD = 0
    STDOUT_DISABLE = 1
    STDOUT_REDIRECT = 2

    def __init__(self, text='', speed=NORMAL, new_line=True,
                 stdout_type=STDOUT_REDIRECT, spinner=BarSpinner()):
        """
        :param text: Text to display during the loading
        :param speed: Spped of the animation (VERY_SLOW, SLOW, NORMAL, FAST, VERY_FAST)
        :param newline: If false, the text will be erased at the end of the loading time.
                        Otherwise it wll create a new line
        :param stdout_type: How the load spinner will react to new print actions:
                            -STDOUT_STANDARD: Standard way (not recommended, risk to display strange things)
                            -STDOUT_DISABLE: Disable the stdout until the end of the loading time
                            -STDOUT_REDIRECT: Will bufferize new outputs and show then as soon as possible (recommended)
        :param spinner: Spinner animation object
        """
        self.speed = int(speed)
        self.text = str(text)
        self.new_line = bool(new_line)
        self._stdout_type = int(stdout_type)
        self._stopped = True
        self._thread = None
        self._list_stdout = ListStream()
        self.update_spinner(spinner, accept_none=False)
        self._dirty_txt = False
        self._next_txt = ''
        self._out = None

    def update_spinner(self, spinner, accept_none=True):
        """
        Change the animation character of the spinner
        :param spinner: Spinner object with the wanted animation character
        :param accept_none: If True, it will not raise error if the spinner is None (no animation is this case)
        :return: None
        """
        if spinner is None:
            if not accept_none:
                raise Exception('Spinner can\'t be None')
            return
        if not isinstance(spinner, AbstractSpinner):
            raise Exception("Spinner must be an AbstractSpinner")
        self._spinchar = spinner.get_iterator()

    def start(self, raise_exception=False):
        """
        Start the LoadSpinner (animation + output modification)
        :param raise_exception: If False, no excpetion will be raised if another spinner is currently running
        :return: None
        """
        with LoadSpinner._running_lock:  # Thread safe
            if LoadSpinner._running is True:  # Check if another one is already running
                if raise_exception:
                    raise LoadSpinnerException('Impossible to start: Already spinning')
                return
            LoadSpinner._running = True
            self._stopped = False
        self._out = sys.__stdout__
        if self._stdout_type == self.STDOUT_DISABLE:
            sys.stdout = open(os.devnull, 'w')  # Output disabled
        elif self._stdout_type == self.STDOUT_REDIRECT:
            sys.stdout = self._list_stdout  # Output bufferized
        self._thread = Thread(target=self._thread_spinning, daemon=True, args=(self.speed,))
        self._thread.start()

    def stop(self, raise_exception=False):
        """
        Stop the LoadSpinner (animation + output modification)
        :param raise_exception: If False, no exception will be raised if the spinner is not currently running
        :return: None
        """
        with LoadSpinner._running_lock:  # Thread safe
            if LoadSpinner._running is False:
                if raise_exception:
                    raise LoadSpinnerException('No spinner running')
                return
            if self._stopped is True or self._thread is None:  # Check if this loadspinner is currently running
                if raise_exception:
                    raise LoadSpinnerException('This spinner is not currently spinning')
                return
            self._stopped = True
        self._thread.join()
        LoadSpinner._running = False
        self._thread = None
        self._print_queue()
        self._clear_loading_line()
        self._out.write(self.text)
        if self.new_line:
            self._out.write('\n')  # Print new line
            self._out.flush()
        else:
            self._clear_loading_line()  # Erase loadspinner line
        sys.stdin.flush()
        sys.stdout = sys.__stdout__  # Reset stdout


    def _clear_loading_line(self):
        """
        Erase the load spinner line
        :return: None
        """
        white_spaces = ' ' * (len(self.text) + 5)
        self._out.write('\r{0}\r'.format(white_spaces))
        self._out.flush()

    def _thread_spinning(self, speed):
        """
        Thread method that will update the LoadSpinner animation (and print bufferized output)
        :param speed: Speed fo the animation
        """
        refresh_frequency = 1 / speed
        sleep_time = 0.05
        self._print_total_sentence()
        start_time = time()
        while not self._stopped:
            self._check_dirty_text()
            self._print_queue()
            if time() - start_time >= refresh_frequency:
                self._print_total_sentence()
                start_time = time()
            sleep(sleep_time)

    def _check_dirty_text(self):
        """
        Check if the LoadSpinner has been changed
        :return: None
        """
        if self._dirty_txt:
            self._dirty_txt = False
            self._clear_loading_line()
            self.text = self._next_txt
            self._print_total_sentence()

    def _print_queue(self):
        """
        Print bufferized output
        :return: None
        """
        if self._stdout_type == self.STDOUT_REDIRECT:
            if len(self._list_stdout.queue) > 0:
                self._clear_loading_line()
                has_new_line = False
                while len(self._list_stdout.queue) > 0:
                    txt = self._list_stdout.queue.pop(0)
                    has_new_line = len(txt) > 0 and txt[-1] == '\n'
                    self._out.write(txt)
                if not has_new_line:
                    self._out.write('\n')
                self._out.flush()
                self._print_total_sentence()

    def _print_total_sentence(self):
        """
        Print the LoadSPinner sentence and the spinner character
        :return:
        """
        white_spaces = 4
        end = '{0}{1}'.format(' ' * white_spaces, '\b' * (white_spaces - 1))
        self._out.write('\r{0}{1}{2}'.format(self.text, next(self._spinchar), end))
        self._out.flush()

    def update(self, new_txt=None, spinner=None):
        """
        Modify the spinner type and the spinner sentence.
        :param new_txt: New text to show during the animation
        :spinner: New spinner object with the new characters for the animation
        :return: None
        """
        if new_txt is not None:
            self._next_txt = new_txt
            self._dirty_txt = True
        self.update_spinner(spinner)

    def __enter__(self):
        self.start(raise_exception=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(raise_exception=True)

def spindec(text='Loading...', speed=LoadSpinner.NORMAL, new_line=True,
            spinner=BarSpinner(), stdout_type=LoadSpinner.STDOUT_REDIRECT):
    """
    Decorator that will create a LoadSpinner (that will last until the end of the function it decorate)
    """
    def deco_wrapper(func):
        def func_wrapper(*args, **kwargs):
            with LoadSpinner(text, speed=speed, new_line=new_line,
                             spinner=spinner, stdout_type=stdout_type):
                return func(*args, **kwargs)
        return func_wrapper
    return deco_wrapper

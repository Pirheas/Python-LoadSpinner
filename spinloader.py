#!/usr/bin/env python3

import os
import sys
from threading import Thread, RLock
from time import sleep, time

class LoadSpinnerException(Exception):
    pass


class ListStream:
    def __init__(self):
        self.queue = []

    def write(self, s):
        self.queue.append(s)

    def flush(self):
        pass


class AbstractSpinner:
    def get_chars(self):
        raise NotImplementedError()

    def get_iterator(self):
        chars = self.get_chars()
        if not isinstance(chars, str) or len(chars) <= 0:
            raise Exception('"get_chars()" must return a non-empty string')
        while True:
            for c in chars:
                yield c

class BarSpinner(AbstractSpinner):
    def get_chars(self):
        return '|/-\\'


class StarSpinner(AbstractSpinner):
    def get_chars(self):
        return '°*'

class LoadSpinner:
  
    _running_lock =  RLock()
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
    
    def update_spinner(self, spinner, accept_none=True):
        if spinner is None:
            if not accept_none:
                raise Exception('Spinner can\'t be None')
            return
        if not isinstance(spinner, AbstractSpinner):
            raise Exception("Spinner must be an AbstractSpinner")
        self._spinchar = spinner.get_iterator()
        
        
    
    def start(self, raise_exception=False):
        with LoadSpinner._running_lock:
            if LoadSpinner._running is True:
                if raise_exception:
                    raise LoadSpinnerException('Impossible to start: Already spinning')
                return
            LoadSpinner._running = True
            self._stopped = False
        self._out = sys.__stdout__
        if self._stdout_type == self.STDOUT_DISABLE:
            sys.stdout = open(os.devnull, 'w')
        elif self._stdout_type == self.STDOUT_REDIRECT:
            sys.stdout = self._list_stdout
        self._thread = Thread(target=self._thread_spinning, daemon=True, args=(self.speed,))
        self._thread.start()

    def stop(self, raise_exception=False):
        with LoadSpinner._running_lock:
            if LoadSpinner._running is False:
                if raise_exception:
                    raise LoadSpinnerException('No spinner running')
                return
            if self._stopped is True or self._thread is None:
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
            self._out.write('\n')
            self._out.flush()
        else:
            self._clear_loading_line()
        sys.stdin.flush()
        sys.stdout = sys.__stdout__


    def _clear_loading_line(self):
        white_spaces = ' ' * (len(self.text) + 5)
        self._out.write('\r{0}\r'.format(white_spaces))
        self._out.flush()

    def _thread_spinning(self, speed):
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
        if self._dirty_txt:
            self._dirty_txt = False
            self._clear_loading_line()
            self.text = self._next_txt
            self._print_total_sentence()

    def _print_queue(self):
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
        white_spaces = 4
        end = '{0}{1}'.format(' ' * white_spaces, '\b' * (white_spaces - 1))
        self._out.write('\r{0}{1}{2}'.format(self.text, next(self._spinchar), end))
        self._out.flush()

    def update(self, new_txt=None, spinner=None):
        if new_txt is not None:
            self._next_txt = new_txt
            self._dirty_txt = True
        self.update_spinner(spinner)

    def __enter__(self):
        self.start(raise_exception=True)
        return self

    def __exit__(self, type, value, traceback):
        self.stop(raise_exception=True)

def spindec(text='Loading...', speed=LoadSpinner.NORMAL, new_line=True,
            spinner=BarSpinner(), stdout_type=LoadSpinner.STDOUT_REDIRECT):
    def deco_wrapper(func):
        def func_wrapper(*args, **kwargs):
            with LoadSpinner(text, speed=speed, new_line=new_line,
                             spinner=spinner, stdout_type=stdout_type):
                return func(*args, **kwargs)
        return func_wrapper
    return deco_wrapper


@spindec(text='Downloading...', new_line=False)
def time_consuming_function():
    sleep(8)

if __name__ == '__main__':
    with LoadSpinner('Generating keys...', speed=LoadSpinner.NORMAL, 
                     new_line=False, spinner=StarSpinner()) as ls:
        sleep(4)
        print('Key generated successfully')
        ls.update('Updating data...', BarSpinner())
        sleep(4)
        ls.update('Finishing...')
        sleep(2)
    print('Done')
    sleep(2)
    print('Downloading new things')
    time_consuming_function()

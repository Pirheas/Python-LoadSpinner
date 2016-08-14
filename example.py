#!/usr/bin/env python3

# Here is a few example for how to user LoadSpinner

from time import sleep
from spinloader import LoadSpinner, spindec, AbstractSpinner, BarSpinner


# Let's make a custom spinner
class CircleSpinner(AbstractSpinner):
    @staticmethod
    def get_chars():
        return '◓◑◒◐'


# As a decorator
@spindec(text='Doing some stuff... ', new_line=True, speed=LoadSpinner.FAST)
def time_consuming_function():
    sleep(4)


if __name__ == '__main__':
    # With the with statement
    with LoadSpinner('Here is my SpinLoader... ', speed=LoadSpinner.NORMAL,
                     new_line=False, spinner=CircleSpinner()) as ls:
        sleep(3)
        print('We can print text during the loading thanks to OUTPUT_REDIRECT ')  # Using print during animation
        sleep(3)
        ls.update('We can change text and animation... ', BarSpinner()) # Updating text and animation
        sleep(4)
        ls.update('This text will be erased at the end... ')  # Just update text
        sleep(3)
    print('Done')
    sleep(1)
    print('Let\'s try with the decorator')
    time_consuming_function()

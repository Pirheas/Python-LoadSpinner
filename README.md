# Python-LoadSpinner
Simple tools to display a spinner in the terminal

## Requirements
* Python >= 3.3

## Demo
The code in `example.py` would give this result:

![alt tag](https://raw.githubusercontent.com/Pirheas/Python-LoadSpinner/demo/demo.gif)

## Args
* speed
  * VERY_FAST
  * FAST
  * NORMAL (default)
  * SLOW
  * VERY_SLOW
* stdout_type
  * STDOUT_STANDARD  (Stdout doesn't change but it's not recommended to print anything in the console while the spinner is spinning)
  * STDOUT_REDIRECT (default) (Stdout is redirected to an internal list and will be printed without affecting the spinner)
  * STDOUT_DISABLE (Stdout is disabled)
* new_line (boolen default=True): If set to false, the latest line shown will be erased


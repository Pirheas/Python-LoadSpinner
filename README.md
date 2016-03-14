# Python-LoadSpinner
Simple tools to display a spinner durring command line tasks

## Requirements
* Python >= 3.3

## Example
This code:

```python
with LoadSpinner('Generating keys...', speed=LoadSpinner.FAST) as ls:
    sleep(4)
    print('Key generated successfully')
    ls.update('Updating data...')
    sleep(4)
    ls.update('Finishing...')
    sleep(2)
print('Done')
```

Is viewed as:

![alt tag](https://i.imgur.com/brP3MYt.gif)

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
  * STDOUT DISABLE (Stdout is disabled)
* new_line (boolen default=True): If set to false, the latest line shown will be erased

## Warnings
This class isn't thread safe (yet)


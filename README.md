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


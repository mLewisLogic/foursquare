# Tests

## Setup
Tests are run using [nose](http://pypi.python.org/pypi/nose). Install the nose package.

Make a copy of _creds.example.py and name it _creds.py

Update it to reflect credentials that you control.

## Run
In shell, run:

    nosetests

Please make sure all test pass before submitting pull requests.


#### Note
_creds.py is in the .gitignore to prevent your credentials from leaking.
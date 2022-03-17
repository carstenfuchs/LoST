Installation
============

```
$ cd ~
$ mkdir .virtualenvs
$ python3 -m venv ~/.virtualenvs/LoST
$ # The virtual env is activated below.
$ # source .virtualenvs/LoST/bin/activate

$ cd LoST/
$ ln -s ~/.virtualenvs/LoST/bin/activate
$ . activate
$ pip install wheel   # important for building pyscard in the next step!
$ pip install -r requirements.txt
```

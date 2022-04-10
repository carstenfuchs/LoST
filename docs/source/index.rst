.. Lori Stempeluhr Terminal documentation master file, created by
   sphinx-quickstart on Sun Apr 10 10:52:11 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Welcome to Lori Stempeluhr Terminal's documentation!
====================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Installation
------------

.. code-block:: console

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


.. comment

   Indices and tables
   ==================

   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

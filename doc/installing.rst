*****************
Installing PypeIt
*****************

This document describes how to install PypeIt.
Both for users and developers.

Installing Dependencies
=======================

Though we have tried to keep the number of dependencies low,
there are a few packages that need to be installed (various python packages
and linetools).

We highly recommend that you use Anaconda for the majority
of these installations.

Detailed installation instructions are presented below:

Python Dependencies
-------------------

PypeIt depends on the following list of Python packages.
Install these first.

We recommend that you use `Anaconda <https://www.continuum.io/downloads/>`_ to install and/or update these packages.

* `python <http://www.python.org/>`_ version 3.7 or later
* `numpy <http://www.numpy.org/>`_ version 1.16.0 or later
* `astropy <http://www.astropy.org/>`_ version 4.0 or later
* `scipy <http://www.scipy.org/>`_ version 1.2 or later
* `matplotlib <http://matplotlib.org/>`_  version 3.1 or later
* `numba <https://numba.pydata.org/>`_ version 0.39.0 or later (optional - some speed ups, inc. wavecal)
* `PyQT5 <https://wiki.python.org/moin/PyQt/>`_ version 5 (needed for linetools)
* `h5py <https://www.h5py.org/>`_ version 2.7 (for data I/O)
* `yaml <https://pyyaml.org/>`_ -- version 5.1
* `configobj <https://pypi.org/project/configobj/>`_ -- version 5.0.6 or later
* `scikit-learn <https://scikit-learn.org/stable/>`_ -- version 0.20 or later
* `IPython <https://ipython.org>`_ -- version 7.2.0 or later
* `linetools <https://github.com/linetools/linetools/>`_ -- version 0.2 or later

If you are using Anaconda, you can check the presence of these packages with::

	conda list "^python$|numpy|astropy$|scipy$|matplotlib|numba|PyQT|ginga|yaml|h5py"

If the packages have been installed, this command should print out all the packages and their version numbers.

If any of the packages are out of date, they can be updated with a command like::

	conda update scipy


GitHub cloning
++++++++++++++

The following packages need to be installed by cloning from GitHub:

* `ginga <https://github.com/profxj/ginga>`_ JXP's fork of Ginga

Do **not** use pip install for this.

To remind you, install via GitHub with a sequence like::

    git clone https://github.com/profxj/ginga
    cd ginga
    python setup.py install

This will push the code into your Python distribution.

PypeIt
======

Read all of the text in this sub-section before choosing how you
wish to install `PypeIt`.

If you are not using code on the edge of development, then
we recommend that you install PypeIt with `pip`::

    pip install pypeit

Nuff said.  If you have not yet satisfied all the requirements, PypeIt will fail
when you first attempt to run it.   Try it::

    run_pypeit -h

This will fail if one or more requirements are missing.
You can grab all of them (except `ginga`; see `GitHub cloning` above) by doing::

    pip install -r path/requirements.txt

where path is to wherever `pip` installed the code.  Or you can download the
`requirements.txt <https://github.com/pypeit/PypeIt/blob/master/pypeit/requirements.txt>`_ file
and run on it directly.

However, if you are going to use development branches (common, we fear)
then you will need to install via GitHub::

    git clone https://github.com/pypeit/PypeIt.git

And we then recommend you install with::

    python setup.py develop

Again, do a test run as above to check you have all the requirements.

Testing the Installation
========================

In order to assess whether PypeIt has been properly installed,
we suggest you run the following tests:

1. Ensure run_pypeit works
--------------------------
Go to a directory outside of the PypeIt directory (e.g. your home directory),
then type run_pypeit.::

	cd
	run_pypeit -h


2. Run the PypeIt unit tests
----------------------------

If you cloned the Repo (i.e., you did *not* use `pip`)
then you can run the standard tests by doing::

    cd `repository_folder`
    python setup.py test


3. Try the test suite -- ONLY FOR DEVELOPERS
--------------------------------------------

Ask for help if you really want to do this.

We have provided a suite of tests that you can download and run via this Repo:
`TestSuite <https://github.com/pypeit/PypeIt-development-suite>`_

It can be installed as follows::

	# we suggest installing this in the directory above PypeIt
	git clone https://github.com/pypeit/PypeIt-development-suite.git

To run the test::

	cd PypeIt-development-suite
	./pypeit_test all

.. note::

	pypeit_test can also take the argument kast instead of all. 


The test takes a while to run but should run without issue if all the packages have been properly installed. 

Developers
==========

For developers, see :doc:`development`.


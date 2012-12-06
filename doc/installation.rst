Installing Optimal Neuron
========================

Dependencies
------------

Optimal Neuron has the following hard dependencies:
* Inspyred
* Numpy

And the following soft dependencies:
* Scipy
* neuronpy
* NEURON
* pyMOOSE
* pyramidal
   

Optimal Neuron installation
---------------------
Install `git`_ and type:

::

    git clone https://github.com/vellamike/Optimal-Neuron.git

Then navigate to the "Optimal Neuron" directory and run the command:

::
   python setup.py install

You may need to run the above command with superuser rights. Optimal Neuron will now be installed.

pyMOOSE instllation
-------------------

The latest version of MOOSE with a Python interface can be installed as follows:

::

    svn co http://moose.svn.sourceforge.net/svnroot/moose/moose/branches/dh_branch moose
    cd moose
    make pymoose
    sudo cp -r python/moose /usr/lib/python2.7/dist-packages


Get a read only copy of libNeuroML
----------------------------------

Install `git`_ and type:

::

    git clone git://github.com/NeuralEnsemble/libNeuroML.git


More details about the git repository and making your own branch/fork are `here <how_to_contribute.html>`_.



.. _Git: http://rogerdudler.github.com/git-guide/


Install libNeuroML
------------------

Use the standard install method for Python packages:


::

    sudo python setup.py install


Get a read only copy of pyramidal
----------------------------------

::

    git clone https://github.com/vellamike/pyramidal.git


Install pyramidal
------------------

Use the standard install method for Python packages:


::

    sudo python setup.py install

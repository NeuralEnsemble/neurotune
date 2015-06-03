#Neurotune

This package provides neurotune, a package for optimizing electical models of excitable cells.

**This is a fork by Padraig Gleeson and others to continue development of Neurotune for use in OpenWorm and other projects**

[![Build Status](https://travis-ci.org/pgleeson/neurotune.svg?branch=master)](https://travis-ci.org/pgleeson/neurotune)

Full documentation can be found [here](http://optimal-neuron.readthedocs.org/en/latest/).

## Installation

### Dependencies
The following (python libraries) can be installed using pip or easy_install:

Hard dependencies:
  1. numpy
  2. inspyred
  3. SciPy
  
The package pyelectro is also required **(if using the pgleeson branch of neurotune, use pgleeson/pyelectro too)**:

    git clone https://github.com/pgleeson/pyelectro.git
    cd pyelectro
    sudo python setup.py install


Soft dependencies:
  1. neuronpy       **(Note: it's best to [install neuron from source](http://www.neuron.yale.edu/neuron/download/compile_linux) 
& [install for Python](http://www.neuron.yale.edu/neuron/static/new_doc/programming/python.html))**

### Using distutils

Install with the following command:

```
sudo python setup.py -install
```

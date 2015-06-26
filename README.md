#Neurotune

This package provides Neurotune, a package for optimizing electical models of excitable cells.

**This package was originally developed by [Mike Vella](https://github.com/vellamike). This is a fork by [Padraig Gleeson](https://github.com/pgleeson) and others to continue development of [pyelectro](https://github.com/pgleeson/pyelectro) and [Neurotune](https://github.com/pgleeson/neurotune) for use in [OpenWorm](http://www.openworm.org/) and other projects**

[![Build Status](https://travis-ci.org/pgleeson/neurotune.svg?branch=master)](https://travis-ci.org/pgleeson/neurotune)

Full documentation can be found [here](http://optimal-neuron.readthedocs.org/en/latest/).

## Installation

The following (Python libraries) can be installed using pip, easy_install, or ideally using [Anaconda](http://continuum.io/downloads):

**Hard dependencies**

- numpy
- inspyred
- SciPy
  
The package pyelectro is also required **(if using the pgleeson branch of neurotune, use pgleeson/pyelectro too)**:

    git clone https://github.com/pgleeson/pyelectro.git
    cd pyelectro
    sudo python setup.py install


**Soft dependencies**

- neuronpy       **(Note: it's best to [install neuron from source](http://www.neuron.yale.edu/neuron/download/compile_linux) 
& [install for Python](http://www.neuron.yale.edu/neuron/static/new_doc/programming/python.html))**


Install Neurotune with the following command:

```
sudo python setup.py -install
```

Note: the [Travic CI script](https://github.com/pgleeson/neurotune/blob/master/.travis.yml) shows the full set of commands for installation & execution of a simple example.

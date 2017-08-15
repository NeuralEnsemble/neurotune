# Neurotune

This package provides Neurotune, a package for optimizing electical models of excitable cells.

**This package was originally developed by [Mike Vella](https://github.com/vellamike). This has been updated by [Padraig Gleeson](https://github.com/pgleeson) and others (and moved to [NeuralEnsemble](https://github.com/NeuralEnsemble)) to continue development of [pyelectro](https://github.com/NeuralEnsemble/pyelectro) and [Neurotune](https://github.com/NeuralEnsemble/neurotune) for use in [OpenWorm](http://www.openworm.org/), [Open Source Brain](http://opensourcebrain.org/) and other projects**

[![Build Status](https://travis-ci.org/NeuralEnsemble/neurotune.svg?branch=master)](https://travis-ci.org/NeuralEnsemble/neurotune)

Full documentation can be found [here](http://neurotune.readthedocs.io/en/latest/).

## Installation

The following (Python libraries) can be installed using pip, easy_install, or ideally using [Anaconda](http://continuum.io/downloads):

**Hard dependencies**

- numpy
- inspyred
- SciPy
  
The package **pyelectro** is also required:

    git clone https://github.com/NeuralEnsemble/pyelectro.git
    cd pyelectro
    sudo python setup.py install


**Soft dependencies**

- PyNEURON       **(Note: it's best to [install NEURON from source](http://www.neuron.yale.edu/neuron/download/compile_linux) 
& [install for Python](http://www.neuron.yale.edu/neuron/static/new_doc/programming/python.html))**


Install Neurotune with the following command:

```
sudo python setup.py install
```

Note: the [Travic CI script](https://github.com/NeuralEnsemble/neurotune/blob/master/.travis.yml) shows the full set of commands for installation & execution of a number of examples.

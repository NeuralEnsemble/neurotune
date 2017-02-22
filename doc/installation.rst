Installing Neurotune
====================

The following (Python libraries) can be installed using pip, easy_install, or ideally using `Anaconda <http://continuum.io/downloads>`_:

**Hard dependencies**

- numpy
- inspyred
- SciPy
  
The package **pyelectro** is also required:


.. code-block:: bash

    git clone https://github.com/NeuralEnsemble/pyelectro.git
    cd pyelectro
    sudo python setup.py install


**Soft dependencies**

- PyNEURON       

Note: it's best to `install NEURON from source <http://www.neuron.yale.edu/neuron/download/compile_linux>`_ & `install for Python <http://www.neuron.yale.edu/neuron/static/new_doc/programming/python.html>`_ 


Install Neurotune with the following command:


.. code-block:: bash

    sudo python setup.py install


Note: the `Travis CI script <https://github.com/NeuralEnsemble/neurotune/blob/master/.travis.yml>`_ shows the full set of commands for installation & execution of a number of examples.


   
Requirements
---------------------
Neurotune has so far been tested on Ubuntu and OSX. It should however also work on Windows.

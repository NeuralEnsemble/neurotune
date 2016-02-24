#### An example which uses neurotune to optimise a parameterised sine wave against expected behaviour.

To run, install https://github.com/pgleeson/pyelectro, followed by https://github.com/pgleeson/neurotune, and then:

    cd examples/example_3
    python SineWaveOptimizer.py
    
  This will run a simple model to generate sine waves ([SineWaveController.py](https://github.com/pgleeson/neurotune/blob/master/examples/example_3/SineWaveController.py)) with a known set of parameters:
  
      sim_vars = {'amp':     65,
                  'period':  250,
                  'offset':  -10}
               
and then try to fit this model based on a set of constraints:

    min_constraints = [60,  150, -20]
    max_constraints = [100, 300, 10]
    
Should produce:

![](https://raw.githubusercontent.com/pgleeson/neurotune/master/examples/example_3/snap.jpg)

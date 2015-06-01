
# Implementation of SineWaveController
# moved to: https://github.com/pgleeson/neurotune/blob/master/neurotune/controllers.py

from neurotune.controllers import SineWaveController
    
    
if __name__ == '__main__':

    sim_vars = {'amp':     65,
               'period':  250,
               'offset':  -10}
    
    swc = SineWaveController(1000, 0.1)
        
  
    swc.run_individual(sim_vars, True, True)
    
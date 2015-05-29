
import math

from matplotlib import pyplot as plt
import numpy as np


class SineWaveController():
    
    def run_individual(self, sim_var, gen_plot=False, show_plot=True):
        """
        Run an individual simulation.

        The candidate data has been flattened into the sim_var dict. The
        sim_var dict contains parameter:value key value pairs, which are
        applied to the model before it is simulated.

        """
        print(">> Running individual: %s"%(sim_var))
        sim_time = 1000
        dt = 0.1
        t = 0
        times = []
        volts = []
        while t <= sim_time:
            v = sim_var['offset'] + (sim_var['amp'] * (math.sin( 2*math.pi * t/sim_var['period'])))
            times.append(t)
            volts.append(v)
            t += dt
            
        if gen_plot:
            info = ""
            for key in sim_var.keys():
                info+="%s=%s "%(key, sim_var[key])
            plt.plot(times,volts, label=info)
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=1)
            
            if show_plot:
                plt.show()
            
        return np.array(times), np.array(volts)
        
    
    def run(self,candidates,parameters):
        """
        Run simulation for each candidate
        
        This run method will loop through each candidate and run the simulation
        corresponding to its parameter values. It will populate an array called
        traces with the resulting voltage traces for the simulation and return it.
        """

        traces = []
        for candidate in candidates:
            sim_var = dict(zip(parameters,candidate))
            t,v = self.run_individual(sim_var)
            traces.append([t,v])

        return traces
    
    
if __name__ == '__main__':

    sim_vars = {'amp':     65,
               'period':  250,
               'offset':  -10}
               
    min_constraints = [60,  150, -20]
    max_constraints = [100, 300, 10]
    
    swc = SineWaveController()
        
  
    swc.run_individual(sim_vars, True, True)
    
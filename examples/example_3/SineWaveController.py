
import math
import numpy as np
from matplotlib import pyplot as plt
import sys
from pyelectro import analysis
import pprint
from neurotune import optimizers
from neurotune import evaluators
from neurotune import utils


class SineWaveController():
    
    def run_individual(self, sim_var, show=False):
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
            
        if show:
            plt.plot(times,volts)

            plt.legend("Vars: %s"%sim_var)
            plt.title("Vars: %s"%sim_var)

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
        
    if len(sys.argv) == 2 and sys.argv[1] == '-sim':
  
        swc.run_individual(sim_vars, True)
    
    else:
        
        times, volts = swc.run_individual(sim_vars, False)

        analysis_var={'peak_delta':0,'baseline':0,'dvdt_threshold':0, 'peak_threshold':0}

        surrogate_analysis=analysis.IClampAnalysis(volts,
                                                   times,
                                                   analysis_var,
                                                   start_analysis=0,
                                                   end_analysis=1000,
                                                   smooth_data=False,
                                                   show_smoothed_data=False)

        # The output of the analysis will serve as the basis for model optimization:
        surrogate_targets = surrogate_analysis.analyse()
        pp = pprint.PrettyPrinter(indent=4)


        weights={'average_minimum': 1.0,
             'spike_frequency_adaptation': 0,
             'trough_phase_adaptation': 0,
             'mean_spike_frequency': 0,
             'average_maximum': 1.0,
             'trough_decay_exponent': 0,
             'interspike_time_covar': 0,
             'min_peak_no': 1,
             'spike_broadening': 0,
             'spike_width_adaptation': 0,
             'max_peak_no': 1.0,
             'first_spike_time': 1.0,
             'peak_decay_exponent': 0,
             'pptd_error':0,
             'peak_linear_gradient':0}


        #make an evaluator
        my_evaluator=evaluators.IClampEvaluator(controller=swc,
                                                analysis_start_time=0,
                                                analysis_end_time=1000,
                                                target_data_path='',
                                                parameters=sim_vars.keys(),
                                                analysis_var=analysis_var,
                                                weights=weights,
                                                targets=surrogate_targets,
                                                automatic=False)

        population_size =  20
        max_evaluations =  60
        num_selected =     10
        num_offspring =    6
        mutation_rate =    0.5
        num_elites =       1
        
        #make an optimizer
        my_optimizer=optimizers.CustomOptimizerA(max_constraints,
                                                 min_constraints,
                                                 my_evaluator,
                                                 population_size=population_size,
                                                 max_evaluations=max_evaluations,
                                                 num_selected=num_selected,
                                                 num_offspring=num_offspring,
                                                 num_elites=num_elites,
                                                 mutation_rate=mutation_rate,
                                                 seeds=None,
                                                 verbose=True)
        
        #run the optimizer
        best_candidate = my_optimizer.optimize(do_plot=False)
        
        keys = sim_vars.keys()
        for i in range(len(best_candidate)):
            sim_vars[keys[i]] = best_candidate[i]
            
        fit_times, fit_volts = swc.run_individual(sim_vars, True)
        
        fit_analysis=analysis.IClampAnalysis(fit_volts,
                                                   fit_times,
                                                   analysis_var,
                                                   start_analysis=0,
                                                   end_analysis=1000,
                                                   smooth_data=False,
                                                   show_smoothed_data=False)

        fit_anal = fit_analysis.analyse()
        
        print("Surrogate analysis")
        pp.pprint(surrogate_targets)
        
        print("Fittest analysis")
        pp.pprint(fit_anal)
        
        utils.plot_generation_evolution(sim_vars.keys())
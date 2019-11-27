# -*- coding: utf-8 -*-
"""
Automated optimization of simulation of Basket cell
"""

__version__ = 0.1

from neuron import h
import neuron
import numpy as np
from neurotune import optimizers
from neurotune import evaluators
from neurotune import controllers
import os
import sys

class Simulation(object):

    """
    Simulation class - inspired by example of Philipp Rautenberg

        Objects of this class control a current clamp simulation. Example of use:

            >>> cell = Cell() #some kind of NEURON section
            >>> sim = Simulation(cell)
            >>> sim.go()
            >>> sim.show()

    """

    def __init__(self, recording_section, sim_time=1000, dt=0.05, v_init=-60):

        self.recording_section = recording_section
        self.sim_time = sim_time
        self.dt = dt
        self.go_already = False
        self.v_init=v_init

    def set_IClamp(self, delay=5, amp=0.1, dur=1000):
        """
        Initializes values for current clamp.
        
        Default values:
          
          delay = 5 [ms]
          amp   = 0.1 [nA]
          dur   = 1000 [ms]

        """
        stim = h.IClamp(self.recording_section(0.5))
        stim.delay = delay
        stim.amp = amp
        stim.dur = dur
        self.stim = stim

    def set_recording(self):
        # Record Time
        self.rec_t = neuron.h.Vector()
        self.rec_t.record(h._ref_t)
        # Record Voltage
        self.rec_v = h.Vector()
        self.rec_v.record(self.recording_section(0.5)._ref_v)

    def show(self):
        """
        Plot the result of the simulation once it's been intialized
        """

        from matplotlib import pyplot as plt

        if self.go_already:
            x = np.array(self.rec_t)
            y = np.array(self.rec_v)

            plt.plot(x, y)
            plt.title("Simulation voltage vs time")
            plt.xlabel("Time [ms]")
            plt.ylabel("Voltage [mV]")

        else:
            print("""First you have to `go()` the simulation.""")
        plt.show()
    
    def go(self, sim_time=None):
        """
        Start the simulation once it's been intialized
        """

        self.set_recording()
        h.dt = self.dt
        
        h.finitialize(self.v_init)
        neuron.init()
        if sim_time:
            neuron.run(sim_time)
        else:
            neuron.run(self.sim_time)
        self.go_already = True

class BasketCellController():

    """
    This is a canonical example of a controller class

    It provides a run() method, this run method must accept at least two parameters:
        1. candidates (list of list of numbers)
        2. The corresponding parameters. 
    """
    
    def __init__(self, show_plots):
        self.show_plots = show_plots

    def run(self,candidates,parameters):
        """
        Run simulation for each candidate
        
        This run method will loop through each candidate and run the simulation
        corresponding to it's parameter values. It will populate an array called
        traces with the resulting voltage traces for the simulation and return it.
        """

        traces = []
        for candidate in candidates:
            sim_var = dict(zip(parameters,candidate))
            t,v = self.run_individual(sim_var)
            traces.append([t,v])

        return traces

    def set_section_mechanism(self, sec, mech, mech_attribute, mech_value):
        """
        Set the value of an attribute of a NEURON section
        """
        for seg in sec:
            setattr(getattr(seg, mech), mech_attribute, mech_value)
    
    def run_individual(self,sim_var):
        """
        Run an individual simulation.

        The candidate data has been flattened into the sim_var dict. The
        sim_var dict contains parameter:value key value pairs, which are
        applied to the model before it is simulated.

        The simulation itself is carried out via the instantiation of a
        Simulation object (see Simulation class above).

        """

        #make compartments and connect them
        soma=h.Section()
        axon=h.Section()
        soma.connect(axon)
    
        axon.insert('na')
        axon.insert('kv')
        axon.insert('kv_3')
        soma.insert('na')
        soma.insert('kv')
        soma.insert('kv_3')
    
        soma.diam=10
        soma.L=10
        axon.diam=2
        axon.L=100
    
        #soma.insert('canrgc')
        #soma.insert('cad2')
    
        self.set_section_mechanism(axon,'na','gbar',sim_var['axon_gbar_na'])
        self.set_section_mechanism(axon,'kv','gbar',sim_var['axon_gbar_kv'])
        self.set_section_mechanism(axon,'kv_3','gbar',sim_var['axon_gbar_kv3'])
        self.set_section_mechanism(soma,'na','gbar',sim_var['soma_gbar_na'])
        self.set_section_mechanism(soma,'kv','gbar',sim_var['soma_gbar_kv'])
        self.set_section_mechanism(soma,'kv_3','gbar',sim_var['soma_gbar_kv3'])
    
        for sec in h.allsec():
            sec.insert('pas')
            sec.Ra=300
            sec.cm=0.75
            self.set_section_mechanism(sec,'pas','g',1.0/30000)
            self.set_section_mechanism(sec,'pas','e',-70)
    
        h.vshift_na=-5.0
        sim=Simulation(soma,sim_time=1000,v_init=-70.0)
        sim.set_IClamp(150, 0.1, 750)
        sim.go()
     
        if self.show_plots:
            sim.show()
    
        return np.array(sim.rec_t), np.array(sim.rec_v)
    



def main():    
    """
    The optimization runs in this main method
    """

    
    show_plots = not ('-nogui' in sys.argv)
    verbose = not ('-silent' in sys.argv)
    
    #make a controller
    my_controller= BasketCellController(show_plots)
    
    #parameters to be modified in each simulation
    parameters = ['axon_gbar_na',
                  'axon_gbar_kv',
                  'axon_gbar_kv3',
                  'soma_gbar_na',
                  'soma_gbar_kv',
                  'soma_gbar_kv3']
    
    #above parameters will not be modified outside these bounds:
    min_constraints = [0,0,0,0,0,0]
    max_constraints = [10000,30,1,300,20,2]


    # EXAMPLE - how to set a seed
    #manual_vals=[50,50,2000,70,70,5,0.1,28.0,49.0,-73.0,23.0] 

    #analysis variables, these default values will do:
    analysis_var={'peak_delta':0,
                  'baseline':0,
                  'dvdt_threshold':2}
    
    weights={'average_minimum': 1.0,
             'spike_frequency_adaptation': 1.0,
             'trough_phase_adaptation': 1.0,
             'mean_spike_frequency': 1.0,
             'average_maximum': 1.0,
             'trough_decay_exponent': 1.0,
             'interspike_time_covar': 1.0,
             'min_peak_no': 1.0,
             'spike_broadening': 1.0,
             'spike_width_adaptation': 1.0,
             'max_peak_no': 1.0,
             'first_spike_time': 1.0,
             'peak_decay_exponent': 1.0,
             'pptd_error':1.0}
    
    
    
    #make an evaluator, using automatic target evaluation:
    my_evaluator=evaluators.IClampEvaluator(controller=my_controller,
                                            analysis_start_time=1,
                                            analysis_end_time=500,
                                            target_data_path='100pA_1a.csv',
                                            parameters=parameters,
                                            analysis_var=analysis_var,
                                            weights=weights,
                                            targets=None, # because we're using automatic
                                            automatic=True,
                                            verbose=verbose)

    #make an optimizer
    my_optimizer=optimizers.CustomOptimizerA(max_constraints,min_constraints,my_evaluator,
                                      population_size=3,
                                      max_evaluations=100,
                                      num_selected=3,
                                      num_offspring=3,
                                      num_elites=1,
                                      seeds=None,
                                      verbose=verbose)

    #run the optimizer
    my_optimizer.optimize(do_plot=show_plots)

main()

# -*- coding: utf-8 -*-
"""
Simulation of Basket cell

"""

__version__ = 0.1

from neuron import h
import neuron
import numpy as np
from optimalneuron import optimizers
from optimalneuron import evaluators
from optimalneuron import controllers


class Simulation(object):

    """
    Simulation class inspired by Philipp Rautenberg

        Objects of this class control a current clamp simulation. Example of use:

            >>> cell = Cell()
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
        from matplotlib import pyplot as plt
        if self.go_already:
            x = np.array(self.rec_t)
            y = np.array(self.rec_v)
            plt.plot(x, y)
            #plt.title("Hello World")
            plt.xlabel("Time [ms]")
            plt.ylabel("Voltage [mV]")
            #plt.axis(ymin=-120, ymax=-50)
        else:
            print("""First you have to `go()` the simulation.""")
        plt.show()
    
    def go(self, sim_time=None):
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
    This is an example of "canonical controler"
    """

    def run(self,candidates,parameters):
        traces = []

        for candidate in candidates:
            sim_var = dict(zip(parameters,candidate))
            t,v = self.run_individual(sim_var)
            traces.append([t,v])

        return traces

    def set_section_mechanism(self, sec, mech, mech_attribute, mech_value):
        for seg in sec:
            setattr(getattr(seg, mech), mech_attribute, mech_value)
    
    def run_individual(self,sim_var):
  
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
    
        #nrntools.set_section_mechanism(sec,'kv','gbar',gkv_dend)
    
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
    
        sim.show()
    
        return np.array(sim.rec_t), np.array(sim.rec_v)
    


sim_var={}

sim_var['axon_gbar_na']    = 1000.0
sim_var['axon_gbar_kv']    = 2310.0
sim_var['axon_gbar_kv3']   = 0.0
sim_var['soma_gbar_na']    = 30.0
sim_var['soma_gbar_kv']    = 220.0
sim_var['soma_gbar_kv3']   = 330.0

my_controller= BasketCellController()

"""
Script to optimize Basket cell current injection response
"""


#first off we need to make an evaluator,


parameters = ['axon_gbar_na','axon_gbar_kv','axon_gbar_kv3','soma_gbar_na','soma_gbar_kv','soma_gbar_kv3']

#manual_vals=[50,50,2000,70,70,5,0.1,28.0,49.0,-73.0,23.0] # EXAMPLE - how to set a seed
min_constraints = [0,0,0,0,0,0]
max_constraints = [10000,30,1,300,20,2]

analysis_var={'peak_delta':0,'baseline':0,'dvdt_threshold':2}

weights={'average_minimum': 1.0, 'spike_frequency_adaptation': 1.0, 'trough_phase_adaptation': 1.0, 'mean_spike_frequency': 1.0, 'average_maximum': 1.0, 'trough_decay_exponent': 1.0, 'interspike_time_covar': 1.0, 'min_peak_no': 1.0, 'spike_broadening': 1.0, 'spike_width_adaptation': 1.0, 'max_peak_no': 1.0, 'first_spike_time': 1.0, 'peak_decay_exponent': 1.0,'pptd_error':1.0}


targets={'average_minimum': -38.839498793604541, 'spike_frequency_adaptation': 0.019619800882894008, 'trough_phase_adaptation': 0.005225712358530369, 'mean_spike_frequency': 47.353760445682454, 'average_maximum': 29.320249266525668, 'trough_decay_exponent': 0.11282542321257279, 'interspike_time_covar': 0.042610190921388166, 'min_peak_no': 34, 'spike_broadening': 0.81838856772318913, 'spike_width_adaptation': 0.0095057081186080035, 'max_peak_no': 35, 'first_spike_time': 164.0, 'peak_decay_exponent': -0.04596529555434687,'pptd_error':0}

#using automatic target evaluation:
#what we should do next is separate out the controller and pass it as an object to the evaluator-
#we really need to think about this deeply, separating the nrnproject logic from the neuronoptimizer
#may be quite hard

#remember, under my new design ideas evaluator is decoupled from the implementation as this is a job for controller

import os

my_evaluator=evaluators.IClampEvaluator(controller=my_controller,
                                        analysis_start_time=1,
                                        analysis_end_time=500,
                                        target_data_path='../experimental_data/100pA_1.csv',
                                        parameters=parameters,
                                        analysis_var=analysis_var,
                                        weights=weights,
                                        targets=targets,
                                        automatic=True)

my_optimizer=optimizers.CustomOptimizerA(max_constraints,min_constraints,my_evaluator,
                                  population_size=3,
                                  max_evaluations=100,
                                  num_selected=3,
                                  num_offspring=3,
                                  num_elites=1,
                                  seeds=None)
my_optimizer.optimize()

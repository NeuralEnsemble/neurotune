#!/usr/bin/python
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
from pyelectro import analysis
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
        self.v_init = v_init

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


class BasketCellController:

    """
    This is a canonical example of a controller class

    It provides a run() method, this run method must accept at least two parameters:
        1. candidates (list of list of numbers)
        2. The corresponding parameters.
    """

    def run(self, candidates, parameters):
        """
        Run simulation for each candidate

        This run method will loop through each candidate and run the simulation
        corresponding to it's parameter values. It will populate an array called
        traces with the resulting voltage traces for the simulation and return it.
        """

        traces = []
        for candidate in candidates:
            sim_var = dict(zip(parameters, candidate))
            t, v = self.run_individual(sim_var)
            traces.append([t, v])

        return traces

    def set_section_mechanism(self, sec, mech, mech_attribute, mech_value):
        """
        Set the value of an attribute of a NEURON section
        """
        for seg in sec:
            setattr(getattr(seg, mech), mech_attribute, mech_value)

    def run_individual(self, sim_var, show=False):
        """
        Run an individual simulation.

        The candidate data has been flattened into the sim_var dict. The
        sim_var dict contains parameter:value key value pairs, which are
        applied to the model before it is simulated.

        The simulation itself is carried out via the instantiation of a
        Simulation object (see Simulation class above).

        """

        # make compartments and connect them
        soma = h.Section()
        axon = h.Section()
        soma.connect(axon)

        axon.insert("na")
        axon.insert("kv")
        axon.insert("kv_3")
        soma.insert("na")
        soma.insert("kv")
        soma.insert("kv_3")

        soma.diam = 10
        soma.L = 10
        axon.diam = 2
        axon.L = 100

        # soma.insert('canrgc')
        # soma.insert('cad2')

        self.set_section_mechanism(axon, "na", "gbar", sim_var["axon_gbar_na"])
        self.set_section_mechanism(axon, "kv", "gbar", sim_var["axon_gbar_kv"])
        self.set_section_mechanism(axon, "kv_3", "gbar", sim_var["axon_gbar_kv3"])
        self.set_section_mechanism(soma, "na", "gbar", sim_var["soma_gbar_na"])
        self.set_section_mechanism(soma, "kv", "gbar", sim_var["soma_gbar_kv"])
        self.set_section_mechanism(soma, "kv_3", "gbar", sim_var["soma_gbar_kv3"])

        for sec in h.allsec():
            sec.insert("pas")
            sec.Ra = 300
            sec.cm = 0.75
            self.set_section_mechanism(sec, "pas", "g", 1.0 / 30000)
            self.set_section_mechanism(sec, "pas", "e", -70)

        h.vshift_na = -5.0
        sim = Simulation(soma, sim_time=1000, v_init=-70.0)
        sim.set_IClamp(150, 0.1, 750)
        sim.go()

        if show:
            sim.show()

        return np.array(sim.rec_t), np.array(sim.rec_v)


def main(
    targets,
    population_size=100,
    max_evaluations=100,
    num_selected=5,
    num_offspring=5,
    seeds=None,
):

    """
    The optimization runs in this main method
    """

    # make a controller
    my_controller = BasketCellController()

    # parameters to be modified in each simulation
    parameters = [
        "axon_gbar_na",
        "axon_gbar_kv",
        "axon_gbar_kv3",
        "soma_gbar_na",
        "soma_gbar_kv",
        "soma_gbar_kv3",
    ]

    # above parameters will not be modified outside these bounds:
    min_constraints = [0, 0, 0, 0, 0, 0]
    max_constraints = [10000, 30, 1, 300, 20, 2]

    # EXAMPLE - how to set a seed
    # manual_vals=[50,50,2000,70,70,5,0.1,28.0,49.0,-73.0,23.0]

    # analysis variables, these default values will do:
    analysis_var = {"peak_delta": 1e-4, "baseline": 0, "dvdt_threshold": 0.0}

    weights = {
        "average_minimum": 1.0,
        "spike_frequency_adaptation": 1.0,
        "trough_phase_adaptation": 1.0,
        "mean_spike_frequency": 1.0,
        "average_maximum": 1.0,
        "trough_decay_exponent": 1.0,
        "interspike_time_covar": 1.0,
        "min_peak_no": 1.0,
        "spike_broadening": 1.0,
        "spike_width_adaptation": 1.0,
        "max_peak_no": 1.0,
        "first_spike_time": 1.0,
        "peak_decay_exponent": 1.0,
        "pptd_error": 1.0,
    }

    data = "./100pA_1.csv"
    print("data location")
    print(data)

    # make an evaluator, using automatic target evaluation:
    my_evaluator = evaluators.IClampEvaluator(
        controller=my_controller,
        analysis_start_time=0,
        analysis_end_time=900,
        target_data_path=data,
        parameters=parameters,
        analysis_var=analysis_var,
        weights=weights,
        targets=targets,
        automatic=False,
        verbose=verbose,
    )

    # make an optimizer
    my_optimizer = optimizers.CustomOptimizerA(
        max_constraints,
        min_constraints,
        my_evaluator,
        population_size=population_size,
        max_evaluations=max_evaluations,
        num_selected=num_selected,
        num_offspring=num_offspring,
        num_elites=1,
        mutation_rate=0.5,
        seeds=seeds,
        verbose=verbose,
    )

    # run the optimizer
    best_candidate, fitness = my_optimizer.optimize(do_plot=False)

    return best_candidate


showPlots = not ("-nogui" in sys.argv)
verbose = not ("-silent" in sys.argv)


# Instantiate a simulation controller to run simulations
controller = BasketCellController()

# surrogate simulation variables:
sim_var = {
    "axon_gbar_na": 3661.79,
    "axon_gbar_kv": 23.23,
    "axon_gbar_kv3": 0.26,
    "soma_gbar_na": 79.91,
    "soma_gbar_kv": 0.58,
    "soma_gbar_kv3": 1.57,
}

parameters = [
    "axon_gbar_na",
    "axon_gbar_kv",
    "axon_gbar_kv3",
    "soma_gbar_na",
    "soma_gbar_kv",
    "soma_gbar_kv3",
]

# This seed should always "win" because it is the solution.
# dud_seed = [3661.79, 23.23, 0.26, 79.91, 0.58, 1.57]

surrogate_t, surrogate_v = controller.run_individual(sim_var, show=False)

analysis_var = {"peak_delta": 1e-4, "baseline": 0, "dvdt_threshold": 0.0}

surrogate_analysis = analysis.IClampAnalysis(
    surrogate_v,
    surrogate_t,
    analysis_var,
    start_analysis=0,
    end_analysis=900,
    smooth_data=False,
    show_smoothed_data=False,
)

# The output of the analysis will serve as the basis for model optimization:
surrogate_targets = surrogate_analysis.analyse()

assert surrogate_targets["max_peak_no"] == 13

weights = {
    "average_minimum": 1.0,
    "spike_frequency_adaptation": 1.0,
    "trough_phase_adaptation": 1.0,
    "mean_spike_frequency": 1.0,
    "average_maximum": 1.0,
    "trough_decay_exponent": 1.0,
    "interspike_time_covar": 1.0,
    "min_peak_no": 1.0,
    "spike_broadening": 1.0,
    "spike_width_adaptation": 1.0,
    "max_peak_no": 1.0,
    "first_spike_time": 1.0,
    "peak_decay_exponent": 1.0,
    "pptd_error": 1.0,
}

# Sanity check - expected is 0
evaluator = evaluators.IClampEvaluator(
    analysis_start_time=0,
    controller=controller,
    analysis_end_time=900,
    target_data_path=".",
    parameters=parameters,
    analysis_var=analysis_var,
    weights=weights,
    verbose=verbose,
)

fitness_value = evaluator.evaluate_fitness(
    surrogate_analysis, target_dict=surrogate_targets, target_weights=weights
)

assert fitness_value == 0.0
# raw_input()


c1_evals = 100
# Now try and get that candidate back, using the obtained targets:
candidate1 = main(
    surrogate_targets,
    population_size=10,
    max_evaluations=c1_evals,
    num_selected=5,
    num_offspring=10,
    seeds=None,
)

c2_evals = 500
candidate2 = main(
    surrogate_targets,
    population_size=30,
    max_evaluations=c2_evals,
    num_selected=5,
    num_offspring=10,
    seeds=None,
)

sim_var1 = {}
for key, value in zip(parameters, candidate1):
    sim_var1[key] = value

candidate1_t, candidate1_v = controller.run_individual(sim_var1, show=False)

sim_var2 = {}
for key, value in zip(parameters, candidate2):
    sim_var2[key] = value

candidate2_t, candidate2_v = controller.run_individual(sim_var2, show=False)

candidate1_analysis = analysis.IClampAnalysis(
    candidate1_v,
    candidate1_t,
    analysis_var,
    start_analysis=0,
    end_analysis=900,
    smooth_data=False,
    show_smoothed_data=False,
)

candidate1_analysis_results = candidate1_analysis.analyse()

candidate2_analysis = analysis.IClampAnalysis(
    candidate2_v,
    candidate2_t,
    analysis_var,
    start_analysis=0,
    end_analysis=900,
    smooth_data=False,
    show_smoothed_data=False,
)

candidate2_analysis_results = candidate2_analysis.analyse()

print("----------------------------------------")
print("Candidate 1 Analysis Results:")
print(candidate1_analysis_results)
print("Candidate 1 values:")
print(candidate1)

print("----------------------------------------")
print("Candidate 2 Analysis Results:")
print(candidate2_analysis_results)
print("Candidate 2 values:")
print(candidate2)

print("----------------------------------------")
print("Surrogate Targets:")
print(surrogate_targets)
print("Surrogate values:")
print(sim_var)
print("----------------------------------------")

if showPlots:
    # plotting
    from matplotlib import pyplot as plt

    (surrogate_plot,) = plt.plot(np.array(surrogate_t), np.array(surrogate_v))
    (candidate1_plot,) = plt.plot(np.array(candidate1_t), np.array(candidate1_v))
    (candidate2_plot,) = plt.plot(np.array(candidate2_t), np.array(candidate2_v))

    plt.legend(
        [surrogate_plot, candidate1_plot, candidate2_plot],
        [
            "Surrogate model",
            "Best model - %i evaluations" % c1_evals,
            "Best model - %i evaluations candidate" % c2_evals,
        ],
    )

    plt.ylim(-80.0, 80.0)
    plt.xlim(0.0, 1000.0)
    plt.title("Models optimized from surrogate solutions")
    plt.xlabel("Time (ms)")
    plt.ylabel("Membrane potential(mV)")
    plt.savefig("surrogate_vs_candidates.png", bbox_inches="tight", format="png")
    plt.show()

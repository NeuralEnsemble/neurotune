
from neurotune.controllers import SineWaveController

import sys
from neurotune import evaluators
from neurotune import optimizers
from neurotune import utils


if __name__ == '__main__':

    
    showPlots = not ('-nogui' in sys.argv)
    verbose = not ('-silent' in sys.argv)

    sim_vars = {'amp':     65,
               'period':  250,
               'offset':  -10}

    min_constraints = [60,  150, -20]
    max_constraints = [100, 300, 20]

    swc = SineWaveController(1000, 0.1)


    times, volts = swc.run_individual(sim_vars, showPlots, False)

    weights={'value_200': 1.0,
             'value_400': 1.0,
             'value_812': 1.0}


    data_analysis = evaluators.PointBasedAnalysis(volts, times)
    targets =  data_analysis.analyse(weights.keys())


    print("Target data: %s"%targets)

    #make an evaluator
    my_evaluator=evaluators.PointValueEvaluator(controller=swc,
                                            parameters=sim_vars.keys(),
                                            weights=weights,
                                            targets=targets)

    population_size =  20
    max_evaluations =  300
    num_selected =     10
    num_offspring =    5
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
                                             verbose=verbose)

    #run the optimizer
    best_candidate, fitness = my_optimizer.optimize(do_plot=False, seed=1234567)


    keys = list(sim_vars.keys())
    for i in range(len(best_candidate)):
        sim_vars[keys[i]] = best_candidate[i]        

    fit_times, fit_volts = swc.run_individual(sim_vars, showPlots, False)

    if showPlots:
        utils.plot_generation_evolution(sim_vars.keys(), sim_vars)
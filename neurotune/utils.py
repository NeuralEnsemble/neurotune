"""

    Script to plot evolution of parameters in neurotune

"""

import math
import numpy as np
try:
    from typing import List, Dict, Bool, Union
except ImportError:
    pass

import logging

logger = logging.getLogger(__name__)


def plot_generation_evolution(
    sim_var_names,
    target_values={},
    individuals_file_name="../data/ga_individuals.csv",
    show_plot_already=True,
    save_to_file=False,
    save_to_file_scatter=False,
    save_to_file_hist=False,
    save_to_file_output=False,
    title_prefix="",
):
    # type: (List, Dict, str, Bool, Union[Bool, str], Union[Bool, str], Union[Bool, str], Union[Bool, str], str) -> None
    """Plot generation evolution related graphs.

    :param sim_var_names: names of variables
    :type sim_var_names: list
    :param target_values: target values provided for fitting
    :type target_values: dict
    :param individuals_file_name: name of file storing data from individual generation runs
    :type individuals_file_name: str
    :param show_plot_already: whether showing plots should wait until plot() is called
    :type show_plot_already: bool
    :param save_to_file: name of file to save fitness plot to, False to not save
    :type save_to_file: str or bool
    :param save_to_file_scatter: name of file to save scatter plot to, False to not save
    :type save_to_file_scatter: str or bool
    :param save_to_file_hist: name of file to save histogram plot to, False to not save
    :type save_to_file_hist: str or bool
    :param save_to_file_output: name of file to save output plot to, False to not save
    :type save_to_file_output: str or bool
    :param title_prefix: prefix of plot title
    :type title_prefix: str

    """

    sim_var_names = list(sim_var_names)
    import matplotlib.pyplot as pyplot

    individuals_file = open(individuals_file_name)

    generations = []
    generations_all = []
    generations_offset = []

    f = []
    val_num = len(sim_var_names)
    nrows = math.ceil(math.sqrt(val_num))
    ncols = math.ceil(val_num / nrows)

    if val_num <= 3 or val_num == 5:
        nrows = val_num
        ncols = 1
    if val_num == 4:
        nrows = 2
        ncols = 2
    if val_num == 6:
        nrows = 3
        ncols = 2
    if val_num == 7 or val_num == 8:
        nrows = 4
        ncols = 2
    if val_num == 9:
        nrows = 3
        ncols = 3
    if val_num == 10:
        nrows = 5
        ncols = 2
    population_total = 0
    generations_total = 0

    for line in individuals_file:
        generation = int(line.split(",")[0])
        if generation == 0:
            population_total += 1
        generations_total = generation

    print(
        "Generating plots for %s variables over %s generations with population %s"
        % (val_num, generations_total, population_total)
    )
    logger.debug("Vals shown in %i rows x %i columns" % (nrows, ncols))

    vals = {}
    colours = {}
    sizes = {}
    ind_vals = {}

    for i in range(val_num):
        vals[i] = []
        colours[i] = []
        sizes[i] = []
        ind_vals[i] = {}

    # Go back to the starting of the file
    individuals_file.seek(0, 0)

    for line in individuals_file:
        main_info = line.split("[")[0]
        values = line.split("[")[1]
        generation = int(main_info.split(",")[0])
        individual = int(main_info.split(",")[1].strip())
        fitness = float(main_info.split(",")[2].strip())

        if individual == 0:
            logger.debug("Generation %s..." % generation)
            generations.append(generation)

        generations_all.append(generation)
        generations_offset.append(generation + (individual / 40.0))
        f.append(fitness)

        val_strings = values[:-2].split(",")

        for v in range(len(val_strings)):
            value = float(val_strings[v].strip())
            if individual == 0:
                ind_vals[v][generation] = []
            ind_vals[v][generation].append(value)
            vals[v].append(value)
            colours[v].append(individual)
            sizes[v].append((population_total - individual) * 2)

    if save_to_file_output:
        pyplot.savefig(save_to_file_output)

    fig = pyplot.figure()
    pyplot.get_current_fig_manager().set_window_title(
        title_prefix
        + " Evolution over %i generations of %s" % (generations_total, sim_var_names)
    )
    pyplot.subplots_adjust(hspace=0.4)
    pyplot.figtext(
        0.40,
        0.01,
        "Generation (%i individuals, offset slightly; larger circle => fitter)"
        % (population_total)
    )
    for i in range(val_num):

        var_name = sim_var_names[i]

        pyplot.subplot(nrows, ncols, i + 1, xlabel="Generation",
                       ylabel="{} ({})".format(var_name.split('/')[-2],
                                               var_name.split('/')[-1]))
        pyplot.title(var_name)
        if target_values is not None and sim_var_names[i] in target_values:
            value = target_values[sim_var_names[i]]
            x = [-1, generations_total + 1]
            y = [value, value]
            pyplot.plot(x, y, "--", color="grey")

        pyplot.scatter(generations_offset, vals[i], s=sizes[i], c=colours[i], alpha=0.4)
    if save_to_file_scatter:
        pyplot.savefig(save_to_file_scatter)

    fig = pyplot.figure()
    pyplot.get_current_fig_manager().set_window_title(
        title_prefix
        + " Fitness over %i generations from %s"
        % (generations_total, individuals_file_name)
    )

    ax = fig.add_subplot(2, 1, 1, ylabel="Fitness")
    ax.scatter(generations_offset, f, s=sizes[i], c=colours[i], alpha=0.4)

    ax = fig.add_subplot(2, 1, 2, ylabel="Fitness (log)")
    ax.set_yscale("log")
    ax.scatter(generations_offset, f, s=sizes[i], c=colours[i], alpha=0.4)
    pyplot.figtext(
        0.40,
        0.01,
        "Generation (%i individuals, offset slightly; larger circle => fitter)"
        % (population_total)
    )

    if save_to_file:
        pyplot.savefig(save_to_file)

    fig = pyplot.figure()
    pyplot.get_current_fig_manager().set_window_title(
        title_prefix + " Histograms over %i generations of %s" %
        (generations_total, sim_var_names)
    )

    pyplot.subplots_adjust(hspace=0.4)
    for i in range(val_num):

        var_name = (sim_var_names[i])
        ax = pyplot.subplot(nrows, ncols, i + 1,
                            xlabel="{} ({})".format(var_name.split('/')[-2],
                                                    var_name.split('/')[-1])
                            )
        pyplot.title(var_name)

        for generation in generations:
            values = ind_vals[i][generation]

            hist, bin_edges = np.histogram(values, bins=10)
            half_bin_width = (bin_edges[1] - bin_edges[0]) / 2
            xs = [be + half_bin_width for be in bin_edges[:-1]]

            shade = 1 - generation / (float(generations[-1]) + 1)
            # print("Gen: %s; shade: %s; value bins: %s; tots: %s"%(generation,shade,xs,hist))
            ax.plot(xs, hist, color=(shade, shade, shade))

    if save_to_file_hist:
        pyplot.savefig(save_to_file_hist)

    if show_plot_already:
        pyplot.show(block=True)

    individuals_file.close()


if __name__ == "__main__":

    # example 3
    target_values = {"amp": 65, "period": 250, "offset": -10}

    # example 2
    target_values = {
        "axon_gbar_na": 3661.79,
        "axon_gbar_kv": 23.23,
        "axon_gbar_kv3": 0.26,
        "soma_gbar_na": 79.91,
        "soma_gbar_kv": 0.58,
        "soma_gbar_kv3": 1.57,
    }

    parameters = [
        "leak_cond_density",
        "k_slow_cond_density",
        "k_fast_cond_density",
        "ca_boyle_cond_density",
        "specific_capacitance",
        "leak_erev",
        "k_slow_erev",
        "k_fast_erev",
        "ca_boyle_erev",
    ]

    # plot_generation_evolution(target_values.keys(), target_values)
    plot_generation_evolution(parameters)

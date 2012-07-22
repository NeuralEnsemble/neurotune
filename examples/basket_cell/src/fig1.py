# -*- coding: utf-8 -*-
"""
Make a composite image of all traces within the past 24-hours. To execute,
from a terminal window from this directory::
    
    python fig1.py

AUTHORS:

- THOMAS MCTAVISH (2010-08-11): initial version
"""
__version__ = 0.1

import os, datetime, pickle
from matplotlib import pyplot
from neuronpy.util import dictdb
import simdb, util

def run():
    """
    Retrieve the records of those simulations that finished in the past
    24 hours and draw their traces into one matplotlib figure as a PDF and
    PNG file.
    """
    (project_path, path_to_src) = util.get_project_and_src_paths()

    path_to_sims = os.path.join(project_path, 'sims')
    db, simdir = simdb.build_database(path_to_sims) # Build the database
    sub_dict = dict(dictdb.filter_dict(db, lambda k, v, p: \
            k == 'end_time' and \
            len(p) >= 2 and p[-2] == 'sim_info' and \
            (datetime.datetime.now() - v).days <= 1))
    
    # Initialize a figure
    fig = pyplot.figure()
    ax = fig.add_subplot(111)
    
    for (k, v) in sub_dict.iteritems():
        # k is the name of the simulation folder in the simdir directory.
        simpath = os.path.join(simdir, k)
            
        # Unpickle the vec.p files in the folder
        with open(os.path.join(simpath, 'v_vec.p')) as vec_file:
            v_vec = pickle.load(vec_file)
        with open(os.path.join(simpath, 't_vec.p')) as vec_file:
            t_vec = pickle.load(vec_file)
        
        # Draw the results to the figure
        ax.plot(t_vec, v_vec)

    # Save as a pdf file and a png file.
    outdir = path_to_sims = os.path.join(project_path, 'analysis')
    fig.savefig(os.path.join(outdir, 'fig1.pdf'))
    fig.savefig(os.path.join(outdir, 'fig1.png'))

if __name__ == "__main__":
    run()

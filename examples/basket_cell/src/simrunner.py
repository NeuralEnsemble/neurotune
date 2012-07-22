# -*- coding: utf-8 -*-
"""
Runs simulations and writes simulation output and parameter settings files.

.. Note::
    
    This module is peripheral to the actual simulation run. It is somewhat
    generalized for pre- and post-processing, initializing parameter 
    settings and then writing results to the simulation's output folder. 
    The module for running the simulation is :mod:`simrun`.

.. Note::
    
    This follows the same paradigm as :mod:`main` for processing command line
    arguments. In short, substituting ``simrunner`` for ``main`` using the
    same commands and arguments in :func:`main.run` will work here, but without
    source control. Operationally, running :mod:`main` with the ``without-hg``
    flag is much like running this.

As opposed to :mod:`main`, this module does not use source control to revert 
or mandate committed sources. Instead, when :mod:`main` is used, this runs as a 
subprocess launched by :mod:`main`. As a subprocess, :mod:`main` takes care 
of reverting sources if necessary before launching this subprocess. This 
ensures that modules loaded by this process will be the correct version in 
memory.
        
AUTHORS:

- THOMAS MCTAVISH (2010-09-01): initial version
- MIKE VELLA (2011-02-11): modified def write_output routine to incorporate loading
    to a database.
- THOMAS MCTAVISH (2011-03-01): Fix so that when calling from command line it can
    be from python, nrngui, or nrniv.
"""
import sys, os, datetime, pickle
from neuronpy.util import paraminit, platforminfo
import util, simrun

# sim_var is a dict, which contains all of our simulation parameter
# values. We load the default parameters with the following import statement.
# These can be overriden by providing another parameter file on the
# command line that has a sim_var dict.
sim_var = {}

sim_info = {} # Dictionary, which will contain simulation info when the
              # simulation finishes.
prj_tmp = {}  # Global dictionary for project-specific variables. These are 
              # defined at runtime and are not stored.

def run(argv = None):
    """
    Run the program. This does the following:
        
        1. Determines the file path of this module (no matter where in the
           directory structure it was launched from) so that it can reference
           output directories.
        2. Processes the arguments.
        3. Runs the simulation.
        4. Writes the results.
    
    :param argv: List of strings, each of which are arguments that would be
        specified on the command line.
    """
    (project_path, path_to_src) = util.get_project_and_src_paths('simrunner')
    prj_tmp['prj_path'] = project_path
    prj_tmp['src_path'] = path_to_src

    try:
        _initialize(argv)
        run_sim() # Run the simulation
        # run_sim_hoc() # Run with hoc. If uncommented, comment out the line
                        # above.
        write_dicts()
    except Exception, e:
        raise

def _initialize(argv):
    """
    Load the ``sim_var`` dict and process arguments.
    
    :param argv: List of strings, each of which are arguments that would be
        specified on the command line.
    """
    local_dict = {}
    sim_var.clear()
    util.load_sim_var(sim_var)
    param_files, cmds = paraminit.parse_args(argv, globals(), local_dict)
    if 'sim_var' in local_dict:
        # Replace default values with those in the local_dict
        sim_var.update(local_dict['sim_var'])
    if 'prj_tmp' in local_dict:
        prj_tmp.update(local_dict['prj_tmp'])

    # Check that the ``prj_tmp`` and ``sim_var`` dicts are complete and fill in
    # anything missing that wasn't already accounted for.
    if not 'prj_path' in prj_tmp:
        (project_path, path_to_src) = util.get_project_and_src_paths()
        prj_tmp['prj_path'] = project_path
        prj_tmp['src_path'] = path_to_src

    if not 'sim_dir_id' in sim_var:
        util.set_sim_dir_id(prj_tmp, sim_var)
        
    prj_tmp['sim_out'] = os.path.join(prj_tmp['prj_path'], \
            sim_var['sim_path'], sim_var['sim_dir_id'])
    
def run_sim():
    """
    Run the simulation and write the output files. This calls 
    :func:`simrun.run` to actually perform the simulation. The results are then
    written to output files.
    """
    sim_info['start_time'] = datetime.datetime.utcnow()
    v_vec, t_vec = simrun.run(sim_var)
    sim_info['end_time'] = datetime.datetime.utcnow()
    sim_info['sim_time'] = sim_info['end_time'] - sim_info['start_time']
    write_output(v_vec, t_vec)

def run_sim_hoc():
    """
    Run a parameterized hoc model where parameters are defined by hoc globals.
    In this case, the keys of *sim_var* correlate to the hoc global variable
    names and if the value of those items in the dict are numbers or strings, 
    they replace any already-loaded hoc globals.
    
    .. Note::
        
        It is important that after 
        :func:`neuronpy.util.hoctranslate.dict_to_global` is called, that no 
        other hoc code reloads or modifies the global parameters.
    """
    from neuron import h
    from neuronpy.util import hoctranslate
    h.load_file("simrun.hoc")
    hoctranslate.dict_to_global(h, sim_var) # Load hoc globals from sim_var
    sim_info['start_time'] = datetime.datetime.utcnow()
    h.simrun(sim_var['tstop'])
    sim_info['end_time'] = datetime.datetime.utcnow()
    sim_info['sim_time'] = sim_info['end_time'] - sim_info['start_time']
    write_output(h.v_vec, h.t_vec)
    
def write_output(v_vec, t_vec):
    """
    Write out the hoc vectors by pickling them and also write a graphic file.
    
    .. note:: Many hoc objects cannot be pickled, including Vector objects.
        However, the data values can be pickled with the Vector's to_python()
        method. When unpickling from the file written here, the values can be
        restored to a Python list.::
    
            with open('/Path/to/v_vec.p') as vec_file:
                v_vec = pickle.load(vec_file)
    
        It is then possible to restore this to a hoc Vector as::
    
            hoc_v_vec = h.Vector(v_vec)
    """
    filepath = os.path.join(prj_tmp['sim_out'], 'v_vec.p')
    with open(filepath, 'w') as v_vec_file:
        try:
            pickle.dump(v_vec.to_python(), v_vec_file)
        except:
            pickle.dump(v_vec, v_vec_file)#may already be a python type
    filepath = os.path.join(prj_tmp['sim_out'], 't_vec.p')
    with open(filepath, 'w') as t_vec_file:
        try:
            pickle.dump(t_vec.to_python(), t_vec_file)
        except:
            pickle.dump(t_vec, t_vec_file)#may already be a python type
    # Write a graphic file.
    try:
        from matplotlib import pyplot
        fig = pyplot.figure()
        ax = fig.add_subplot(111)
        ax.plot(t_vec, v_vec)
        fig.suptitle(sim_var['title_str'])
        filepath = os.path.join(prj_tmp['sim_out'], sim_var['output_file'] + 
                                sim_var['graphic_format'])
        fig.savefig(filepath)
    except ImportError:
        pass # If on a non-graphical system, don't write a graphics file
    
def write_dicts():
    """
    Write the *sim_var* dict to the file *params.py* and include 
    instructions for how to execute the simulation again. Also describe
    the *sim_info* dict in *info.py*.
    """
    rel_out = os.path.join('..', sim_var['sim_path'], sim_var['sim_dir_id'], \
            'params.py')
    filepath = os.path.join(prj_tmp['sim_out'], 'params.py')
    with open(filepath, 'w') as param_file:
        param_file.write('# Parameters for simulation ' + \
                sim_var['sim_dir_id'] + '\n#\n')
        param_file.write('# This file has been auto-generated. \n#\n')
        param_file.write('# To re-run the simulation with these parameters, \
                \n')
        param_file.write('# execute the following from the command line: \n#\n')
        param_file.write('# python main.py ' + rel_out + '\n#\n')
        param_file.write('# This will duplicate these parameters and \n')
        param_file.write('# a new output directory, so it will not replace \n')
        param_file.write('# the output in this directory. \n#\n')
        param_file.write('# Alternatively, using the --replace flag\n')
        param_file.write('# will overwrite output:\n#\n')
        param_file.write('# python main.py --replace ' + rel_out + '\n#\n')
        param_file.write('# To use these parameters with the latest sources\n')
        param_file.write('# use the --tip directive:\n#\n')
        param_file.write('# python main.py --tip ' + rel_out + '\n#\n')
        param_file.write('# This will generate a new output directory, but\n')
        param_file.write('# the --replace directive can also be used with\n')
        param_file.write('# the --tip directive.\n#\n')
        
        # Since we are recording timestamps, we need to write an import
        # statement if we re-execute this file.
        param_file.write('import datetime\n')
        
        # Now, actually write the parameters used. We iterate so that we
        # can write each parameter on a separate line so that the file
        # is readable.
        param_file.write('sim_var = { \\\n')
        for (key, val) in sim_var.iteritems():
            param_file.write(repr(key) + ' : ' + repr(val) + ', \\\n')
        param_file.write('}\n')

    # Write the system and other simulation information
    sim_info.update(platforminfo.get_platform_info())
    filepath = os.path.join(prj_tmp['sim_out'], 'info.py')
    
    with open(filepath, 'w') as info_file:
        info_file.write('# System information for simulation ' + \
                sim_var['sim_dir_id'] + '\n#\n')
        info_file.write('# This file has been auto-generated. \n#\n')
        info_file.write('# Make a sim_info dict, \n\n')
        info_file.write('import datetime\n')
        info_file.write('sim_info = { \\\n')
        for (key, val) in sim_info.iteritems():
            info_file.write(repr(key) + ' : ' + repr(val) + ', \\\n')
        info_file.write('}\n')

if __name__ == "__main__":
    """
    Runs when called from the command line. Optional arguments may specify 
    different param files and Python commands.
    """
    idx=1
    for item in sys.argv:
        if item.endswith('simrunner.py'): # Ignore all args leading up to ourselves
            break
        idx += 1
    run(sys.argv[idx:])

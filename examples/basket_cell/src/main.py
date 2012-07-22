# -*- coding: utf-8 -*-
r"""
Program entry point for a NEURON project with source control. This implements
the following:

- Simulation parameters are stored in a *sim_var* \
  `dict <http://docs.python.org/library/stdtypes.html#typesmapping>`_, which \
  are defined in *params.py*. Other parameter files can be specified \
  and individual elements of the dict can be overridden on the command line.

- Simulation output is directed to a unique subfolder of the *sims* \
  directory. The parameters used in the simulation, instructions for \
  re-running the simulation, and system and platform information in the run \
  are also recorded. Specifically, parameters used in the simulation are \
  written to the dict *sim_var* in *params.py* and platform and simulation \
  info are written to the *sim_info* dict in *info.py*.

- Before running a simulation, there is a check that there are no uncommitted \
  changes to the source code.

- Re-running a simulation reverts to the source code used in the original \
  run, but this default behavior can be changed to run with the most recent \
  version of the code.

Command line format::
    
    python main.py [--<flag>] [<pythonfile>.py] [cmd]
    
where the optional arguments may appear in any order and where several Python
files and commands may be specified, but files and commands are processed in 
sequential order as they appear on the command line.
    
    - ``--tip``
        Flag when re-running a simulation to disregard the \
        original sources and use the most recent changeset.

    - ``--replace``
        Flag when re-running a simulation to not create a new output \
        directory, but replace files in the original output directory.

    - ``--without-hg``
        Flag to ignore Mercurial source control. This uses current sources and 
        does not write source control information with output, so simulations 
        with this flag cannot revert sources. This flag may be useful in
        making test runs during development without having to commit sources
        between trials.

    - ``<pythonfile>.py``
        A Python file to be executed with `Python's execfile \
        function <http://docs.python.org/library/functions.html#execfile>`_. \
        The most common use of this would be to specify a different parameter \
        file from *params.py*.
        
    - ``cmd``
        Any number of expressions (delimited with a space ``' '``) that can \
        be evaluated with `Python's exec function \
        <http://docs.python.org/reference/simple_stmts.html#exec>`_. It may \
        be important to surround each expression with double quotes. For \
        example, ``"expr1" "expr2"``.

    
EXAMPLES:
    
1. To launch with default behavior, and run the simulation, putting the \
   output in a new subfolder in the *sims* directory::
    
    $ python main.py

2. To override a variable of the *sim_var* dict, pass in a command::
    
    $ python main.py "sim_var['asyn_onset']=30"
    
3. To specify a completely different parameter file::

    $ python main.py ../sims/default_run/params.py
    
4. To re-run a simulation using the latest sources::
    
    $ python main.py --tip ../sims/some_previous_run/params.py
    
5. In situations where you are testing code and do not want to keep \
   committing changes as you are developing. Use the ``--without-hg`` and \
   also write simulation output to a temporary directory keeping these \
   results separate from the normal *sims* directory::
       
    $ python main.py --without-hg "sim_var['sim_path']='temp'"
    
6. Instead of running from the command line, this module can be imported and \
   arguments can be passed in a list of strings to the :func:`run` function:
    
   .. testcode::
    
      import main
      main.run(["../sims/asyn_gmax_2/params.py", "sim_var['asyn_onset']=30"])

.. note::
    
    This module largely provides source code management to :mod:`simrunner`.
    After sources are set to their appropriate versions, :mod:`simrunner` is
    launched as a subprocess with the proper values in *sim_var*, which, in 
    turn, runs the simulation and writes the simulation output files. 
    Launching as a subprocess simply ensures that the correct versions of our 
    modules are loaded. It also keeps the code in :mod:`main` small and 
    without the need for much modification, which is important because 
    **YOU CANNOT DYNAMICALLY REVERT LOADED MODULES!!!** Since :mod:`main` 
    is the program launched, it is loaded in memory, so while it cannot be 
    reverted, the rest of the files can.

AUTHORS:

- THOMAS MCTAVISH (2010-08-01): initial version
- Thomas McTavish (2011-01-27): Fix for subrepo
- THOMAS MCTAVISH (2011-03-01): Fix so that when calling from command line it can
    be from python, nrngui, or nrniv.
"""
__version__ = 0.1

import sys, subprocess, os
from neuronpy.util import hgutil, paraminit
import util

replace_output = False
use_tip = False
use_hg = True
prj_tmp = {} # Dict for runtime variables.
sim_var = {} # Dict of simulation parameters

def run(argv = None):
    """
    Run main program. This does the following:
        
        1. Determines the file path of this module (no matter where in the
           directory structure it was launched from) so that it can reference
           output directories.
        2. Checks that all source code has been committed.
        3. Processes the arguments.
        4. Runs the simulation in a subprocess, which writes the results.
        5. If an error was encountered, it reverts to the last committed 
           changeset.

    :param argv: List of strings, each of which are arguments that would be
        specified on the command line.
    """
    global replace_output, use_tip, use_hg

    filtered_args = _preprocess_args(argv)
    
    (project_path, path_to_src) = util.get_project_and_src_paths()
    prj_tmp['prj_path'] = project_path
    prj_tmp['src_path'] = path_to_src

    if use_hg:
        hg_obj = hgutil.HGUtil(os.path.join(project_path, path_to_src)) 
        try:
            hg_obj.check_status() # Check that we have committed all changes.
        except Exception as _ex:
            print _ex
            return # If there is any error just return.
    else:
        hg_obj = None
        
    try:
        _initialize(hg_obj, filtered_args)
        # We may have just reverted sources, so we launch simrunner as a
        # subprocess, using the sim_var dict we have just assembled. This
        # ensures that modules imported by simrunner will be the correct
        # revision.
        exec_file = os.path.join(project_path, path_to_src, 'simrunner.py')
        child = subprocess.Popen(['python', exec_file, 'sim_var='+str(sim_var)])
        child.wait()
        if hg_obj:
            hg_obj.revert_to_changeset()
    except:
        if hg_obj:
            hg_obj.revert_to_changeset() # Revert to the last changeset

def _preprocess_args(in_argv):
    """
    Look for the flags, ``--replace``, ``--tip``, and ``without-hg`` and set
    the global parameters accordingly. Strip out these flags and return the
    remaining arguments.
    """
    global replace_output, use_tip, use_hg
    argv = []
    if in_argv is not None:
        for arg in in_argv:
            if arg.startswith('--'):
                if arg == '--replace':
                    replace_output = True
                elif arg == '--tip':
                    use_tip = True
                elif arg == '--without-hg':
                    use_hg = False
                else:
                    print "Unrecognized and ignored command", arg
            else:
                argv.append(arg)
    return argv 
    
def _initialize(hg_obj = None, argv=None, ):
    """
    Initialize the simulation parameters, setting ``sim_var`` and reverting
    sources, if necessary. The simulation output directory is also set.
    
    :param hg_obj: :class:`neuronpy.util.hgutil` object to retrieve source
        control information from.
        
    :param argv: List of strings, which correlate to the optional commands
        that would be listed on the command line when launching the program.
    """
    global replace_output, use_tip, use_hg
    sim_var.clear() # In case non-empty
    util.load_sim_var(sim_var) # Load from params.py

    # Process args, loading them into local_dict.
    local_dict = {}
    param_files, cmds = paraminit.parse_args(argv, globals(), local_dict)
    if 'sim_var' in local_dict:
        # Replace default values with those in the local_dict
        sim_var.update(local_dict['sim_var'])

    if use_hg:
        if use_tip == False and 'hg' in sim_var:
            # Note that while this will revert sources, any already code loaded
            # into program memory will leave the revert inconsequential.
            hg_obj.revert_to_changeset(str(sim_var['hg']['node']))
        else:
            sim_var['hg'] = hg_obj.get_changeset_dict()

    if replace_output is False:
        util.set_sim_dir_id(prj_tmp, sim_var)
        
if __name__ == '__main__':
    """
    Runs when called from the command line. Optional arguments may specify 
    different param files and Python commands.
    """
    idx=1
    for item in sys.argv:
        if item.endswith('main.py'): # Ignore all args leading up to ourselves
            break
        idx += 1
    run(sys.argv[idx:])
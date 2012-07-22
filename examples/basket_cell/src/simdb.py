# -*- coding: utf-8 -*-
r"""
Build a database of simulation data for use with :mod:`neuronpy.util.dictdb`.

EXAMPLES:
    
Find those simulations where ``asyn_onset`` is greater or equal to ``20``.

::
    
    from neuronpy.util import dictdb
    import simdb
        
    db = simdb.build_database()[0] # builds the database, using sims folder.
    sub_sims = dict(dictdb.filter_dict(db, \
            lambda k, v, p: k == 'asyn_onset' and v >=20))
    for some_dir in sub_sims.iterkeys():
        # Analyze an output file in some_dir
        print "Matching sim = ", some_dir
        

Let us say a bug was introduced in rev 2, and we need to delete all of
those simulations greater than that revision. (Mac/Unix example):
    
::
    
    import os
    from neuronpy.util import dictdb
    import simdb
    
    db, simdir = simdb.build_database() # builds the database
    sub_sims = dict(dictdb.filter_dict(db, \
            lambda k, v, p: \
                k == 'rev' and \
                len(p) >= 3 and p[-2] == 'hg' and p[-3] == 'sim_var' and \
                v >=2))
    for some_dir in sub_sims.iterkeys():
        filepath = os.path.join(simdir, some_dir)
        exec_str = 'rm -r -f ' + filepath
        os.system(exec_str)
    
.. Warning::
    
    The above code example is a very lethal example. You may want to ensure
    that ONLY those directories you wish to delete will be deleted!

AUTHORS:

- THOMAS MCTAVISH (2010-08-01): initial version
"""
__version__ = 0.1
import os, imp
import util
    
def build_database(simdir=None):
    """
    Iterate through the folder where simulations are and for each 
    directory, execute each python file found, adding the results to the
    *db* dict.

    :param simdir: The main simulation output directory, which holds the
        directories of each simulation. If :keyword:None, then it will be
        assumed to be the *sims* directory under the project root.
    
    :return (db, simdir): ``db`` is the dict where the keys are the name of the 
        simulation folders that contain the various runs' output files. The 
        values of the dict are sub-dictionaries written to Python *'.py'* files 
        in those folders. ``simdir`` is the directory (either full path or 
        relative to *simdb.py*.
    """
    db = {}
    if simdir is None:
        (project_path, path_to_src) = util.get_project_and_src_paths('simdb')
        simdir = os.path.join(project_path,'sims')
    
    for (dirpath, dirnames, filenames) in os.walk(simdir):
        parent_dir = dirpath.rsplit('/')[-1] # Get the tail of the path
        for the_file in filenames:
            if the_file.endswith('.py'):
                local_dict = {}
                execfile(os.path.join(dirpath, the_file), globals(), \
                        local_dict)
                if not parent_dir in db:
                    db[parent_dir] = {}
                db[parent_dir].update(local_dict)
    
    return db, simdir
        

    

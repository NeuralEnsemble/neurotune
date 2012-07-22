# -*- coding: utf-8 -*-
"""
Utility methods for the various modules of the project to share. 

AUTHORS:

- THOMAS MCTAVISH (2010-09-01): initial version
- Thomas McTavish (2011-01-27): Removed uuid of sim directory ids and made them incremenal
        numbers.
"""
import os, imp

def get_project_and_src_paths(module_name='main'):
    """
    Get the absolute path to the project and the relative path to the source
    directory from the project path where ``module_name`` is located, which 
    assumes it is one level down from the project.
    
    :return: (project_path, path_to_src)
    """
    try:
        (file, pathname, description) = imp.find_module(module_name)
    except ImportError as _ex:
        print "Cannot find the path to the %s module!" % module_name
        raise _ex
    return os.path.split(os.path.dirname(os.path.abspath(pathname)))
    
def load_sim_var(sim_var):
    """
    Update ``sim_var`` with the dict values in ``params.py``. Any
    non-overlapping keys with those defined in ``params.py`` will
    remain.
    """
    sim_var.update(__import__('params', globals(), locals(), \
            ['sim_var'], -1).sim_var)

def _no_hidden(item): return item[0] != '.'
def _no_text(item):
    try:
        int(item)
    except:
        return False
    return True

def set_sim_dir_id(prj_tmp, sim_var):
    """
    Sets the output directory id, accessible as ``sim_var['sim_dir_id']``. This increments
    a value.
    
    Assumes values for ``prj_tmp['prj_path']`` and ``sim_var['sim_path']``
    have already  been made. If they have not, then a :py:class:`NameError`
    or :py:class:`KeyError` will be thrown.
    """
    dirid = 0
    sim_dir = os.path.join(prj_tmp['prj_path'], sim_var['sim_path'])
    if not os.path.isdir(sim_dir):
        os.mkdir(sim_dir)
    else:
        # Get directories
        dirlist = [ name for name in os.listdir(sim_dir) \
                if os.path.isdir(os.path.join(sim_dir, name)) ]
        
        # Remove hidden
        dirlist = filter(_no_hidden, dirlist)
        
        # Remove non-integer dirs, like 'default_run'
        dirlist = filter(_no_text, dirlist)
        
        if len(dirlist) > 0:
            # Convert to ints
            dirlist = map(int, dirlist)
            
            dirlist.sort()
            dirid = dirlist[-1] + 1
            
    sim_dir = os.path.join(prj_tmp['prj_path'], sim_var['sim_path'], \
            str(dirid))
    os.mkdir(sim_dir)
    sim_var['sim_dir_id'] = str(dirid)
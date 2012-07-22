# -*- coding: utf-8 -*-
"""
Builds the preliminary files necessary for the documentation of the source 
files from the comments in the code.

To use, add or remove the list of source files to be documented in the 
*modules* list. Then, from the command line.::
    
    $ python refbuilder.py

This will create the necessary *'.rst'* files in the *../doc/source/*
directory. Make sure the *../doc/source/index.rst* file contains a reference
to ``api`` either as::
    
    .. include:: api.rst

or in the table of contents.::
    
    .. toctree::
    
        api

Assuming that a Sphinx makefile exists in the *../doc/* directory from 
running ``sphinx-quickstart``, then executing ``make html`` or ``make latex``
should compile the documentation.

AUTHORS:

- THOMAS MCTAVISH (2010-08-01): initial version
"""
__version__ = 0.1
import os

import util

(project_path, path_to_src) = util.get_project_and_src_paths('refbuilder')

# Set the directory where .rst files will go.
build_path=os.path.join(project_path, 'doc', 'source')

# Files to include in the API.
modules = ['main', 'simrunner', 'simrun', 'simdb', 'sqldbutils', 'fig1', \
        'refbuilder', 'util']

# Write the api.rst file
filepath = os.path.join(build_path, 'api.rst')
with open(filepath, 'w') as api_file:
    api_file.write('.. _api:\n\n')
    api_file.write('################\n')
    api_file.write('Source Reference\n')
    api_file.write('################\n')
    api_file.write('.. index::\n')
    api_file.write('   single: Source Reference\n\n')
    api_file.write('This is the reference documentation for the source code ')
    api_file.write('of the nrnproject.\n\n')
    api_file.write('.. toctree::\n\n')
    for modulename in modules:
        api_file.write('   ' + modulename + '\n')
    
# Write the other files to include in the API.
for modulename in modules:
    try:
        filepath = os.path.join(build_path, modulename + '.rst')
        fout=open(filepath, 'w')
        fout.write(modulename+'\n')
        for i in range(len(modulename)):
            fout.write('-')
        fout.write('\n\n')
        fout.write('.. This file has been automatically generated ')
        fout.write('by refbuilder.py\n\n')
        fout.write('.. automodule :: %s\n' % (modulename))
        fout.write('   :members:\n\n')
    except:
        print "could not generate doc for {0}".format(modulename)
        fout.close()
        pass
    fout.close()

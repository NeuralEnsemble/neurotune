#c -*- coding: utf-8 -*-
"""
Default parameters for nrnproject.

AUTHORS:

- THOMAS MCTAVISH (2010-08-01): initial version
- MIKE VELLA (2011-02-11): Added functionality to allow storing to database and some controls over the database storage(nth_timestep_sample parameter, store_traces to db flag)
"""

# SIMULATION PARAMETERS
sim_var = { \
'tstop' : 50.,  # Duration of simulation \
'asyn_onset' : 30,  # Delay of the alpha synapse \
'asyn_gmax' : 1,  # Maximal conductance of the synapse \

# OUTPUT PARAMETERS
'sim_path' : 'sims', # Main simulation output directory path relative to \
        # project path. Individual simulations go in subdirectories of here. \
'output_file' : 'plot', # Name of the graphic file without the extension \
'graphic_format' : '.png', # May be '.jpg', '.gif', '.pdf' \
'title_str' : 'Hello World!', # Graphic title
'dbname' : 'output.sqlite', #name of database to output to \
'simulation_name':'example simulation to demonstrate sqldbutils extension to nrnproject',
'morphology':'test morphology',
'author':'Mike Vella',
'dbpath' : 'sims', #local path to the database
'nth_timestep_sample' : 2, # every nth timestep to sample, sample density is therefore = 1/nth_timestep_sample

#MECHANISM DENSITIES:
'axon_gbar_na':4998.124,
'soma_gbar_na':52.241,

'soma_gbar_kv':3.543,
'axon_gbar_kv':6.222,

'soma_gbar_kv3':0.213,
'axon_gbar_kv3':0.112,

#DATABASE PARAMETERS
'database_type':'sqlite' #currently only option, next to be supported will be mongodb
}

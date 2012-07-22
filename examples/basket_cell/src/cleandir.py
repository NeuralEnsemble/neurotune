import os, datetime
from neuronpy.util import dictdb
import simdb

import main

main.run()
main.run(["sim_var['asyn_gmax']=2"])
main.run(["sim_var['asyn_gmax']=2", "sim_var['asyn_onset']=30"])
main.run(["sim_var['asyn_onset']=30"])

import fig1

fig1.run()

db, simdir = simdb.build_database() # Build the database
sub_sims = dict(dictdb.filter_dict(db, lambda k, v, p: \
        k == 'end_time' and \
        len(p) >= 2 and p[-2] == 'sim_info' and \
        (datetime.datetime.now() - v).days <= 1))

for some_dir in sub_sims.iterkeys():
    filepath = os.path.join(simdir, some_dir)
    exec_str = 'rm -r -f ' + filepath
    os.system(exec_str)
# -*- coding: utf-8 -*-
"""
Run a simulation utilizing parameters from a Python dictionary.

AUTHORS:

- THOMAS MCTAVISH (2010-08-01): initial version
- MIKE VELLA (2011-02-11): modified the run routine to include an example of returning output_values which are calculated for each simulation and stored in the database
"""
__version__ = 0.1
from neuron import h

def run(sim_var):
    """
    Simulation of Basket cell
    """

    from neuron import h
    from nrndev import nrntools

    #make compartments and connect them
    soma=h.Section()
    axon=h.Section()
    soma.connect(axon)

    axon.insert('na')
    axon.insert('kv')
    axon.insert('kv_3')
    soma.insert('na')
    soma.insert('kv')
    soma.insert('kv_3')

    soma.diam=10
    soma.L=10
    axon.diam=2
    axon.L=100

    #soma.insert('canrgc')
    #soma.insert('cad2')

    #nrntools.set_section_mechanism(sec,'kv','gbar',gkv_dend)

    nrntools.set_section_mechanism(axon,'na','gbar',sim_var['axon_gbar_na'])
    nrntools.set_section_mechanism(axon,'kv','gbar',sim_var['axon_gbar_kv'])
    nrntools.set_section_mechanism(axon,'kv_3','gbar',sim_var['axon_gbar_kv3'])
    nrntools.set_section_mechanism(soma,'na','gbar',sim_var['soma_gbar_na'])
    nrntools.set_section_mechanism(soma,'kv','gbar',sim_var['soma_gbar_kv'])
    nrntools.set_section_mechanism(soma,'kv_3','gbar',sim_var['soma_gbar_kv3'])

    for sec in h.allsec():
        sec.insert('pas')
        sec.Ra=300
        sec.cm=0.75
        nrntools.set_section_mechanism(sec,'pas','g',1.0/30000)
        nrntools.set_section_mechanism(sec,'pas','e',-70)

    h.vshift_na=-5.0
    sim=nrntools.Simulation(soma,sim_time=1000,v_init=-70.0)
    sim.set_IClamp(150, 0.1, 750)
    sim.go()

#    sim.show()

    #Example of recording data to the database:
    
    import db

    writer=db.db_writer.get_db_writer(sim_var) #create writer object
    #write all recordings, label appropriately:
    writer.write_timeseries(sim.rec_t,sim.rec_v,label='voltage_mV') 

    #record what input parameters were in the db:
    writer.write_sim_var() 

    #write results of a calculation - this is a trivial example
    writer.write('example value',3) 
    writer.write('example value_2','can also be a string')

    return sim.rec_v,sim.rec_t

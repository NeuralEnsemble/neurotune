# -*- coding: utf-8 -*-
"""
API for different database systems for use with nrnproject

This API is still in the beta stage. Its main function is to implement
writer and reader classes for datbase systems storing data with nrnproject.

The db_loader and db_writer classes follow the basic factory design pattern,
based on the database_type option specified in params.py (example mongoddb 
or sqlite it provides the correct subclass).

AUTHORS:

- MIKE VELLA (2011-09-6): initial version
  mv333@cam.ac.uk
""" 

import sqldbutils
import util

class db_loader(object):#using the factory pattern

    @staticmethod
    def get_db_loader(db_path,database_type,experiment_id):
        loader_name=database_type+'_loader'
        return globals()[loader_name](db_path,experiment_id)

    def get(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def get_timeseries(self):
        raise NotImplementedError("Subclass must implement abstract method")

class db_writer(object):#using the factory pattern

    @staticmethod
    def get_db_writer(sim_var):
        database_type=sim_var['database_type']
        writer_name=database_type+'_writer'
        return globals()[writer_name](sim_var)

    def write(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def write_timeseries(self):
        raise NotImplementedError("Subclass must implement abstract method")

class sqlite_loader(db_loader):

    def __init__(self,db_path,experiment_id):
        self.db_path=db_path
        self.experiment_id=experiment_id

    def get(self,param):
        """
        Get a value from sqlite database.

        There can be only one experiment id per loader. Returns an array 
        containing time-dependent data or a single value. User does not 
        need to worry which table the data is stored in, i.e whether it 
        is of the sim_var, output_data etc.. types.
        """

        try:
            self.data=sqldbutils.sim_data(self.db_path,self.experiment_id,param) #try and get the time-correlated samples for that param
            var=self.data.samples #first try and load time-varying data if it exists
            if len(var)>0:
                variable=var
        except:
            pass

        connection=sqldbutils.db_connect(self.db_path)
        #try and get it from output_params table using SQL query:
        try:
            query='SELECT numerical_value FROM output_params WHERE parameter=\''+param+'\' AND experiment_id ='+str(self.experiment_id)
            numerical_value=sqldbutils.execute_query(connection,query).fetchall()[0][0]
            if type(numerical_value)!=None:
                variable=numerical_value
        except:
            pass

        try:
            query='SELECT string_value FROM output_params WHERE parameter=\''+param+'\' AND experiment_id ='+str(self.experiment_id)
            string_value=sqldbutils.execute_query(connection,query).fetchall()[0][0]
            if type(string_value)!=None:
                variable=string_value
        except:
            pass

        #try and get it from sim_var table using SQL query:

        try:
            query='SELECT numerical_value FROM sim_var WHERE parameter=\''+param+'\' AND experiment_id ='+str(self.experiment_id)
            numerical_value=sqldbutils.execute_query(connection,query).fetchall()[0][0]
            if type(numerical_value)!=None:
                variable=numerical_value
        except:
            pass

        try:
            query='SELECT string_value FROM sim_var WHERE parameter=\''+param+'\' AND experiment_id ='+str(self.experiment_id)
            string_value=sqldbutils.execute_query(connection,query).fetchall()[0][0]
            if type(string_value)!=None:
                variable=string_value
        except:
            pass

        try:        
            return variable #will either return a single value or time-varying (array)
        except:
            print 'Parameter not found in database'
        
    def get_timeseries(self,param):
        """
        Get a time vector corresponding to a value

        Returns an array containing time-vector of a related value, typically
        this will be a voltage recording.
        """ 

        try: #first try and get  
            data=sqldbutils.sim_data(self.db_path,experiment_id=self.experiment_id,param=param)
            return data.t
        except:
            print 'no such data'

        
    def write_spike_events(self):
        pass #not yet implemeneted as I don't know anything about this in NEURON

    def get_spike_events(self):
        pass #not yet implemeneted as I don't know anything about this in NEURON


class sqlite_writer(db_writer):

    """
    Write to sqlite database

    Allows writing of time-varying data, sim_var dict and
    single name-value pairs to sqlite database.
    """ 

    def __init__(self,sim_var):
        
        self.loader=sqldbutils.db_loader(sim_var)

    def write_timeseries(self,times,values,label='voltage_mV'):

        #load data to database:
        self.loader.load_samples(label,times,values)
    
    def write_sim_var(self):

        self.loader.load_params()

    def write(self,key,value,label='voltage_mV'):

        self.loader.load_output_params(key, value)

class mongodb_loader(db_loader):

    def __init__(self):
        print 'in mongodb loader'

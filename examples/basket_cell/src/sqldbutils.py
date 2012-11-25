# -*- coding: utf-8 -*-
"""

Library to allow output of nrnproject simulations to be stored in an
sqlite database.

.. note::
	For more information on sqlite see http://www.sqlite.org/quickstart.html

The main use of this library is to implement two classes: :class:`db_loader` which
allows loading of simulation data into an sqlite database and :class:`sim_data`
which allows retrieving the simulation data from a database into a :class:`sim_data`
object.

The :class:`db_loader` object creates 4 tables (if they do not already exist) which
compromise the structure of the nrnrproject-sqlite database:

    1. *simulations*:
        Each new simulation is assigned a row entry in the sqlite
        the ID of each simulation serves as a foreign key for all other rows
    
    2. *sim_var*:
        The sim_var dictionary in default_params.py or a
        user-supplied sim_var dictionary is recorded in this table
    
    3. *sample table*:
        load_samples method of the db_loader object loads the 
        time, sample pair into a row on the samples_table. The user must specify
        by means of a string what type of variable is being recorded 
        (eg voltage). The nth_timestep_sample paramater specifies the "density"
        of recording, if set to 1 each sample is recorded, if set to 3 each 3rd
        sample is recorded etc.
    
    4. *output_params*:
        This is where user can store results of a calculation
        performed mid-simulation or after the simulation has finished running.
        example includes mean-spike frequency, coefficient of variation of
        interspike times etc.

.. Note::
    
    1. Location of database is specified in *params.py*, default is 
       ``[working_directory]/sims``.
    
    2. For viewing sqlite data graphically, SQLite Manager firefox extension is 
       recommended: https://addons.mozilla.org/en-US/firefox/addon/5817/

AUTHORS:

- MIKE VELLA (2011-01-12): initial version
- MIKE VELLA (2011-02-18): improved documentation
  mv333@cam.ac.uk
""" 
 
import sqlite3
import util
import os
import operator
import csv

__version__=0.3
 
class db_loader():
    """
    Loader for data into a SQLITE database in nrnproject-compliant format
    
	1. Connects-to or creates the database if it doesn't exist.
        
	2. Creates simulations table if it doesn't already exist
            
	3. Inserts a unique entry for the simulation into simulations table
            
	4. Logs the experiment ID in the loader
            
	.. note::    
		One db_loader instance should correspond to one simulation - hence\
    	only one experiment-id can exist per loader object

	"""
 
    def __init__(self,sim_var):


        self.sim_var=sim_var
       
        (project_path, path_to_src) = util.get_project_and_src_paths()
        self.project_path=project_path
        self.path_to_src=path_to_src
       
        dbpath=os.path.join(self.project_path,sim_var['sim_path'], sim_var['dbname'])
        
        self.conn=db_connect(dbpath) #connection object
        self.c = self.conn.cursor()
    
        # Create a simulations table
        create_sims_table='create table simulations \
        (id INTEGER PRIMARY KEY, simulation_name TEXT,morphology TEXT\
        ,author TEXT);'
        execute_query(self.conn,create_sims_table)
        
        #To do:generate an error if exp_id already exists on the database
        if 'exp_id' in sim_var: #Need a check to ensure key is unique! (WIP)
            simulation_string='''INSERT INTO simulations(id,\
            simulation_name, morphology,author) values (?,?,?,?);'''
            values=[sim_var['exp_id'],sim_var['simulation_name'],sim_var['morphology'],\
			sim_var['author']]
        else:
            simulation_string='''INSERT INTO simulations(simulation_name, \
            morphology,author) values (?,?,?);'''
            values=[sim_var['simulation_name'],sim_var['morphology'],\
			sim_var['author']]
        
        execute_query(self.conn,simulation_string,values)
        
        exp_id_cursor=execute_query(self.conn,'SELECT last_insert_rowid();')
        self.experiment_id=exp_id_cursor.fetchone()[0]

        self.conn.commit()
    
    def load_samples (self, param, t_vec, y_vec):
        """
        Loads samples from vectors or arrays into the database 
        
        1. Creates table named 'samples' if it doesn't exist
        2. Sequentially loads the sample value, it's time and parameter\
        into table named 'samples'
 		
        .. note::      
            t_vec and y_vec must be 1Xn lists with the same n value.
    
        :param param: the parameter being recorded - typical example is voltage
        :param t_vec: the vector/array containing the times of samples
        :param y_vec: the samples (e.g voltage measurements)
        """

        execute_query(self.conn,'''create table samples (id INTEGER PRIMARY \
        KEY,time_ms REAL,param TEXT,param_value REAL,experiment_id, \
        FOREIGN KEY(experiment_id) REFERENCES simulations(id));''')
        
        
        try:
            num_entries = int(y_vec.size())
        except:
            import numpy as np
            num_entries = int(np.size(y_vec))

        nth_sample=self.sim_var['nth_timestep_sample']
        n=nth_sample
        for i in range (0,num_entries):
            if n==nth_sample:
                value_list=[t_vec[i],y_vec[i],param,self.experiment_id]
                execute_query(self.conn,'''insert into samples(time_ms, \
                param_value,param,experiment_id) values(?,?,?,?);''',value_list)
                n=1
            else:
                n+=1

        self.conn.commit()

    def load_params (self):
        """
        Loads keys and values of sim_var into the sim_var table  
        
            1. Creates table named 'sim_var' if it doesn't exist
        
            2. Sequentially loads the key name and value into table
               rows.
        """
        query='''create table sim_var (id INTEGER PRIMARY KEY,\
        parameter TEXT, string_value TEXT, numerical_value REAL,experiment_id\
        , FOREIGN KEY(experiment_id) REFERENCES simulations(id));'''
        
        execute_query(self.conn,query)
        
        paramaters=self.sim_var

        for param,value in paramaters.iteritems():
            
            value_list=[param,value,self.experiment_id]

            if isinstance(value, str):
                execute_query(self.conn,'''insert into sim_var(parameter,\
                string_value,experiment_id) values(?,?,?);''',value_list)
            
            if isinstance(value, int) or isinstance(value,float):
                execute_query(self.conn,'''insert into sim_var(parameter,\
                numerical_value,experiment_id) values(?,?,?);''',value_list)
        
        self.conn.commit()
    
    def load_output_params (self,param_name,value):
        """
        Load outputs of calculations mid-simulation to the database. 
        
            1. Creates table named 'output_params' if it doesn't exist
        
            2. Sequentially loads the param_name and value into the
               output_params table
        
        NOTE: This method allows the user to load outputs of calculations
        mid-simulation to the database, they can be later used for more
        effective searching through the database of a large number of
        simulations
        
        :param param_name: post-analysis recorded param, e.g mean spike-width
        :param value: The value corresponding to the parameter being recorded
        """
        execute_query(self.conn,'''create table output_params \
        (id INTEGER PRIMARY KEY,parameter TEXT, numerical_value REAL,\
        experiment_id, FOREIGN KEY(experiment_id) REFERENCES \
        simulations(id));''')
        
        value_list=[param_name,value,self.experiment_id]
        execute_query(self.conn,'''insert into output_params(parameter,\
        numerical_value,experiment_id) values(?,?,?);''',value_list)
            
        self.conn.commit()

class sim_data():
    """
    Loads data from an nrnproject-sqlte database.
    
    The class takes experiment_id and param arguments. By default the param
    is voltage_mV. The relevant data is then loaded into the sim_data object.
    For example, to load voltage,time and output_params and sim_var for a
    simulation with experiment id 3 located at
    [sim_directory]/outputdb.sqlite::

        >>>experiment_3_data=sim_data([sim_directory]/outputdb.sqlite,3)
        >>>v=experiment_3.samples
        >>>t=experiment_3.t
        >>>sim_var=experiment_3.sim_var
        >>>output_params=experiment_3.output_params

    The idea is that once they are loaded from the database these lists and dicts
    are identical as to how they were before they went in, 
    hence methods which operate on the data before it enters the database
    can operate on it once they have been retrieved from the database.
    """
    def __init__(self,dbpath,experiment_id=1,param='voltage_mV'):
    
        self.conn=db_connect(dbpath)
    
        self.dbpath=dbpath
        self.experiment_id=experiment_id
        self.param=param
        
        
        self.sim_var=self.load_sim_var()
        self.t=self.load_time_vector()
        self.samples=self.load_samples_vector()
        self.output_params=self.load_output_params()
        
        #get the sim_var data - still to do
    
    def load_sim_var(self):

        load_sim_var_query='SELECT parameter,string_value,numerical_value\
         FROM sim_var WHERE experiment_id='+str(self.experiment_id)
        
        sim_var=execute_query(self.conn,load_sim_var_query)
        sim_var=sim_var.fetchall()
        
        keys=[]
        values=[]
        for i in sim_var:
            
            key=i[0].encode('ascii','ignore')
            keys.append(key)
            
            if i[1]!=None:
                value=i[1].encode('ascii','ignore')
                values.append(value)
            else:
                if i[2]!=None:
                    values.append(i[2])
            
        sim_var=dict(zip(keys, values))
        
        return sim_var

    def load_time_vector(self):
        
        load_time_query='SELECT time_ms FROM samples WHERE experiment_id='+\
        str(self.experiment_id) + ' AND param=\''+self.param+'\''
        
        cursor=execute_query(self.conn,load_time_query)
        time_vector=cursor.fetchall()
        time_vector=map(operator.itemgetter(0), time_vector)
    
        return time_vector
        
    
    def load_samples_vector(self):
        
        load_samples_query='SELECT param_value FROM samples WHERE\
         experiment_id='+str(self.experiment_id) + ' AND param=\''\
        +self.param+'\''
        
        cursor=execute_query(self.conn,load_samples_query)
        samples=cursor.fetchall()
        samples=map(operator.itemgetter(0), samples)
        
        return samples

    def load_output_params(self):
        
        load_output_params_query='SELECT parameter,numerical_value FROM\
         output_params WHERE experiment_id='+str(self.experiment_id)
        cursor=execute_query(self.conn,load_output_params_query)
        output_params_unicode=cursor.fetchall()

        #convert unicode to ascii:    
        output_params=[]
        for i in enumerate(output_params_unicode):
            unicode_tuple = output_params_unicode[i[0]]
            ascii_tuple = (unicode_tuple[0].encode('ascii','ignore'),unicode_tuple[1])
            output_params.append(ascii_tuple)
        
        return output_params

    def tocsv(self,csvpath,csvname=None):
        """
        Load the samples vs time data of an simulation to a csv file.

        :param csvname: name of csvfile not including extension if\
            no name is given will default to experiment id.
        :param csvpath: path where csvfile is to be saved to
        """
        csvpath

        if csvname==None:
            csvname=str(self.experiment_id)+'.csv'

        csvfile=csvpath+csvname

        t_samples_tuples=zip(self.t,self.samples)

        writer = csv.writer(open(csvfile, "wb"))

        print 'writing csvfile to: ' + csvfile

        writer.writerows(t_samples_tuples)

def execute_query(connection,query,values=0):
    """
    Execute arbitrary SQL query.
        
        1. Determines the file path of this module (no matter where in the
           directory structure it was launched from) so that it can 
           reference output directories.
        
        2. A cursor containing the result of the query is returned or an
           integer 0 if an error occurs.
                
    :param connection: an sqlite3 connection object (see db_connect method)
    :param query: a string containing an SQL Query, can contain placeholders
    :param values: list of values for the SQL Query placeholders
    """
    if values==0:
        try:
            cursor=connection.execute(query)
            return cursor
        except sqlite3.OperationalError:
            return 0 
    if values!=0:
        try:
            cursor=connection.execute(query,values)
            return cursor
        except sqlite3.OperationalError:
            return 0 

def db_connect(dbpath):
    """
    Connects to a SQLITE database and returns a connection object. 
        
        1. Determines the location of the database
        
        2. Makes a connection and returns it
                
    :param dbpath: path to the database
    """
    dbdir=dbpath[:dbpath.rfind('/')]
    if not os.path.exists(dbdir):
        os.makedirs(dbdir)

    conn=sqlite3.connect(dbpath)
    return conn

def exp_ids(dbpath):
    """
    Returns a list of all experiment_ids from an nrnproject-sqlite database.

    This can be useful when loading and/or analysing results of different
    simulations from a single database.

    :param dbpath: path to the database
    """
    conn=db_connect(dbpath)
    query='SELECT id FROM simulations;'
    cursor=execute_query(conn,query)

    print "test - is this stage long or always brief?"

    try:
        exp_ids_tuples=cursor.fetchall()
        exp_ids=[]
        for i in exp_ids_tuples: #there may be a more efficient way to do this.
            exp_id=i[0]
            exp_ids.append(exp_id)
    except:
        exp_ids=[0]

    try:
        print exp_ids_tuples
    except:
        print 'first exp_id_tuples'
    print "test ended"
    
    return exp_ids
   
def generate_exp_ids(dbpath):
    """
    Returns an integer which is one higher than the highest exp_id.

    This can be used if you want to know the experiment id of the simulation
    you are about to run (eg when saving to multiple databases on a cluster).

    :param dbpath: path to the database
    """
    exp_id_list=exp_ids(dbpath)
    max_exp_id=max(exp_id_list)
    generated_exp_id=max_exp_id+1
    return generated_exp_id

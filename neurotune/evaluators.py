import os
import sys
from threading import Thread
from pyelectro import analysis
import numpy

class __CandidateData(object):
    """Container for information about a candidate (chromosome)"""
    
    def __init__(self,chromosome):
        self.chromosome=chromosome
    
    def set_dbpath(self,dbpath):
        self.dbpath=dbpath
        
    def set_exp_id(self,exp_id):
        self.exp_id=exp_id
    
    def set_job_num(self,job_num):
        self.job_num=job_num


class __Evaluator(object):
    """Base class for Evaluators"""
    
    def __init__(self,parameters,weights,targets,controller):

        self.parameters=parameters
        self.weights=weights
        self.targets=targets
        self.controller=controller
            

class __CondorContext(object):
    """manager for dealing with a condor-based grid"""
        
    def __split_list(self,alist, wanted_parts=1):
        
        length = len(alist)
        return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
                 for i in range(wanted_parts) ]
    
    def __prepare_candidates(self,candidates,candidates_per_job=1):
        
        #Split candidate list into smaller ones (jobs):
        #and make a job list
        if optimizer_params.candidates_in_job != None:
            candidates_in_job=optimizer_params.candidates_in_job
        else:
            candidates_in_job=candidates_per_job

        num_candidates=len(candidates)
        ids=range(num_candidates)
        enumerated_candidates=zip(candidates,ids)
        num_jobs=num_candidates/candidates_in_job
        self.num_jobs=num_jobs
        self.job_list=self.__split_list(enumerated_candidates,wanted_parts=self.num_jobs)
    
    def __make_job_file(self,job,job_number):
        #write the header:
        filepath = os.path.join(self.tmpdir, 'run' + str(job_number) + '.sh')
        run_shell = open(filepath, 'w')
        run_shell.write('#!/bin/bash\n')
        run_shell.write('reldir=`dirname $0`\n')
        run_shell.write('cd $reldir\n')
        run_shell.write('directory=`pwd`\n')
        run_shell.write('pndirectory=$directory\n')
        run_shell.write('#Untar the file:\n')
        run_shell.write('/bin/tar xzf ./portable-neuron.tar.gz\n')
        tarfile_name=optimizer_params.tarred_nrnproj
        run_shell.write('/bin/tar xzf ./'+tarfile_name+'\n')
        
        #CandidateData_list=[]
        for enumerated_candidate in job:
                
            chromosome = enumerated_candidate[0]
            candidate_info = CandidateData(chromosome)
            exp_id = enumerated_candidate[1]
            candidate_info.set_exp_id(exp_id)
            candidate_info.set_job_num(job_number)
            self.CandidateData_list.append(candidate_info)
                
            nproj = controllers.NrnProjSimRun(optimizer_params.project_path, chromosome)
            run_shell.write('#issue the commands\n')
            run_shell.write('$pndirectory/pnpython.sh \
                    $directory/src/simrunner.py "sim_var[\'exp_id\'] \
                    = ' + str(exp_id) + '\" ' + '"sim_var[\'''dbname''\'] \
                    = \'outputdb' + str(job_number) + '.sqlite\'"' + 
                    nproj.sim_var_string + '\n')
            run_shell.write('echo \'done\'\n')
        
        run_shell.write('cp $directory/sims/outputdb' + str(job_number) + '.sqlite $directory\n')
        #self.CandidateData_list=CandidateData_list
        run_shell.close()

    def __make_submit_file(self):
        #now we write the submit file
        filepath = os.path.join(self.tmpdir, 'submitfile.submit')
        submit_file=open(filepath,'w')
        
        submit_file.write('universe   = vanilla\n')
        submit_file.write('log        = pneuron.log\n')
        submit_file.write('Error   = err.$(Process)\n')                                                
        submit_file.write('Output  = out.$(Process)\n')
        submit_file.write('requirements = GLIBC == "2.11"\n')
        tarfile_name=optimizer_params.tarred_nrnproj
        submit_file.write('transfer_input_files = portable-neuron.tar.gz,'+tarfile_name+'\n')
        submit_file.write('should_transfer_files   = yes\n')
        submit_file.write('when_to_transfer_output = on_exit_or_evict\n')
        #this is where you have to do the clever stuff:
        
        for shellno in range(self.num_jobs):
            submit_file.write('executable = run'+str(shellno)+'.sh\n')
            submit_file.write('queue\n')
        
        #finally close the submit file
        submit_file.close()
    
    def __build_condor_files(self,candidates,candidates_per_job=100):
        
        #prepare list of candidates to be farmed on grid:
        self.__prepare_candidates(candidates,candidates_per_job=100)
        
        #make the job files (shell scripts to be executed on the execute nodes)
        job_number=0 #run shell script number
        for job in self.job_list:
            self.__make_job_file(job,job_number)
            job_number+=1
        
        #now make the submit file
        self.__make_submit_file()

    def __delete_remote_files(self,host):
        import ssh_utils
        command='rm -rf ./*'
        ssh_utils.issue_command(host, command)
    
    def __put_multiple_files(self,host,filelist,localdir='/',remotedir='/'):
        import ssh_utils
        
        for file in filelist:
            localpath=os.path.join(localdir,file)
            remotepath=os.path.join(remotedir,file)
            ssh_utils.put_file(host,localpath,remotepath)


class DumbEvaluator(__Evaluator):
    """
    The simulations themselves report their fitness. The evaluator
    just reads them from a file. Requires the appropriate controller.
    """

    def __init__(self,controller,fitness_filename_prefix,threads_number=1):
        self.controller = controller
        self.fitness_filename_prefix = fitness_filename_prefix
        self.threads_number = threads_number
        
    def evaluate(self,candidates,args):

        threads_number = int(self.threads_number)
        candidates_per_thread = (len(candidates)) / threads_number
        remainder_candidates = len(candidates) % threads_number
        chunk_begin = 0
        chunk_end = candidates_per_thread

        if remainder_candidates != 0:
            chunk_end += 1

        threads = []

        try:
            for i in range(0, threads_number):
                #if fitness file exists need to destroy it:
                file_name = self.fitness_filename_prefix + str(i)
                if os.path.exists(file_name):
                    os.remove(file_name)

                #run the candidates:
                candidate_section=candidates[chunk_begin:chunk_end]
                threads.append(Thread(target=self.controller.run, args=(candidate_section,args,file_name,)))
                threads[i].daemon=True            	
                threads[i].start()

                chunk_begin = chunk_end
                chunk_end += candidates_per_thread
                if i < (remainder_candidates - 1):
                    chunk_end += 1

            fitness = []   
            for i in range(0, threads_number):
               # we should let the main thread handle keybord interrupts
                while True:
                    threads[i].join(1)
                    if not threads[i].isAlive():
                        break

                #get their fitness from the file
                file_name =  self.fitness_filename_prefix + str(i)
                threads[i].join()
                fitness = fitness + [float(i) for i in open(file_name).readlines()]
                os.remove(file_name)
        except (KeyboardInterrupt, SystemExit):
            sys.exit("Interrupted by ctrl+c\n")
        
        return fitness
    
class IClampEvaluator(__Evaluator):
    """
    Locally-evaluates (not using cluster or grid computing) a model.
    
    The evaluate routine runs the model and returns its fitness value
      
    """
    def __init__(self,
                 analysis_start_time,
                 controller,
                 analysis_end_time,
                 target_data_path,
                 parameters,
                 analysis_var,
                 weights,
                 targets=None,
                 automatic=False):

        super(IClampEvaluator, self).__init__(parameters,
                                              weights,
                                              targets,
                                              controller)
      
        self.analysis_start_time=analysis_start_time
        self.analysis_end_time=analysis_end_time
        self.target_data_path=target_data_path
        self.analysis_var=analysis_var

        print('target data path in evaluator:'+target_data_path)
        
        if automatic == True:
            t , v_raw = analysis.load_csv_data(target_data_path)
            v = numpy.array(v_raw)

            v_smooth = list(analysis.smooth(v))

            ic_analysis = analysis.IClampAnalysis(v_smooth,
                                                    t,
                                                    analysis_var,
                                                    start_analysis=analysis_start_time,
                                                    end_analysis=analysis_end_time) 

            ic_analysis.analyse()

            self.targets = ic_analysis.analysis_results

            print('Obtained targets are:')
            print(self.targets)
        
    def evaluate(self,candidates,args):
        
        print("\n>>>>>  Evaluating: %s"%candidates)
        
        simulations_data = self.controller.run(candidates,
                                               self.parameters)

        fitness = []
        
        for data in simulations_data:

            times = data[0]
            samples = data[1]

            data_analysis=analysis.IClampAnalysis(samples,
                                                  times,
                                                  self.analysis_var,
                                                  start_analysis=self.analysis_start_time,
                                                  end_analysis=self.analysis_end_time,
                                                  target_data_path=self.target_data_path)

            
            try:
                data_analysis.analyse()
            except:
                data_analysis.analysable_data = False
                
                
            fitness_value = data_analysis.evaluate_fitness(self.targets,
                                                           self.weights,
                                                           cost_function=analysis.normalised_cost_function)
            fitness.append(fitness_value)

            print('Fitness: %s\n'%fitness_value)
            
        return fitness
    

class IClampCondorEvaluator(IClampEvaluator):
    """
    Evaluate simulations and return their fitness on a condor grid.
    
        Tested and known to work on CamGrid 
        (http://www.escience.cam.ac.uk/projects/camgrid/)
      
        WARNING:
        this entire class should now be considered obsolete, the evaluator
        is just an IClampEvaluator and everything here that is different
        from that class needs to become its own controller

    """

    def __init__(self,local_analysis=False):

        super(IClampCondorEvaluator,self).__init__()

        #other things like the number of nodes to divide the work onto and
        #host connection parameters need to go into this constructor

        if local_analysis:
            self.evaluate=self.__local_evaluate
        else:
            self.evaluate=self.__remote_evaluate__

    def __condor_evaluate(self,candidates,args):
        """
        Run simulations on grid and analyse data locally
        WARNING: (???I'm quite confused here...there is a mistake somewhere
        as the name doesn't match the description - which method is which?)
      
            Once each generation has finished, all data is pulled to local
            workstation in form of sqlite databases (1 database per job)
            and these are analysed and the fitness estimated sequentially
            the fitness array is then returned.
        """
        
        import time
        import ssh_utils
        
        self.CandidateData_list=[]
       
        self.__build_condor_files(candidates) #Build submit and runx.sh files, exp_id now corresponds to position in chromosome and fitness arrays
        
        messagehost=ssh_utils.host(optimizer_params.host,optimizer_params.username,optimizer_params.password,optimizer_params.port)
        
        self.__delete_remote_files__(messagehost)#delete everything in thssh_utilse directory you're about to put files in
        filelist=os.listdir(self.tmpdir)
        self.__put_multiple_files(messagehost,filelist,localdir=self.tmpdir,remotedir=optimizer_params.remotedir)#copy local files over
        filelist=os.listdir(self.portableswdir)
        self.__put_multiple_files(messagehost,filelist,localdir=self.portableswdir,remotedir=optimizer_params.remotedir)#copy local files over
        
        ssh_utils.issue_command(messagehost,'export PATH=/opt/Condor/release/bin:$PATH\ncondor_submit submitfile.submit')
        
        self.jobdbnames=[]
        for job_num in range(self.num_jobs):        #make a list of the databases we need:
            jobdbname='outputdb'+str(job_num)+'.sqlite'
            self.jobdbnames.append(jobdbname)
           
        #wait till you know file exists:
        dbs_created=False
        pulled_dbs=[] # list of databases which have been extracted from remote server
        while (dbs_created==False):
            print('waiting..')
            time.sleep(20)            
            print('checking if dbs created:')
            command='ls'
            remote_filelist=ssh_utils.issue_command(messagehost, command)

            for jobdbname in self.jobdbnames:

                db_exists=jobdbname+'\n' in remote_filelist
                
                if (db_exists==False):
                    print(jobdbname +' has not been generated')
                    dbs_created=False

                elif db_exists==True and jobdbname not in pulled_dbs:
                    print(jobdbname +' has been generated')
                    remotefile=optimizer_params.remotedir+jobdbname
                    localpath=os.path.join(self.datadir,str(self.generation)+jobdbname)
                    ssh_utils.get_file(messagehost,remotefile,localpath)
                    pulled_dbs.append(jobdbname) #so that it is not extracted more than once
                    #here pop-in the fitness evaluation

                if len(pulled_dbs)==len(self.jobdbnames):
                    dbs_created=True
            
        fitness=[]
        for CandidateData in self.CandidateData_list:
            job_num = CandidateData.job_num
            
            dbname=str(self.generation)+'outputdb'+str(job_num)+'.sqlite'
            dbpath=os.path.join(self.datadir,dbname)
            exp_id=CandidateData.exp_id
            
            connection=sqldbutils.db_connect(dbpath) #establish a database connection
            query='SELECT numerical_value\
                    FROM output_params WHERE experiment_id=\
                    '+str(exp_id)+' AND parameter="fitness"'       

            exp_fitness=sqldbutils.execute_query(connection,query)
            exp_fitness=exp_fitness.fetchall()
            exp_fitness=exp_fitness[0][0]
            
            #print('fitness: %s'%exp_fitness)
    
            fitness.append(exp_fitness)

        self.generation+=1
        return fitness

    def __local_evaluate(self,candidates,args):
        import time
     
        self.CandidateData_list=[]
        analysis_var=self.analysis_var
        
        #Build submitfile.submit and runx.sh files:
        self.__build_condor_files(candidates) #exp_id now corresponds to position in chromosome/fitness array
        
        fitness=[]
        #submit the jobs to the grid
        os.chdir(self.tmpdir)
        os.system('condor_submit submitfile.submit')
        
        #wait till you know file exists:
        dbs_created=False
        while (dbs_created==False):
            print('checking if dbs created:')
            for job_num in range(self.num_jobs):
                jobdbname='outputdb'+str(job_num)+'.sqlite'
                jobdbpath=os.path.join(self.datadir,jobdbname)
                print(jobdbpath)
                db_exists=os.path.exists(jobdbpath)
                
                if (db_exists==False):
                    time.sleep(60)
                    dbs_created=False
                    break
                
                dbs_created=True

        for CandidateData in self.CandidateData_list:
            job_num = CandidateData.job_num
            dbname='/outputdb'+str(job_num)+'.sqlite'
            dbpath=self.datadir+dbname
            exp_id=CandidateData.exp_id
            exp_data=sqldbutils.sim_data(dbpath,exp_id)
            analysis=analysis.IClampAnalysis(exp_data.samples,exp_data.t,analysis_var,5000,10000)
            exp_fitness=analysis.evaluate_fitness(optimizer_params.targets,optimizer_params.weights,cost_function=analysis.normalised_cost_function)
            fitness.append(exp_fitness)

        for job_num in range(self.num_jobs):
            jobdbname='outputdb'+str(job_num)+'.sqlite'
            jobdbpath=os.path.join(self.datadir,jobdbname)
            print(jobdbpath)
            os.remove(jobdbpath)

        return fitness

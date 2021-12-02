"""
The controllers module provides different controller classes,
applicable to different simulations.

A controller object's job is to control simulations-
At a high level a controller objects  accepts a list of
parameters and chromosomes and (usually) returns
corresponding simulation data.
This is implemented polymporphically in subclasses.
Each controller class must therefore provide a run method, which is used by
the evaluator to run a simulation.

A controller must be able to accept simulation parameters (chromosomes)
from the evaluator.

The evaluator is therefore only concerned with assigining fitness to chromosomes.

On the whole this allows for deep modularization -
as long as the user can provide a controller which will (for instance)
reutrn sample and time arrays for arbitrary chromosome and parameter
lists a range of evaluators would be able to utilise it.
"""

import os
import subprocess

import math


class __Controller:
    """
    Controller base class
    """

    def run(self, candidates, parameters):
        """
        At a high level - accepts a list of parameters and chromosomes
        and (usually) returns corresponding simulation data. This is
        implemented polymporphically in subclasses.
        """
        raise NotImplementedError("Valid controller requires run method!")


class CLIController(__Controller):
    """
    Control simulations via command line arguments executed through the Python os module.
    """

    def __init__(self, cli_argument):
        self.cli_argument = cli_argument

    def run(self, candidates, parameters, fitness_filename="evaluations"):

        # "Run simulation"

        for chromosome in candidates:
            self.chromosome = chromosome
            self.parameters = parameters  # actually unneeded
            # this manipulation is slightly messy, done for conversion of chromosome
            # into something that can be executed on the shell
            chromosome_str = "".join(str(e) + " " for e in chromosome)
            cla = self.cli_argument + " " + fitness_filename + " " + chromosome_str
            print(cla)
            subprocess.call(cla, shell=True)


class NrnProject(__Controller):
    """
    Run an nrnproject simulation based on optimizer parameters."""

    def __init__(self, nrnproject_path, db_path, exp_id=None):

        self.sim_main_path = os.path.join(nrnproject_path, "src/simrunner.py")
        self.nrnproject_path = nrnproject_path
        self.db_path = db_path
        self.exp_id = exp_id

    def __generate_cla(self):
        sim_var_string = self.__generate_sim_var_string()
        cla = "python " + self.sim_main_path + sim_var_string
        return cla

    def __generate_sim_var_string(self):
        sim_var_string = ""
        for i in enumerate(self.parameters):
            sim_var_string += (
                " \"sim_var['" + i[1] + "'] = " + str(self.chromosome[i[0]]) + '"'
            )

        if self.exp_id != None:
            sim_var_string += " \"sim_var['exp_id'] =" + str(self.exp_id) + '"'

        return sim_var_string

    def run(self, candidates, parameters):

        # """Run simulations"""

        import sqldbutils

        exp_data_array = []
        for chromosome in candidates:
            self.chromosome = chromosome
            self.parameters = parameters
            exp_id = sqldbutils.generate_exp_ids(self.db_path)
            cla = self.__generate_cla()
            os.chdir(self.nrnproject_path + "/src/")  # there should be a smarter way
            os.system(cla)
            print(self.db_path)
            print(exp_id)
            exp_data = sqldbutils.sim_data(self.db_path, exp_id)
            exp_data_array.append(exp_data)
        return exp_data_array


class __CondorContext(object):
    """Context for Condor-based grid"""

    def __init__(self, host, username, password, port):

        self.messagehost = ssh_utils.host(host, username, password, port)

    def __split_list(self, alist, wanted_parts=1):

        length = len(alist)
        return [
            alist[i * length // wanted_parts : (i + 1) * length // wanted_parts]
            for i in range(wanted_parts)
        ]

    def __prepare_candidates(self, candidates, candidates_per_job=1):

        # Split candidate list into smaller ones (jobs):
        # and make a job list
        if optimizer_params.candidates_in_job != None:
            candidates_in_job = optimizer_params.candidates_in_job
        else:
            candidates_in_job = candidates_per_job

        num_candidates = len(candidates)
        ids = range(num_candidates)
        enumerated_candidates = zip(candidates, ids)
        num_jobs = num_candidates / candidates_in_job
        self.num_jobs = num_jobs
        self.job_list = self.__split_list(
            enumerated_candidates, wanted_parts=self.num_jobs
        )

    def __make_job_file(self, job, job_number):
        # write the header:
        filepath = os.path.join(self.tmpdir, "run" + str(job_number) + ".sh")
        run_shell = open(filepath, "w")
        run_shell.write("#!/bin/bash\n")
        run_shell.write("reldir=`dirname $0`\n")
        run_shell.write("cd $reldir\n")
        run_shell.write("directory=`pwd`\n")
        run_shell.write("pndirectory=$directory\n")
        run_shell.write("#Untar the file:\n")
        run_shell.write("/bin/tar xzf ./portable-neuron.tar.gz\n")
        tarfile_name = optimizer_params.tarred_nrnproj
        run_shell.write("/bin/tar xzf ./" + tarfile_name + "\n")

        # CandidateData_list=[]
        for enumerated_candidate in job:

            chromosome = enumerated_candidate[0]
            candidate_info = CandidateData(chromosome)
            exp_id = enumerated_candidate[1]
            candidate_info.set_exp_id(exp_id)
            candidate_info.set_job_num(job_number)
            self.CandidateData_list.append(candidate_info)

            nproj = controllers.NrnProjSimRun(optimizer_params.project_path, chromosome)
            run_shell.write("#issue the commands\n")
            run_shell.write(
                "$pndirectory/pnpython.sh \
                    $directory/src/simrunner.py \"sim_var['exp_id'] \
                    = "
                + str(exp_id)
                + '" '
                + "\"sim_var['"
                "dbname"
                "'] \
                    = 'outputdb"
                + str(job_number)
                + ".sqlite'\""
                + nproj.sim_var_string
                + "\n"
            )
            run_shell.write("echo 'done'\n")

        run_shell.write(
            "cp $directory/sims/outputdb" + str(job_number) + ".sqlite $directory\n"
        )
        # self.CandidateData_list=CandidateData_list
        run_shell.close()

    def __make_submit_file(self):
        """write the condor submit files"""

        filepath = os.path.join(self.tmpdir, "submitfile.submit")
        submit_file = open(filepath, "w")

        submit_file.write("universe   = vanilla\n")
        submit_file.write("log        = pneuron.log\n")
        submit_file.write("Error   = err.$(Process)\n")
        submit_file.write("Output  = out.$(Process)\n")
        submit_file.write('requirements = GLIBC == "2.11"\n')
        tarfile_name = optimizer_params.tarred_nrnproj
        submit_file.write(
            "transfer_input_files = portable-neuron.tar.gz," + tarfile_name + "\n"
        )
        submit_file.write("should_transfer_files   = yes\n")
        submit_file.write("when_to_transfer_output = on_exit_or_evict\n")
        # this is where you have to do the clever stuff:

        for shellno in range(self.num_jobs):
            submit_file.write("executable = run" + str(shellno) + ".sh\n")
            submit_file.write("queue\n")

        # finally close the submit file
        submit_file.close()

    def __build_condor_files(self, candidates, parameters, candidates_per_job=100):

        # prepare list of candidates to be farmed on grid:
        self.__prepare_candidates(candidates, candidates_per_job=100)

        # make the job files (shell scripts to be executed on the execute nodes)
        job_number = 0  # run shell script number
        for job in self.job_list:
            self.__make_job_file(job, job_number)
            job_number += 1

        # now make the submit file
        self.__make_submit_file()

    def __delete_remote_files(self, host):
        import ssh_utils

        command = "rm -rf ./*"
        ssh_utils.issue_command(host, command)

    def __put_multiple_files(self, host, filelist, localdir="/", remotedir="/"):
        import ssh_utils

        for file in filelist:
            localpath = os.path.join(localdir, file)
            remotepath = os.path.join(remotedir, file)
            ssh_utils.put_file(host, localpath, remotepath)


class NrnProjectCondor(NrnProject):
    """
    Run NrnProject-based simulations on a Condor-managed
    federated system
    """

    def __init__(
        self,
        host,
        username,
        password,
        port=80,
        local_analysis=False,
        candidates_per_job=100,
    ):

        super(NrnProjectCondor, self).__init__()

        # other things like the number of nodes to divide the work onto and
        # host connection parameters need to go into this constructor
        # the more I think about it the less this seems like a good idea
        # though

        if local_analysis:
            self.run = self.__local_run
        else:
            self.run = self.__remote_run__

        # make a context which provides grid utilities
        self.context = __CondorContext(host, username, password, port)

        self.cpj = candidates_per_job

    def __condor_run(self, candidates, parameters):
        """
        Run simulations on grid and analyse data locally (???I'm quite confused here...there is a mistake somewhere as the name doesn't match the description - which method is which?)

            Once each generation has finished, all data is pulled to local
            workstation in form of sqlite databases (1 database per job)
            and these are analysed and the fitness estimated sequentially
            the fitness array is then returned.
        """

        import time
        import ssh_utils

        # Build submit and runx.sh files, exp_id now corresponds
        # to position in chromosome and fitness arrays
        self.context.__build_condor_files(
            candidates, parameters, candidates_per_job=self.cpj
        )

        # This is a file handling block..
        # delete everything in the ssh_utilse directory you're about to put files in
        self.__delete_remote_files__()
        filelist = os.listdir(self.tmpdir)
        # copy local files over, some stuff is missing here as it needs to be an attribute in the condor context
        self.__put_multiple_files(filelist, localdir=self.tmpdir)
        filelist = os.listdir(self.portableswdir)
        # copy portable software files over:
        self.__put_multiple_files(filelist, localdir=self.portableswdir)

        # issue a command to the message host to issue commands to the grid:
        ssh_utils.issue_command(
            context.messagehost,
            "export PATH=/opt/Condor/release/bin:$PATH\ncondor_submit submitfile.submit",
        )

        # make a list of the database files we need:
        self.jobdbnames = []
        for job_num in range(self.num_jobs):
            jobdbname = "outputdb" + str(job_num) + ".sqlite"
            self.jobdbnames.append(jobdbname)

        # wait till we know file exists:
        dbs_created = False
        pulled_dbs = (
            []
        )  # list of databases which have been extracted from remote server
        while dbs_created == False:
            print("waiting..")
            time.sleep(20)
            print("checking if dbs created:")
            command = "ls"
            remote_filelist = ssh_utils.issue_command(self.messagehost, command)
            for jobdbname in self.jobdbnames:
                db_exists = jobdbname + "\n" in remote_filelist
                if db_exists == False:
                    print(jobdbname + " has not been generated")
                    dbs_created = False
                elif db_exists == True and jobdbname not in pulled_dbs:
                    print(jobdbname + " has been generated")
                    remotefile = optimizer_params.remotedir + jobdbname
                    localpath = os.path.join(
                        self.datadir, str(self.generation) + jobdbname
                    )
                    ssh_utils.get_file(self.messagehost, remotefile, localpath)
                    pulled_dbs.append(
                        jobdbname
                    )  # so that it is not extracted more than once
                    # here pop-in the fitness evaluation
                if len(pulled_dbs) == len(self.jobdbnames):
                    dbs_created = True

        # this block can be simplified, it need simply return exp_data containers
        fitness = []
        for CandidateData in self.CandidateData_list:
            job_num = CandidateData.job_num

            dbname = str(self.generation) + "outputdb" + str(job_num) + ".sqlite"
            dbpath = os.path.join(self.datadir, dbname)
            exp_id = CandidateData.exp_id

            connection = sqldbutils.db_connect(
                dbpath
            )  # establish a database connection
            query = (
                "SELECT numerical_value\
                    FROM output_params WHERE experiment_id=\
                    "
                + str(exp_id)
                + ' AND parameter="fitness"'
            )

            exp_fitness = sqldbutils.execute_query(connection, query)
            exp_fitness = exp_fitness.fetchall()
            exp_fitness = exp_fitness[0][0]

            print("Fitness:")
            print(exp_fitness)

            fitness.append(exp_fitness)

        self.generation += 1
        return fitness

    ###ignore this for now###
    def __local_evaluate(self, candidates, args):
        import time

        analysis

        self.CandidateData_list = []
        analysis_var = self.analysis_var

        # Build submitfile.submit and runx.sh files:
        self.__buil_condor_files(
            candidates
        )  # exp_id now corresponds to position in chromosome/fitness array

        fitness = []
        # submit the jobs to the grid
        os.chdir(self.tmpdir)
        os.system("condor_submit submitfile.submit")

        # wait till you know file exists:
        dbs_created = False
        while dbs_created == False:
            print("checking if dbs created:")
            for job_num in range(self.num_jobs):
                jobdbname = "outputdb" + str(job_num) + ".sqlite"
                jobdbpath = os.path.join(self.datadir, jobdbname)
                print(jobdbpath)
                db_exists = os.path.exists(jobdbpath)

                if db_exists == False:
                    time.sleep(60)
                    dbs_created = False
                    break

                dbs_created = True

        for CandidateData in self.CandidateData_list:
            job_num = CandidateData.job_num
            dbname = "/outputdb" + str(job_num) + ".sqlite"
            dbpath = self.datadir + dbname
            exp_id = CandidateData.exp_id
            exp_data = sqldbutils.sim_data(dbpath, exp_id)
            analysis = analysis.IClampAnalysis(
                exp_data.samples, exp_data.t, analysis_var, 5000, 10000
            )
            exp_fitness = analysis.evaluate_fitness(
                self.targets,
                self.weights,
                cost_function=analysis.normalised_cost_function,
            )
            fitness.append(exp_fitness)

        for job_num in range(self.num_jobs):
            jobdbname = "outputdb" + str(job_num) + ".sqlite"
            jobdbpath = os.path.join(self.datadir, jobdbname)
            print(jobdbpath)
            os.remove(jobdbpath)

        return fitness


class SineWaveController(__Controller):
    """
    Simple sine wave generator which takes a number of variables ('amp', 'period', 'offset')
    and produces an output based on these.
    """

    def __init__(self, sim_time, dt):

        self.sim_time = sim_time
        self.dt = dt

    def run_individual(self, sim_var, gen_plot=False, show_plot=False):
        """
        Run an individual simulation.

        The candidate data has been flattened into the sim_var dict. The
        sim_var dict contains parameter:value key value pairs, which are
        applied to the model before it is simulated.

        """
        print(">> Running individual: %s" % (sim_var))

        import numpy as np

        t = 0
        times = []
        volts = []

        while t <= self.sim_time:
            v = sim_var["offset"] + (
                sim_var["amp"] * (math.sin(2 * math.pi * t / sim_var["period"]))
            )
            times.append(t)
            volts.append(v)
            t += self.dt

        if gen_plot:
            from matplotlib import pyplot as plt

            info = ""
            for key in sim_var.keys():
                info += "%s=%s " % (key, sim_var[key])
            plt.plot(times, volts, label=info)
            plt.legend(
                loc="upper center",
                bbox_to_anchor=(0.5, -0.05),
                fancybox=True,
                shadow=True,
                ncol=1,
            )

            if show_plot:
                plt.show()

        return np.array(times), np.array(volts)

    def run(self, candidates, parameters):
        """
        Run simulation for each candidate

        This run method will loop through each candidate and run the simulation
        corresponding to its parameter values. It will populate an array called
        traces with the resulting voltage traces for the simulation and return it.
        """

        traces = []
        for candidate in candidates:
            sim_var = dict(zip(parameters, candidate))
            t, v = self.run_individual(sim_var)
            traces.append([t, v])

        return traces

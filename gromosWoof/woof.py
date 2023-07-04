from glob import glob
import pandas as pd
import os
import subprocess
import time
from datetime import datetime
from gromosWoof.ssh import SSHConnection
import numpy as np
import warnings
from natsort import natsorted

class Woof():
    def __init__(self,user: str, basepath: str = "./", host: str = None,  progressbar = True):
        """
        Watchdog class

        Args:
            user (str): username to connect to host and query slurm jobs. Defaults to None.
            basepath (str, optional): Path to the directory where the individual simulation folders are. Defaults to "./".
            host (str, optional): hostname to connect to to get slurm status. Defaults to None.
            progressbar (bool, optional): Displays an ASCII progress-bar. Defaults to True.
        """
        print("starting up")
        self.basepath = os.path.abspath(basepath)
        self.user = user
        self.progressbar = progressbar

        self.connection = SSHConnection(host=host, user=user)

        # Initialization
        dirs = list()
        runfiles = list()
        status = list()
        jobIDs = list()
        runtimes = list()

        # Loop over directories in the basepath and create dataframe
        for all_runs in natsorted(glob(self.basepath+'/**/*.run', recursive=True)):
            dirs.append(os.path.dirname(all_runs))
            runfiles.append(os.path.basename(all_runs))
            status.append("unknown")
            jobIDs.append(None)
            runtimes.append(np.NAN)

        self.df = pd.DataFrame({'dir': dirs, 'runfile': runfiles, 'status':status, 'jobID': jobIDs, 'runtime': runtimes}, copy=True)
        self.df.set_index(["dir","runfile"], inplace=True)

    def check(self):
        # Goes through all individual runs and checks, if there is already a finished omd file and checks if the run finished successfully
        for i in self.df.iterrows():
            dirpath = i[0][0]
            runfile = i[0][1]
            omdpath = dirpath + "/" + runfile.split(".run")[0] + ".omd"
            if not self.df.at[(dirpath, runfile), 'status'] == "finished":
                if os.path.isfile(omdpath):
                    lines = subprocess.Popen(['tail', '-20', omdpath], stdout=subprocess.PIPE).stdout.readlines()
                    if b'MD++ finished successfully\n' in lines:
                        self.df.at[(dirpath, runfile), 'status'] = 'finished'
                        time = np.NAN
                        for l in lines:
                            if l.startswith(b"Overall time used:") or l.startswith(b'Wall time total'):
                                time = float(l.split()[-1])
                        self.df.at[(dirpath, runfile), 'runtime'] = time
                    else:
                        self.df.at[(dirpath, runfile), 'status'] = 'crashed'
                else:
                    self.df.at[(dirpath, runfile), 'status'] = 'pending'

        jobs, err = self.connection.exec_command(f"squeue -u {self.user} -o '%A,%T,%o'")

        for job in jobs.split('\n')[1:-1]:
            jID, jStat, Jcmd = job.split(",")
            dirname = os.path.dirname(Jcmd)
            runfile = os.path.basename(Jcmd)

            if (dirname, runfile) in self.df.index:
                self.df.at[(dirname, runfile), 'jobID'] = jID
                self.df.at[(dirname, runfile), 'status'] = jStat

    def summarize(self):
        # Printing function that prints a pretty summary
        print("{:<30}{:<9}{:<11}{:<10}{:<8}".format("Directory","Finished","Total Runs", "Status", "ETA (h)"))
        for rundir, data in self.df.groupby(level=0, sort=False):
            runName = rundir.split("/")[-1]
            nruns = len(data)
            finished_runs = (data['status'] == 'finished').sum()
            hasErr = 'crashed' in data['status']
            perc_finished = finished_runs / nruns
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                avg_runtime = np.nanmean(data['runtime'].values)
            hours_left = (nruns - finished_runs) * (avg_runtime / 3600)
            if finished_runs == nruns:
                status = "FINISHED"
            else:
                status = data['status'][finished_runs]
            
            if hasErr:
                color = '\033[91m' # red
            elif perc_finished == 1:
                color = '\033[92m' # green
            else:
                color = ''

            color_reset = '\033[0m'

            print(color+"{:<30}{:<9}{:<11}{:<10}{:<8.2f}".format(runName, finished_runs, nruns, status, hours_left) + color_reset, end="")

            if self.progressbar:
                if os.get_terminal_size().columns < 150:
                    print("")
                print(color+f"[{'x'*round(perc_finished*75)}{'-'*round((1-perc_finished)*75)}]" + color_reset)
            else:
                print("")
    
    def guard(self, refresh_time: int = 30):
        """
        Main function, calls self.check periodically and displays the result in a formatted way

        Args:
            refresh_time (int, optional): Time to refresh in seconds. Defaults to 30.
        """
        while True:
            try:
                self.check()
                os.system("clear")
                print(f"Last check on {datetime.now().isoformat()}")
                self.summarize()
                time.sleep(refresh_time)
            except KeyboardInterrupt:
                print("\nExiting...")
                self.connection.closeSession()
                exit()
# GromosWoof

A simple python tool to monitor the status of running gromos simulations in a slurm environment.

## Installation

1. Download the git repository
2. Change directory into the repository.
3. Run `pip install .`
4. Done.

## Usage

### Prerequisites

Your gromos jobs need to be in the following directory structure (names of the directories are not important, but numbers of the runs are):

```
basedir
    Simulation1
        sim_1.run
        sim_1.omd
        sim_2.run
        sim_2.omd
        sim_n.run
        sim_n.omd
        ...
    Simulation2
        ...
    ...
```

The remote file system needs to be on the same path on your local machine (where the script is running) and on the cluster (where the active slurm jobs are checked).

### Simple usage

Create a python script with the following content

```{python}
from gromosWoof.woof import Woof

dog = Woof(basedir=*path_of_basedir*, user=*your_username*, host=*host_of_slurm_server*, progressbar=True)
dog.guard(refresh_time=*seconds_to_refresh_status*)
```

Run this script with: `python script.py`

This will then try to connect to your remote host using ssh, goes through all directories in your basepath and tries to determine the status of your runs. A summary is displayed in the console and refreshed periodically.
# CIC-asymptotics
Codes for Change-in-Change Asymptotics project with Xavier D'Haultfoeuille and Martin Mugnier.

## Main file:
[simulation.py](simulation.py) is the main file for running the simulations. It loads the configuration from the YAML file [example_config_simulation.yml](example_config_simulation.yml).

Can be ran from terminal by being in the main folder and entering:
```
python3 simulation.py example_config_simulation.yml
```

## Parallel computing:
Simulations can be ran in parallel from the terminal using GNU parallel tool. First, YAML files need to be created using the script [create_yml_files.py](create_yml_files.py). Then, simulations can be ran in parallel inputing the YAML file names from the automatically created list.

```
python3 create_yml_files.py
parallel -a files_list.txt python3 simulation.py
```

Different outputs are produced from this scripts, among which the summary of the results in a pickle file. Then to aggregate them all and create a latex table, run:

```
generate_latex.py
```

If 'parallel' is not installed, run before:

```
sudo apt-get update
sudo apt-get install parallel
```

## Important folders:
- [functions](functions/): contains all the necessary functions splitted by theme,
- [test_scripts](test_scripts/): contains scripts that were used to develop the functions.

## Other folders:
- input_configs: will be created when running create_yml_files.py](create_yml_files.py) and will contain the necessary YAML files,
- output: will also be created when running [simulation.py](simulation.py). It will contain simulations results (log files, histograms, latex table) as well as saved raw results as pickle format (inside the "raw" folder).
Both folders should not be pushed to git repo.

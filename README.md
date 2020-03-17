# Traffic Stops Analysis

This repository contains the code necessary to run the DSC180A traffic stops analysis project. The following are included in the San Diego traffic stops analysis:

1. Relevant descriptive statistics
2. Stop rate and post-stop outcome analysis
3. Veil of Darkness analysis

## Usage Instructions

* Targets:
    * project: run replication on all data
    * test-project: run replication on small amount of test data
* Using 'run.py':
    * To run replication on test data on the DSMLP server, use commands:
        launch-scipy-ml.sh -i your_docker_hub/your_docker_image
        cd project && python run.py test-project

## Description of Contents
The project consists of these portions:
'''
PROJECT
├── README.md
├── config
│   ├── 01-data-params.json
│   ├── 02-test-data-params.json
│   ├── 01-clean-params.json
│   ├── 02-test-clean-params.json
│   └── env.json
├── data
│   ├── raw
│   ├── cleaned
│   ├── out
│   └── test
├── references
│   └── census_2010_datadict.txt
├── run.py
└── src
    ├── data
    │   └── get_data.py
    ├── process
    │   └── clean_data.py
    ├── analyze
        └── analysis.py

'''

### `src`

* `data/get_data.py`: Libary code that executes tasks to get the data.
* `process/clean_data.py`: Libary code that executes tasks to clean the data.
* `analysis/analyze.py`: Libary code that performs analysis on the cleaned data.

### `config`

* `01-data-params.json`: parameters for getting data, serving as
  inputs to library code.

* `02-test-data-params.json`: parameters for getting small amounts of data, serving as
  inputs to library code.

* `01-clean-params.json`: parameters for getting cleaning data, serving as
  inputs to library code.

* `02-test-clean-params.json`: parameters for cleaning test data, serving as
  inputs to library code.

* `env.json`: parameters for accessing the projects Docker Image and list of outputted files.

### `references`

* `census_2010_datadict.txt` : datadict for census data

# Open Targets Code Test

Queries the Open Targets REST API by target and/or disease ID and outputs the results as well as simple metrics (min, max, avg, stdev) for the corresponding association score.

Python 3.6 or later is required to run this module.

## Create the virtual environment and install dependencies
```bash
python3 -m venv env
source env/bin/activate
python3 -m pip -q install --upgrade setuptools pip
python3 -m pip -q install --upgrade --requirement requirements.txt
```

## Run the tests
With the environment activated:
```bash
python3 -m pytest
```

## Run
With the environment activated:
```bash
python3 ot_query.py -t ENSG00000197386 -d Orphanet_399
```

Where:
* `-t` runs analysis for a given Ensembl gene (target)
* `-d` runs analysis for a given disease, specified as an ontology term

Both flags are optional. When both flags are specified, target and disease analyses are run independently of each other, and the results are provided separately.

## Output format
The script outputs results for each query (one row per one entry returned), as well as simple statistics for the `association_score.overall` field: min, max, avg, and stdev.

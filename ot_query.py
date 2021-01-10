#!/usr/bin/env python3

import argparse
import logging

# Set up logging facilities
logging.basicConfig()
logger = logging.getLogger(__name__)

# Set up the argument parser but don't parse just yet
parser = argparse.ArgumentParser('Query the Open Targets REST API by target (gene) and/or by disease and calculate '
                                 'simple statistics for the association_score.overall: min, max, avg and stdev. Both '
                                 'parameters are optional, but at least one must be specified. When both parameters are'
                                 'specified, the target and disease analyses are run separately.')
parser.add_argument('-t', '--target', required=False, help='Target (gene) ID, e.g. ENSG00000197386.')
parser.add_argument('-d', '--disease', required=False, help='Disease ID, e.g. Orphanet_399.')


def main(target_id, disease_id):
    assert target_id or disease_id, 'At least one of (target ID, disease ID) must be specified'


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.target, args.disease)

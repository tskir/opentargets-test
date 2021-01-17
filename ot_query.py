#!/usr/bin/env python3

import argparse
import logging
import sys

import opentargets
import pandas as pd
import retry


# Set up logging facilities
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Set up the argument parser but don't parse just yet
parser = argparse.ArgumentParser('Query the Open Targets REST API by target (gene) and/or by disease and calculate '
                                 'simple statistics for the association_score.overall: min, max, avg and stdev. Both '
                                 'parameters are optional, but at least one must be specified. When both parameters are'
                                 'specified, the target and disease analyses are run separately.')
parser.add_argument('-t', '--target', required=False, help='Target (gene) ID, e.g. ENSG00000197386.')
parser.add_argument('-d', '--disease', required=False, help='Disease ID, e.g. Orphanet_399.')


@retry.retry(tries=5, delay=5, backoff=1.2, jitter=(1, 3), logger=logger)
def query_rest_api(ot_client, filter_type: str, filter_value: str):
    """Query the Open Targets REST API with the appropriate filters. Retry if necessary in case of network errors.

    Args:
        ot_client: Instance of an Open Targets client for querying
        filter_type: which field to filter by. Can be either 'target' or 'disease'.
        filter_value: which value to filter by in a given filter.

    Return:
        A list of (target_id, disease_id, association_score.overall) tuples, possibly empty if nothing is found.
    """
    associations = ot_client.filter_associations(**{filter_type: filter_value})
    return [(a['target']['id'], a['disease']['id'], a['association_score']['overall']) for a in associations]


def main(target_id: str, disease_id: str):
    if not (target_id or disease_id):
        logger.error('At least one of (target ID, disease ID) must be specified')
        sys.exit(1)
    ot_client = opentargets.OpenTargetsClient()
    for filter_type, filter_value in (('target', target_id), ('disease', disease_id)):
        logger.info(f'Query by filter {filter_type} with value {filter_value}')
        if not filter_type:
            logger.info('Nothing to query.')
            continue
        associations = query_rest_api(ot_client, filter_type, filter_value)
        if not associations:
            logger.info('No associations found for the query.')
            continue
        associations = pd.DataFrame(associations)
        logger.info('  Found associations:')
        logger.info(associations)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.target, args.disease)

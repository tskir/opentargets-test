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

# Configure Pandas settings
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)

# Set up the argument parser but don't parse just yet
parser = argparse.ArgumentParser('Query the Open Targets REST API by target (gene) and/or by disease and calculate '
                                 'simple statistics for the association_score.overall: min, max, avg and stdev. Both '
                                 'parameters are optional, but at least one must be specified. When both parameters are'
                                 'specified, the target and disease analyses are run separately.')
parser.add_argument('-t', '--target', required=False, help='Target (gene) ID, e.g. ENSG00000197386.')
parser.add_argument('-d', '--disease', required=False, help='Disease ID, e.g. Orphanet_399.')


@retry.retry(tries=5, delay=5, backoff=1.2, jitter=(1, 3), logger=logger)
def query_rest_api(ot_client, filter_type: str, filter_value: str) -> pd.DataFrame:
    """Query the Open Targets REST API with the appropriate filters. Retry if necessary in case of network errors.

    Args:
        ot_client: Instance of an Open Targets client for querying
        filter_type: which field to filter by. Can be either 'target' or 'disease'.
        filter_value: which value to filter by in a given filter.

    Return:
        A Pandas dataframe with target_id, disease_id, and association_score.overall columns, one row per one entry
        in the query result. Possibly empty if nothing is found.
    """
    associations = list(ot_client.filter_associations(**{filter_type: filter_value}))

    # Construct the dataframe. Since Pandas doesn't yet support a composite dtype in a dataframe constructor, the
    # easiest way (which would not rely on dtype autodetection) is to supply column as separate series with explicit
    # dtype.
    association_df = pd.DataFrame({
        'target_id': pd.Series([a['target']['id'] for a in associations], dtype='str'),
        'disease_id': pd.Series([a['disease']['id'] for a in associations], dtype='str'),
        'association_score_overall': pd.Series([a['association_score']['overall'] for a in associations], dtype='float')
    })

    return association_df


def main(target_id: str, disease_id: str) -> None:

    # Check if we have anything to query
    if not (target_id or disease_id):
        sys.exit('At least one of (target ID, disease ID) must be specified')

    # Init the Open Targets client and do the query. Store the dataframes rather than printing immediately, because we
    # need to first print the raw results, and then separately summary statistics per query type.
    ot_client = opentargets.OpenTargetsClient()
    associations = {
        filter_type: query_rest_api(ot_client, filter_type, filter_value)
        for filter_type, filter_value in (('target', target_id), ('disease', disease_id))
        if filter_value
    }

    # Print the associations
    for filter_type, results in associations.items():
        print(f'Query results for {filter_type}:')
        print(results)
        print()

    # Print the summary statistics
    for filter_type, results in associations.items():
        print(f'Summary results for {filter_type}:')
        print(f'Minimum = {results.association_score_overall.min():.3f}')
        print(f'Maximum = {results.association_score_overall.max():.3f}')
        print(f'Mean = {results.association_score_overall.mean():.3f}')
        print(f'Standard deviation = {results.association_score_overall.std():.3f}')
        print()


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.target, args.disease)

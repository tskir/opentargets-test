#!/usr/bin/env python3

import argparse
import sys

import opentargets as ot
import pandas as pd
import retry


# Check Python version
if sys.version_info < (3, 6):
    sys.exit('Python 3.6 or newer is required to run this module.')

# Configure Pandas settings for complete dataframe printouts
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 10)
pd.set_option('max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)

# Set up the argument parser but don't parse just yet
parser = argparse.ArgumentParser('Query the Open Targets REST API by target (gene) and/or by disease and calculate '
                                 'simple statistics for the association_score.overall: min, max, avg and stdev. When '
                                 'both parameters are specified, the target and disease analyses are run separately.')
parser.add_argument('-t', '--target', required=False, help='Target (gene) ID, e.g. ENSG00000197386.')
parser.add_argument('-d', '--disease', required=False, help='Disease ID, e.g. Orphanet_399.')


@retry.retry(tries=5, delay=5, backoff=1.2, jitter=(1, 3))
def query_rest_api(ot_client: ot.OpenTargetsClient, filter_type: str, filter_value: str) -> list:
    """Query the Open Targets REST API with the appropriate filters. Retry if necessary in case of network errors.

    Args:
        ot_client: Instance of an Open Targets client for querying.
        filter_type: Filter name to query by, can be 'target' or 'disease'.
        filter_value: The value for the selected filter.

    Returns:
        * If the filter value is unspecified, None.
        * Otherwise, a list of association results (can be empty if nothing was found).
    """
    return list(ot_client.filter_associations(**{filter_type: filter_value})) if filter_value else None


def get_associations(ot_client: ot.OpenTargetsClient, target_id: str, disease_id: str) -> dict:
    """Based on target and/or disease ID, perform the necessary queries and format the association data in the form
    of a Pandas dataframe.

    Args:
        ot_client: Instance of an Open Targets client for querying.
        target_id: Target (gene) ID as understood by the Open Targets API, e.g. ENSG00000197386.
        disease_id: Disease ID as understood by the Open Targets API, e.g. Orphanet_399.

    Returns:
        A dict with two keys ('target' and 'disease'). The value for each field will be:
        * If the corresponding filter value is unspecified, None
        * Otherwise, a Pandas dataframe with three columns: target_id, disease_id, score_overall. The dataframe can be
          empty if no results were found.
    """
    association_result = dict()
    for filter_type, filter_value in (('target', target_id), ('disease', disease_id)):
        associations = query_rest_api(ot_client, filter_type, filter_value)
        if associations is None:
            result = None
        else:
            result = pd.DataFrame({
                'target_id': pd.Series([a['target']['id'] for a in associations], dtype='str'),
                'disease_id': pd.Series([a['disease']['id'] for a in associations], dtype='str'),
                'score_overall': pd.Series([a['association_score']['overall'] for a in associations], dtype='float')
            })
            # Verify API sanity
            assert set(result[filter_type + '_id']) == {filter_value}, 'API returned inconsistent results'
        association_result[filter_type] = result
    return association_result


def print_association_data(associations: dict) -> None:
    """Prints the raw association data, one row per entry returned by query.

    Args:
        associations: The association dict, as returned by get_associations().
    """
    for filter_type, results in associations.items():
        print(f'Query results for {filter_type}:')
        if results is None:
            print('No filter was specified for this query.')
        elif len(results) == 0:
            print('The query did not return any results.')
        else:
            print(results)
        print()


def print_summary_metrics(associations: dict) -> None:
    """Prints the summary metrics for the association data.

    Args:
        associations: The association dict, as returned by get_associations().
    """
    for filter_type, results in associations.items():
        print(f'Summary results for {filter_type}:')
        if results is None:
            print('No filter was specified for this query.')
        elif len(results) == 0:
            print('The query did not return any results.')
        else:
            print(f'Minimum = {results.score_overall.min():.3f}')
            print(f'Maximum = {results.score_overall.max():.3f}')
            print(f'Mean = {results.score_overall.mean():.3f}')
            print(f'Standard deviation = {results.score_overall.std():.3f}')
            print()


def main(target_id: str, disease_id: str) -> None:
    """Do the queries, print the full results first, and then the summary statistics.

    Args:
        target_id: Target (gene) ID as understood by the Open Targets API, e.g. ENSG00000197386.
        disease_id: Disease ID as understood by the Open Targets API, e.g. Orphanet_399.
        """

    # Init the Open Targets client
    ot_client = ot.OpenTargetsClient()

    # Get the associations
    associations = get_associations(ot_client, target_id, disease_id)

    # Print the associations
    print_association_data(associations)

    # Print the summary statistics
    print_summary_metrics(associations)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.target, args.disease)

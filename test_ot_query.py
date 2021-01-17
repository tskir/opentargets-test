#!/usr/bin/env python3

import itertools
import opentargets as ot
import pandas as pd

import ot_query


mock_data_client = {
    'target': [
        {'target': {'id': 'valid_target'}, 'disease': {'id': 'diseaseA'}, 'association_score': {'overall': 1.00}},
        {'target': {'id': 'valid_target'}, 'disease': {'id': 'diseaseB'}, 'association_score': {'overall': 0.70}},
        {'target': {'id': 'valid_target'}, 'disease': {'id': 'diseaseC'}, 'association_score': {'overall': 0.50}},
    ],
    'disease': [
        {'target': {'id': 'targetA'}, 'disease': {'id': 'valid_disease'}, 'association_score': {'overall': 1.00}},
        {'target': {'id': 'targetB'}, 'disease': {'id': 'valid_disease'}, 'association_score': {'overall': 0.70}},
        {'target': {'id': 'targetC'}, 'disease': {'id': 'valid_disease'}, 'association_score': {'overall': 0.50}},
    ]
}

mock_data_df = {
    'target': pd.DataFrame({
                  'target_id': pd.Series(['valid_target', 'valid_target', 'valid_target'], dtype='str'),
                  'disease_id': pd.Series(['diseaseA', 'diseaseB', 'diseaseC'], dtype='str'),
                  'score_overall': pd.Series([1.00, 0.70, 0.50], dtype='float')
              }),
    'disease': pd.DataFrame({
                  'target_id': pd.Series(['targetA', 'targetB', 'targetC'], dtype='str'),
                  'disease_id': pd.Series(['valid_disease', 'valid_disease', 'valid_disease'], dtype='str'),
                  'score_overall': pd.Series([1.00, 0.70, 0.50], dtype='float')
               })
}


class OpenTargetsClientMock(ot.OpenTargetsClient):

    def filter_associations(self, **kwargs):
        if int('target' in kwargs) + int('disease' in kwargs) != 1:
            raise AssertionError('The mock client must always receive exactly one query attribute')
        for filter_type in ('target', 'disease'):
            if filter_type in kwargs:
                if kwargs[filter_type] == 'valid_' + filter_type:
                    return mock_data_client[filter_type]
                else:
                    return []


mock_ot_client = OpenTargetsClientMock()


def test_query_rest_api():
    """Test the API query functionality, as well as the internal consistency of the mock Open Targets client."""
    for filter_type in ('target', 'disease'):
        result_filter_unspecified = ot_query.query_rest_api(mock_ot_client, filter_type, None)
        assert result_filter_unspecified is None, 'Expected None when filter is not specified'

        result_no_data = ot_query.query_rest_api(mock_ot_client, filter_type, 'nonexistent_' + filter_type)
        assert result_no_data == [], 'Expected empty list when filter returns no values'

        result_success = ot_query.query_rest_api(mock_ot_client, filter_type, 'valid_' + filter_type)
        assert result_success == mock_data_client[filter_type], 'Expected data with correct filter settings'


def test_get_associations():
    """Test the functionality to get associations for all combinations of (unspecified, nonexistent, valid) values for
    target and disease parameters."""
    target_ids = (None, 'nonexistent_target', 'valid_target')
    disease_ids = (None, 'nonexistent_target', 'valid_target')
    for target_id, disease_id in itertools.product(target_ids, disease_ids):
        result = ot_query.get_associations(mock_ot_client, target_id, disease_id)
        assert set(result.keys()) == {'target', 'disease'}, 'Result must always contain two specific keys'
        # Check target and disease associations
        for filter_type, filter_value in (('target', target_id), ('disease', disease_id)):
            if filter_value is None:
                assert result[filter_type] is None, 'Expected None when filter is not specified'
            elif filter_value == 'nonexistent_' + filter_type:
                assert result[filter_type].empty, 'Expected empty dataframe when filter returns no values'
            elif filter_value == 'valid_' + filter_type:
                assert result[filter_type].equals(mock_data_df[filter_type]), 'Expected specific dataframes'

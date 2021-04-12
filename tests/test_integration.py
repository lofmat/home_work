import os
import pytest
import pyexasol
import configparser
from fetch_matches_score import import_csv, fetch_match_data_by_date

config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())

test_dir = os.path.dirname(os.path.abspath(__file__))
test_data = os.path.join(test_dir, 'test_data')

# CSV for tests
correct_csv = os.path.join(test_data, 'positive_short_soccer_scores.csv')
missed_values_csv = os.path.join(test_data, 'negative_missed_vals_short_soccer_scores.csv')
incorrect_type_of_values_csv = os.path.join(test_data,
                                                  'negative_incorrect_data_types_inside_csv_short_soccer_scores.csv')
incomplete_date_csv = os.path.join(test_data, 'negative_incomplete_date_soccer_scores.csv')

# DB related parameters
test_config = os.path.join(test_dir, 'config', 'test_config.ini')


def compare_output_with_csv_data(csv_data, output, year, month):
    with open(csv_data, 'r') as cf:
        data_list = cf.readlines()
        if len(data_list):
            for line in data_list:
                if not line.startswith('#') and f'{year}-{month}-' in line:
                    x = []
                    for i in line.strip().split(','):
                        if not i:
                            i = None
                        elif len(i) == 1:
                            i = int(i)
                        x.append(i)

                    t = tuple(x)
                    if t not in output:
                        return False
            return True


def test_e2e_correct_data_format():
    import_csv(csv_file=correct_csv,
               fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
               cfg_path=test_config)

    output = fetch_match_data_by_date(month='10',
                                      year='2020',
                                      cfg_path=test_config,
                                      date_column_name='MATCH_DATE')
    assert compare_output_with_csv_data(csv_data=correct_csv,
                                        output=output,
                                        year='2020',
                                        month='10')


# 'MATCH_DATE': 'DATE' -> 'MATCH_DATE': 'VARCHAR(10)'
def test_e2e_correct_data_format_char_instead_of_date_type():
    import_csv(csv_file=correct_csv,
               fields={'MATCH_DATE': 'VARCHAR(10)', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
               cfg_path=test_config)

    output = fetch_match_data_by_date(month='10',
                                      year='2020',
                                      cfg_path=test_config,
                                      date_column_name='MATCH_DATE')
    assert compare_output_with_csv_data(csv_data=correct_csv,
                                        output=output,
                                        year='2020',
                                        month='10')


def test_e2e_missed_values_in_csv():
    import_csv(csv_file=missed_values_csv,
               fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
               cfg_path=test_config)

    output = fetch_match_data_by_date(month='10',
                                      year='2020',
                                      cfg_path=test_config,
                                      date_column_name='MATCH_DATE')
    assert compare_output_with_csv_data(csv_data=missed_values_csv,
                                        output=output,
                                        year='2020',
                                        month='10')


def test_import_incorrect_data_types_in_csv():
    with pytest.raises(pyexasol.exceptions.ExaQueryError) as ex:
        assert import_csv(csv_file=incorrect_type_of_values_csv,
                          fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
                          cfg_path=test_config)
    assert "Transformation of value='A' failed - invalid character value for cast;" in str(ex.value)


def test_import_incomplete_date():
    with pytest.raises(pyexasol.exceptions.ExaQueryError) as ex:
        assert import_csv(csv_file=incomplete_date_csv,
                          fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
                          cfg_path=test_config)
    assert "Transformation of value='2020-10-' failed - invalid value for DD format token" in str(ex.value)

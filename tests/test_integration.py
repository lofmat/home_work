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
csv_injection_file = os.path.join(test_data, 'negative_csv_injection_soccer_scores.csv')

# DB related parameters
test_config = os.path.join(test_dir, 'config', 'test_config.ini')
wrong_dsn_test_config = os.path.join(test_dir, 'config', 'fake_dsn_test_config.ini')
wrong_creds_test_config = os.path.join(test_dir, 'config', 'fake_creds_test_config.ini')
non_existed_table_config = os.path.join(test_dir, 'config', 'fake_db_table_test_config.ini')


# Compare data from csv file and select result
def compare_output_with_csv_data(csv_data, output, year, month):
    with open(csv_data, 'r') as cf:
        # Data from CSV
        data_list = cf.readlines()
        if len(data_list):
            for line in data_list:
                # Skip 1st line with headers
                if not line.startswith('#') and f'{year}-{month}-' in line:
                    tlist = []
                    # Split CSV lines by ',' and cut \n in the end
                    for val in line.strip().split(','):
                        if not val:
                            # Replace space with None
                            val = None
                        else:
                            try:
                                # Convert value if it possible
                                val = int(val)
                            except ValueError:
                                pass
                        # Make list and then convert it to tuple
                        tlist.append(val)
                    tpl = tuple(tlist)
                    # in the case of the first mismatch -> exit
                    if tpl not in output:
                        return False
            return True


def test_e2e_call_main():
    """Check simple call of the main function"""
    import fetch_matches_score
    out = fetch_matches_score.main(month='09', year=2020, source_csv=correct_csv)
    assert f"2020-09-01, 0:3" in out
    assert len(out) == 1


def test_e2e_call_main_empty_response():
    """Main call when select when the request should have returned nothing"""
    import fetch_matches_score
    out = fetch_matches_score.main(month='11', year=2021, source_csv=correct_csv)
    assert len(out) == 0


def test_e2e_correct_data_format():
    """Call all function separately with correct config and fields dict"""
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


def test_e2e_correct_data_format_char_instead_of_date_type():
    """ Case when date of match was stored as 'MATCH_DATE': 'VARCHAR(10)'"""
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
    """ CSV with missed score of goals"""
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


def test_select_incorrect_table_name():
    """ SELECT with incorrect table name """
    with pytest.raises(pyexasol.exceptions.ExaQueryError) as ex:
        assert fetch_match_data_by_date(month='10',
                                        year='2020',
                                        cfg_path=non_existed_table_config,
                                        date_column_name='MATCH_DATE')
    assert "object PUB3439.NON_EXISTENT_TABLE not found" in str(ex.value)


def test_import_incorrect_data_types_in_csv():
    """ CSV with letters instead of numbers"""
    with pytest.raises(pyexasol.exceptions.ExaQueryError) as ex:
        assert import_csv(csv_file=incorrect_type_of_values_csv,
                          fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
                          cfg_path=test_config)
    assert "Transformation of value='A' failed - invalid character value for cast;" in str(ex.value)


def test_import_incomplete_date():
    """ Date looks like 2020-10- """
    with pytest.raises(pyexasol.exceptions.ExaQueryError) as ex:
        assert import_csv(csv_file=incomplete_date_csv,
                          fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
                          cfg_path=test_config)
    assert "Transformation of value='2020-10-' failed - invalid value for DD format token" in str(ex.value)


def test_incorrect_db_address():
    """ Wrong DB address """
    with pytest.raises(pyexasol.exceptions.ExaConnectionDsnError) as ex:
        assert import_csv(csv_file=correct_csv,
                          fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
                          cfg_path=wrong_dsn_test_config)
    assert "Could not resolve IP address of host" in str(ex.value)


def test_incorrect_db_creds():
    """ Wrong DB credentials """
    with pytest.raises(pyexasol.exceptions.ExaAuthError) as ex:
        assert import_csv(csv_file=correct_csv,
                          fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
                          cfg_path=wrong_creds_test_config)
    assert "Connection exception - authentication failed." in str(ex.value)


def test_csv_injection():
    """ CSV contains some insecure constructions """
    with pytest.raises(Exception) as ex:
        assert import_csv(csv_file=csv_injection_file,
                          fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
                          cfg_path=test_config)
    assert "CSV file contains insecure construction" in str(ex.value)




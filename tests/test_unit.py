import pytest
import os
from argparse import ArgumentTypeError

from fetch_matches_score import valid_month, valid_year, valid_path, format_matches_data


# input parameters validation tests
@pytest.mark.parametrize("month", ['03', '12'])
def test_valid_month_correct_value(month):
    assert valid_month(month) == month


@pytest.mark.parametrize("month", ['3', 'A3', ' ', '0'])
def test_valid_month_incorrect_value(month):
    with pytest.raises(ArgumentTypeError) as ex:
        assert valid_month(month)
    assert f"Parameter 'month' should have the following format -> 'MM' but has -> '{month}'." in str(ex.value)


@pytest.mark.parametrize("year", ['02020', '2o2o', ' ', '0', '4000'])
def test_valid_year_incorrect_value(year):
    with pytest.raises(ArgumentTypeError) as ex:
        assert valid_year(year)
    assert f"Parameter 'month' should have the following format -> 'YYYY' but has -> '{year}'." in str(ex.value)


@pytest.mark.parametrize("year", ['2020', '1000', '3999'])
def test_valid_year_correct_value(year):
    assert valid_year(year) == year


@pytest.mark.parametrize("path", [os.getcwd()])
def test_valid_path_correct_value(path):
    assert valid_path(path) == path


@pytest.mark.parametrize("path", ['/home/fake_user/1/2/3', ''])
def test_valid_path_incorrect_value(path):
    with pytest.raises(ArgumentTypeError) as ex:
        assert valid_path(path)
    assert f"No such path: '{path}'." in str(ex.value)


@pytest.mark.parametrize("data", [[], ])
def test_data_formatting_empty_dataset(data):
    assert len(format_matches_data(data)) == 0


@pytest.mark.parametrize("data", [[('2020-10-17', 1, 2), ('2020-10-15', 0, 1), ('2020-10-14', 1, 1)]])
def test_data_formatting(data):
    res = format_matches_data(data)
    assert len(res) == len(data)
    for row in data:
        s = f"{row[0]}, {row[1]}:{row[2]}"
        assert s in res


@pytest.mark.parametrize("data", [[('2020-10-17', 1, ' ')]])
def test_data_formatting(data):
    res = format_matches_data(data)
    assert len(res) == len(data)
    assert f"2020-10-17, 1:None" in res


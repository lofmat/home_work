import pytest
from fetch_matches_score import valid_month, valid_year

from argparse import ArgumentTypeError


@pytest.mark.parametrize("month", ['03', '12'])
def test_valid_month_correct_month_value(month):
    assert valid_month(month) == month


@pytest.mark.parametrize("month", ['3', 'A3', ' ', '0'])
def test_valid_month_incorrect_month_value(month):
    with pytest.raises(ArgumentTypeError):
        valid_month(month)


@pytest.mark.parametrize("year", ['02020', '2o2o', ' ', '0', '4000'])
def test_valid_month_incorrect_year_value(year):
    with pytest.raises(ArgumentTypeError):
        valid_year(year)


@pytest.mark.parametrize("year", ['2020', '1000', '3999'])
def test_valid_month_correct_year_value(year):
    assert valid_year(year) == year



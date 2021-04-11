import os
import pytest
import configparser
from fetch_matches_score import import_csv, fetch_match_data_by_date

config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
test_dir = os.path.dirname(os.path.abspath(__file__))

def test_e2e_correct_data_format():
    pass

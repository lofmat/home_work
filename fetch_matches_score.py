import os
import re
import contextlib

from argparse import ArgumentParser, ArgumentTypeError
import configparser
import pyexasol
import logging

config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
logging.basicConfig(level=logging.INFO)


# Context manager for DB connection
@contextlib.contextmanager
def get_exasol_conn(cfg):
    conn = pyexasol.connect_local_config('DB_CONNECTION', config_path=cfg)
    try:
        yield conn
    finally:
        conn.close()


# Check if it existed path
def valid_path(path: str) -> str:
    if os.path.exists(path):
        return path
    else:
        msg = f"No such path: '{path}'."
        raise ArgumentTypeError(msg)


# Check if month that passed as command line parameter
# has 2 digits and starts with '0' if it less than 10
def valid_month(m: str) -> str:
    if re.match(r'0[1-9]|1[0-2]', m):
        return m
    else:
        msg = f"Parameter 'month' should have the following format -> 'MM' but has -> '{m}'."
        raise ArgumentTypeError(msg)


# Check if year has 4 digits and starts with '1', '2' or '3'
def valid_year(y: str) -> str:
    if re.match(r'[1-3][0-9]{3}$', y):
        return y
    else:
        msg = f"Parameter 'month' should have the following format -> 'YYYY' but has -> '{y}'."
        raise ArgumentTypeError(msg)


def create_parser() -> ArgumentParser:
    # Construct the argument parser
    ap = ArgumentParser(description=f'The utility can select the results of matches '
                                    f'through a query by year and month')
    required_params = ap.add_argument_group('required arguments')
    optional_params = ap.add_argument_group('optional arguments')
    # Add the arguments to the parser
    required_params.add_argument("-m", "--month",
                                 required=True,
                                 help="Month number e.g 03 or 12",
                                 type=valid_month)
    required_params.add_argument("-y", "--year",
                                 required=True,
                                 help="Year number e.g. 1994",
                                 type=valid_year)
    optional_params.add_argument("-s", "--source_csv",
                                 help="CSV file abs path to load data to DB",
                                 type=valid_path)
    return ap


# Load data to DB from csv file
def import_csv(csv_file: str, fields: dict, cfg_path: str) -> None:
    # Read ini configuration file
    config.read(cfg_path)
    with get_exasol_conn(cfg=cfg_path) as conn:
        conn.open_schema(config['DB_CONFIG']['schema'])
        # Convert dict {'column1':'type1', 'column2': 'type2'}
        # to string 'column1 type1, column2 type2'
        fields_str = ', '.join(f"{key} {val}" for (key, val) in fields.items())
        create_table_query = f"CREATE TABLE IF NOT EXISTS {config['DB_CONFIG']['table']} ({fields_str})"
        conn.execute(create_table_query)
        # Cleanup the table to be sure that the table after loading will contain correct dataset
        conn.execute(f"TRUNCATE TABLE {config['DB_CONFIG']['table']}")
        # Import data from csv to db
        conn.import_from_file(csv_file, f"{config['DB_CONFIG']['table']}")
        # Check result
        stmt = conn.last_statement()
        logging.info(f'IMPORTED {stmt.rowcount()} rows in {stmt.execution_time}s')
        logging.info(f'Source file is {csv_file}')


# Get matches data
def fetch_match_data_by_date(month: str, year: str, cfg_path: str, date_column_name: str) -> list:
    # Read ini configuration file
    config.read(cfg_path)
    with get_exasol_conn(cfg=cfg_path) as conn:
        conn.open_schema(config['DB_CONFIG']['schema'])
        # Select matches data where column with date contains date that starts with 'year-month-'
        stmt = conn.execute(f"SELECT *  FROM "
                            f"{config['DB_CONFIG']['schema']}.{config['DB_CONFIG']['table']}"
                            f" WHERE {date_column_name} LIKE '{year}-{month}-%'")
    # Will be returned list of tuples like ('2020-10-17', 1, 2)
    return stmt.fetchall()


def format_matches_data(data: list) -> list:
    formatted_data = []
    for match in data:
        # Unpack tuple such as ('2020-10-11', 0, 0)
        d, h, v = match
        # Check if home and visitor goals count exist in the table and have
        # correct format
        score_regex = re.compile(r'^(?:[1-9][0-9]{3}|[1-9][0-9]{2}|[1-9][0-9]|[0-9])$')
        # ('2020-10-17', 1, 2) -> '2020-10-17, 1:2'
        formatted_data.append(f"{d}"
                              f", {h if score_regex.match(str(h)) else None}"
                              f":{v if score_regex.match(str(v)) else None}")
    return formatted_data


if __name__ == '__main__':
    # ini config path
    project_root = os.path.dirname(os.path.abspath(__file__))
    default_cfg = os.path.join(project_root, 'config.ini')
    # Create parser
    parser = create_parser()
    args = vars(parser.parse_args())
    logging.info(f"Script arguments -> Month: {args['month']}, Year: {args['year']}.")
    # Load data if needed
    if args['source_csv']:
        import_csv(csv_file=args['source_csv'],
                   fields={'MATCH_DATE': 'DATE', 'Home': 'DECIMAL(4,0)', 'Visitor': 'DECIMAL(4,0)'},
                   cfg_path=default_cfg)
    # Fetch data from table
    matches_data = fetch_match_data_by_date(month=args['month'],
                                            year=args['year'],
                                            cfg_path=default_cfg,
                                            date_column_name='MATCH_DATE')
    if len(matches_data) > 0:
        print('Date, Home:Visitors')
        res = format_matches_data(matches_data)
        for r in res:
            print(r)
    else:
        logging.warning(f"There were no matches in such month!")



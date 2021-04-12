# home_work

Fetch/load matches score

#HOWTO run app

1. Install python3.9, pip
2. git clone https://github.com/lofmat/home_work.git
3. cd home_work
4. pip install -r requirements.txt
5. python3.9 fetch_matches_score.py -m 10 -y 2020 -s csv_data/soccer_scores.csv

#HOWTO start tests

1. cd home_work
2. export PYTHONPATH=$(pwd)
3. python3.9 -m pytest -s -v

#NOTE 

Script tested on the following environment:
  * Ubuntu 18
  * python3.9
  * Exasol Cloud
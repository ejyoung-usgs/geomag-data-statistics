geomag-data-statistics
======================
Run statistics on how often USGS geomagnetic observatory data becomes available.

Getting Started
---------------

### Dependencies:

* Python 3 Interpreter
* PostgresSQL or Sqlite
  * If Postgres: [py-postgresql](http://python.projects.pgfoundry.org/)

### Getting Started:

1. Install Python3

2. Clone the repository

3. Setup database of choice
  1. For postgres, install py-postgresql someplace the interpreter can find it

4. Edit configs to fit your environment in geostat.py

    ```python
configs["observatories"] = ["BOU", "BRW", "BSL", "CMO", "DED", "FRD", "FRN", "GUA", "HON", "NEW", "SHU", "SIT", "SJG", "TUC"]
configs["delays"] = [datetime.timedelta(minutes = 1),datetime.timedelta(minutes = 5), datetime.timedelta(minutes = 10),datetime.timedelta(minutes = 15)]
configs["db"] = geopsqladaptor.PostgresAdapter("username", "database", configs["observatories"],configs["delays"])
configs["html_file"] = "statistics.html"
configs["filters"] = [datetime.timedelta(days = 30), datetime.timedelta(days = 7), datetime.timedelta(days = 0)]
### Note, the 0 days filter means a range of today - 0 days to today, meaning a current day statistic.
    ```
    1. observatories are the USGS Codes to identify the station.
    2. delays are timedeltas to represent how far back to look when checking to see if data is available.
    3. db is the database adaptor. Create an instance of PostgresAdaptor or SqliteAdaptor
    4. html_file is the resulting web page
    5. filters is the range to calculate an average for

5. Setup task to run the script at your given interval
  1. Example of crontab to run every minute:  `* * * * * * /usr/local/bin/python3 $HOME/geomag-data-statistics/geostat.py`

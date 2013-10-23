import urllib.request
import argparse
import datetime
import re
import sqlite3
import time

import geosqliteatapter

def setupEnv():
    argParser = argparse.ArgumentParser(description = "Gather information from Geomag HTTP site")
    argParser.add_argument("observatory", help = "Observatory to gather data on")
    args = argParser.parse_args();
    
    configs = dict()
    
    ## Setup all runtime configurations here ##
    configs["observatory"] = args.observatory
    configs["url"] = "http://magweb.cr.usgs.gov/data/magnetometer"
    return configs
    
def start_http_session( url ):

    today_utc = datetime.datetime.utcnow()
    deltas = []
    deltas.append( datetime.timedelta() )
    deltas.append( datetime.timedelta( minutes = 1 )  )
    deltas.append( datetime.timedelta( minutes = 5 )  )
    deltas.append( datetime.timedelta( minutes = 10 ) )
    deltas.append( datetime.timedelta( minutes = 15 ) )

    request = urllib.request.urlopen(url)
    regex_string = "{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}.*"
    dataset=[]
    geo_data = request.read().decode("utf-8")

    for dtime in deltas:
        today_date = today_utc - dtime
        search_regex = re.compile( regex_string.format(year = today_date.year, month = today_date.month, day = today_date.day, hour = today_date.hour, minute = today_date.minute, second =0) )
        result = re.search( search_regex, geo_data )
        if(result is None):
            print ("regex not matched for", today_date, regex_string.format(year = today_date.year, month = today_date.month, day = today_date.day, hour = today_date.hour, minute = today_date.minute, second =0) )
        else:
            print("Found", result.group())
            if "99999.00" not in result.group():
                print("data is valid")
                dataset.append(True)
            else:
                print("data is not valid")
                dataset.append(False)
    return dataset
    
def form_file_name(obs_str, date):
    file_template = "{obs}{year:4d}{month:02d}{day:02d}vmin.min"
    today_year = date.year
    today_month = date.month
    today_day = date.day
    
    return file_template.format( obs = obs_str, year = today_year, month = today_month, day = today_day )
    
runtimeConfigs = setupEnv()
requestString = "{url}/{observatory}/{type}/{file}"
today_date = datetime.datetime.utcnow()
data_sets=[]

#### Code to test the database ####
dbAdapter = geosqliteatapter.SqliteAdapter("testdb.db")

#Make dynamic later
while True:
    data_stats = start_http_session( requestString.format( url = runtimeConfigs["url"], observatory = runtimeConfigs["observatory"], type = "OneMinute", file= form_file_name("frd", today_date) ) )
    if len(data_sets ) > 5:
        data_sets = data_sets[1:]
        data_sets.append(data_stats)
        
        
        
       # for d in data_sets
    time.sleep(60)

print( form_file_name("FRD", today_date) )
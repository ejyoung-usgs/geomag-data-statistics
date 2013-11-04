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
    configs["db"] = geosqliteatapter.SqliteAdapter("testdb.db")
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
    data_regex_string = "(-?\\d{1,5}\\.\\d{2}\\s+){4}"
    data_regex = re.compile( data_regex_string )
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
            data_result = re.search(data_regex, result.group() )
            data_points = data_result.group().split()
            data_map = dict()
            data_map["h"] = data_points[0] 
            data_map["d"] = data_points[1] 
            data_map["z"] = data_points[2] 
            data_map["f"] = data_points[3] 

            delay_value = dtime.seconds
            observatory_name = runtimeConfigs["observatory"]
            db_data = get_record(observatory_name, delay_value)
            for key, value in data_map.items():
                old_average = db_data[key]
                point_count = db_data["point_count"]
                valid = 0
                if value != "99999.00":
                    valid = 100
                new_average = (old_average * point_count + valid) / ( point_count + 1)
                #### Strip fraction off ####
                new_average = str(new_average).split(".")[0]
                print(new_average)
    
def form_file_name(obs_str, date):
    file_template = "{obs}{year:4d}{month:02d}{day:02d}vmin.min"
    today_year = date.year
    today_month = date.month
    today_day = date.day
    
    return file_template.format( obs = obs_str, year = today_year, month = today_month, day = today_day )

def insert_new_record(observatory, db):
    dbAdapter = geosqliteatapter.SqliteAdapter(db)
    #dbAdapter.insert_stat()

def get_record(observatory, delay):
    dbAdapter = runtimeConfigs["db"]
    observatory_key = dbAdapter.find_location_id_by_name(observatory)
    delay_key = dbAdapter.find_delay_id_by_value(delay)
    return dbAdapter.select_stat(observatory_key, delay_key)
    
runtimeConfigs = setupEnv()
requestString = "{url}/{observatory}/{type}/{file}"
today_date = datetime.datetime.utcnow()
data_sets=[]

#Make dynamic later
while True:
    start_http_session( requestString.format( url = runtimeConfigs["url"], observatory = runtimeConfigs["observatory"], type = "OneMinute", file= form_file_name("frd", today_date) ) )        
        
       # for d in data_sets
    time.sleep(60)

print( form_file_name("FRD", today_date) )




############# SHAME #####################
#### Adjusted sum is ( average * data_points + new_value ) / ( n + 1 )
import urllib.request
import datetime
import re
import sqlite3
import time

import geosqliteatapter

def setupEnv():    
    configs = dict()
    
    ## Setup all runtime configurations here ##
    configs["observatories"] = ["BOU", "BDT", "BRW", "BSL", "CMO", "DED", "FRD", "FRN", "GUA", "HON", "NEW", "SHU", "SIT", "SJG", "TUC"]
    configs["delays"] = [datetime.timedelta(minutes=0), datetime.timedelta(minutes=1),datetime.timedelta(minutes=5), datetime.timedelta(minutes=7),datetime.timedelta(minutes=10),datetime.timedelta(minutes=15)]
    configs["url"] = "http://magweb.cr.usgs.gov/data/magnetometer"
    configs["db"] = geosqliteatapter.SqliteAdapter("geostat.db", configs["observatories"], configs["delays"])
    configs["log_file"] = "log.txt"
    return configs
    
def start_http_session( observatory ):

    today_utc = datetime.datetime.utcnow()
    deltas = runtimeConfigs["delays"]

    requestString = "{url}/{observatory}/{type}/{file}"
    #requestString.format( url = runtimeConfigs["url"], observatory = runtimeConfigs["observatory"], type = "OneMinute", file= form_file_name("frd", today_date) ) )
    url = requestString.format( url = runtimeConfigs["url"], observatory = observatory, type = "OneMinute", file = form_file_name(observatory.lower(), today_utc) )
    try:
        request = urllib.request.urlopen(url)
        regex_string = "{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}.*"
        data_regex_string = "(-?\\d{1,5}\\.\\d{2}\\s*){4}"
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
                data_result = re.search(data_regex, result.group() )
                data_points = data_result.group().split()
                data_map = dict()
                data_map["h"] = data_points[0] 
                data_map["d"] = data_points[1] 
                data_map["z"] = data_points[2] 
                data_map["f"] = data_points[3] 

                delay_value = dtime.seconds
                db_data = get_record(observatory, delay_value)
                for key, value in data_map.items():
                    old_average = db_data[key]
                    point_count = db_data["point_count"]
                    valid = 0
                    if value != "99999.00":
                        valid = 100
                    new_average = (old_average * point_count + valid) / ( point_count + 1)
                    #### Strip fraction off ####
                    db_data[key] = str(new_average).split(".")[0]
                db_data["point_count"] = db_data["point_count"] + 1
                update_record(db_data)
    except urllib.error.HTTPError:
        print("Error connecting to ", url)
    
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

def update_record(data_map):
    dbAdapter = runtimeConfigs["db"]
    dbAdapter.update_geostat(data_map["id"], data_map["h"], data_map["d"], data_map["z"], data_map["f"], data_map["point_count"])

def printTable():
    log = open(runtimeConfigs["log_file"], "w")
    log.close()
    log = open(runtimeConfigs["log_file"], "a")
    dbAdapter = runtimeConfigs["db"]
    #### TODO Parse data into some logical table structure ####
    all_stats = dbAdapter.get_all_stats()
    print_str = "|| {:^14} || {:^8} || {:^5} || {:^5} || {:^5} || {:^5} ||"
    print(print_str.format("Observatory", "Delay(s)", "H", "D", "Z", "F"))
    log.write(print_str.format("Observatory", "Delay", "h", "d", "z", "f") )
    log.write("\n")
    for item in all_stats:
        print (print_str.format(item["obs"], item["delay"], item["h"], item["d"], item["z"], item["f"]))
        log.write(print_str.format(item["obs"], item["delay"], item["h"], item["d"], item["z"], item["f"]))
        log.write("\n")
    log.close()
    print("\n\n")

    
runtimeConfigs = setupEnv()
data_sets=[]

#Make dynamic later
while True:
    for obs in runtimeConfigs["observatories"]:
        start_http_session( obs )
    printTable()
    time.sleep(60)


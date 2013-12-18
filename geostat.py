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
    configs["delays"] = [datetime.timedelta(minutes=1),datetime.timedelta(minutes=5), datetime.timedelta(minutes=6), datetime.timedelta(minutes=7), datetime.timedelta(minutes=8), datetime.timedelta(minutes=9), datetime.timedelta(minutes=10),datetime.timedelta(minutes=15)]
    configs["url"] = "http://magweb.cr.usgs.gov/data/magnetometer"
    configs["db"] = geosqliteatapter.SqliteAdapter("geostat.db", configs["observatories"], configs["delays"])
    configs["html_file"] = "statistics.html"
    configs["program_start"] = datetime.datetime.now()
    return configs
    
def start_http_session( observatory ):

    today_utc = datetime.datetime.utcnow()
    deltas = runtimeConfigs["delays"]

    requestString = "{url}/{observatory}/{type}/{file}"
    #requestString.format( url = runtimeConfigs["url"], observatory = runtimeConfigs["observatory"], type = "OneMinute", file= form_file_name("frd", today_date) ) )
    url = requestString.format( url = runtimeConfigs["url"], observatory = observatory, type = "OneMinute", file = form_file_name(observatory.lower(), today_utc) )
    url_sec = requestString.format( url = runtimeConfigs["url"], observatory = observatory, type = "OneSecond", file = form_file_name_sec(observatory.lower(), today_utc) )
    try:
        request = urllib.request.urlopen(url)
        request_sec = urllib.request.urlopen(url)
        regex_string = "{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}.*"
        data_regex_string = "(-?\\d{1,5}\\.\\d{2}\\s*){4}"
        data_regex = re.compile( data_regex_string )
        dataset=[]
        dataset_s = []
        geo_data = request.read().decode("utf-8")
        geo_data_s = request.read().decode("utf-8")

        for dtime in deltas:
            today_date = today_utc - dtime
            search_regex = re.compile( regex_string.format(year = today_date.year, month = today_date.month, day = today_date.day, hour = today_date.hour, minute = today_date.minute, second =0) )
            result = re.search( search_regex, geo_data )
            result_s = re.search( search_regex, geo_data_s)
            if(result is None):
                print ("regex not matched for", today_date, regex_string.format(year = today_date.year, month = today_date.month, day = today_date.day, hour = today_date.hour, minute = today_date.minute, second =0) )
            else:
                data_result = re.search(data_regex, result.group() )
                data_result_s = re.search(data_regex, result_s.group() )
                data_points = data_result.group().split()
                data_points_s = data_result_s.group().split()
                data_map = dict()
                data_map_s = dict()
                data_map["h"] = data_points[0] 
                data_map["d"] = data_points[1] 
                data_map["z"] = data_points[2] 
                data_map["f"] = data_points[3] 

                data_map_s["h"] = data_points_s[0] 
                data_map_s["d"] = data_points_s[1] 
                data_map_s["z"] = data_points_s[2] 
                data_map_s["f"] = data_points_s[3] 

                delay_value = dtime.seconds
                db_data = get_record(observatory, delay_value, "min")
                for key, value in data_map.items():
                    old_average = db_data[key]
                    point_count = db_data["point_count"]
                    valid = 0
                    if value != "99999.00":
                        valid = 100
                    new_average = (old_average * point_count + valid) / ( point_count + 1)
                    db_data[key] = new_average
                db_data["point_count"] = db_data["point_count"] + 1
                update_record(db_data)

                db_data = get_record(observatory, delay_value, "sec")
                for key, value in data_map_s.items():
                    old_average = db_data[key]
                    point_count = db_data["point_count"]
                    valid = 0
                    if value != "99999.00":
                        valid = 100
                    new_average = (old_average * point_count + valid) / ( point_count + 1)
                    db_data[key] = new_average
                db_data["point_count"] = db_data["point_count"] + 1
                update_record(db_data)

    except urllib.error.HTTPError:
        print("Error connecting to ", url)
    except http.client.IncompleteRead:
        print("Incomplete Read, Something went wrong network side")
    
def form_file_name(obs_str, date):
    file_template = "{obs}{year:4d}{month:02d}{day:02d}vmin.min"
    today_year = date.year
    today_month = date.month
    today_day = date.day
    
    return file_template.format( obs = obs_str, year = today_year, month = today_month, day = today_day )

def form_file_name_sec(obs_str, date):
    file_template = "{obs}{year:4d}{month:02d}{day:02d}vsec.sec"
    today_year = date.year
    today_month = date.month
    today_day = date.day
    return file_template.format( obs = obs_str, year = today_year, month = today_month, day = today_day )

def get_record(observatory, delay, res):
    dbAdapter = runtimeConfigs["db"]
    observatory_key = dbAdapter.find_location_id_by_name(observatory)
    delay_key = dbAdapter.find_delay_id_by_value(delay)
    res_key = dbAdapter.find_res_id_by_name(res)
    return dbAdapter.select_stat(observatory_key, delay_key, res_key)

def update_record(data_map):
    dbAdapter = runtimeConfigs["db"]
    dbAdapter.update_geostat(data_map["id"], data_map["h"], data_map["d"], data_map["z"], data_map["f"], data_map["point_count"])

def printTable():
    log = open(runtimeConfigs["html_file"], "w")
    header_file = open("head.html")
    header = header_file.read()
    log.write(header)
    header_file.close()
    print("Uptime", datetime.datetime.now() - runtimeConfigs["program_start"])
    dbAdapter = runtimeConfigs["db"]
    print_str = "<tr> <td>{}</td> <td>{:.2f}%</td> <td>{:.2f}%</td> <td>{:.2f}%</td> <td>{:.2f}%</td> </tr>\n"
    title_str = "<tr> <th>Observatory</th> <th>H</th> <th>D</th> <th>Z</th> <th>F</th> <th>Delay: {:2.0f} Minutes </th> </tr>\n"
    div_str = "<div id=\"delay{delay}\" class=\"delays\">\n"

    log.write("<div class=\"select_box\">\n<select onchange=\"showTime(this)\">\n")
    option_str = "<option value=\"{0}\">{0} Minute(s)</option>\n"
    for d in runtimeConfigs["delays"]:
        if int(d.seconds/60) == 10:
            log.write("<option selected=\"selected\" value=\"10\"> 10 Minute(s) </option>\n")
        else:
            log.write(option_str.format(str(int(d.seconds/60))))
    log.write("</select>\n</div>\n")

    for d in runtimeConfigs["delays"]:
        log.write( div_str.format(delay = int(d.seconds/60)) )
        log.write( "<table>\n")
        all_stats = dbAdapter.get_stats_for_delay(d.seconds)
        log.write(title_str.format(d.seconds/60) )
        for item in all_stats:
            log.write(print_str.format(item["obs"], item["h"], item["d"], item["z"], item["f"]))
        log.write("</table>\n")
        log.write("</div>\n")
    footer_file = open("foot.html")
    footer = footer_file.read()
    log.write(footer)
    footer_file.close()
    log.close()

    
runtimeConfigs = setupEnv()

while True:
    for obs in runtimeConfigs["observatories"]:
        start_http_session( obs )
    printTable()
    time.sleep(60)


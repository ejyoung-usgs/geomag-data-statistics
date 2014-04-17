import urllib.request
import datetime
import re
import sqlite3
import time
import http
import subprocess

import geosqliteatapter
import geopsqladaptor

def setupEnv():
    configs = dict()

    ## Setup all runtime configurations here ##
    configs["observatories"] = ["BOU", "BRW", "BSL", "CMO", "DED", "FRD", "FRN", "GUA", "HON", "NEW", "SHU", "SIT", "SJG", "TUC"]
    configs["delays"] = [datetime.timedelta(minutes=1),datetime.timedelta(minutes=5), datetime.timedelta(minutes=10),datetime.timedelta(minutes=15)]
    configs["url"] = "http://magweb.cr.usgs.gov/data/magnetometer"
    configs["db"] = geopsqladaptor.PostgresAdapter("username", configs["observatories"], configs["delays"])
    configs["html_file"] = "statistics.html"
    configs["program_start"] = datetime.datetime.now()
    configs["filters"] = [datetime.timedelta(days=30), datetime.timedelta(days = 7), datetime.timedelta(days = 0)]
    #configs["program_start"] = time.time()
    return configs

def start_http_session( observatory ):

    today_utc = datetime.datetime.utcnow()
    deltas = runtimeConfigs["delays"]

    requestString = "{url}/{observatory}/{type}/{file}"
    url = requestString.format( url = runtimeConfigs["url"], observatory = observatory, type = "OneMinute", file = form_file_name(observatory.lower(), today_utc) )
    url_sec = requestString.format( url = runtimeConfigs["url"], observatory = observatory, type = "OneSecond", file = form_file_name_sec(observatory.lower(), today_utc) )
    try:
        request = urllib.request.urlopen(url)
        request_sec = urllib.request.urlopen(url_sec)
        regex_string = "{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}.*"
        data_regex_string = "(-?\\d{1,5}\\.\\d{2}\\s*){4}"
        geo_data = request.read().decode("utf-8")
        geo_data_s = request_sec.read().decode("utf-8")

        for dtime in deltas:
            today_date = today_utc - dtime
            search_regex = re.compile( regex_string.format(year = today_date.year, month = today_date.month, day = today_date.day, hour = today_date.hour, minute = today_date.minute, second =0) + data_regex_string)
            search_regex_s = re.compile( regex_string.format(year = today_date.year, month = today_date.month, day = today_date.day, hour = today_date.hour, minute = today_date.minute, second = today_date.second) + data_regex_string )
            process_data(geo_data, search_regex, "min", dtime, observatory)
            process_data(geo_data_s, search_regex_s, "sec", dtime, observatory)

    except urllib.error.HTTPError:
        print("Error connecting to ", url)
        for dtime in deltas:
            data_map_m = {"h": 1, "d": 1, "z": 1, "f":1, "delay": dtime.seconds, "timestamp": datetime.date.today(), "res":"min", "obs": observatory }
            data_map_s = {"h": 1, "d": 1, "z": 1, "f":1, "delay": dtime.seconds, "timestamp": datetime.date.today(), "res":"sec", "obs": observatory }
            insert_record(data_map_m)
            insert_record(data_map_s)
    except http.client.IncompleteRead:
        print("Incomplete Read, Something went wrong network side")

def process_data(data, regex, res, dtime, observatory):
    result = re.search(regex, data)
    data_regex_string = "(-?\\d{1,5}\\.\\d{2}\\s*){4}"
    data_regex = re.compile( data_regex_string )
    if result is None:
        print("regex not matched for", regex.pattern)
    else:
        data_result = re.search(data_regex, result.group() )
        data_points = data_result.group().split()
        data_map = dict()

        for point in range(len(data_points)):
            if data_points[point] == "99999.00":
                data_points[point] = 1
            else:
                data_points[point] = 0

        data_map["h"] = data_points[0]
        data_map["d"] = data_points[1]
        data_map["z"] = data_points[2]
        data_map["f"] = data_points[3]

        data_map["delay"] = dtime.seconds
        data_map["timestamp"] = datetime.date.today()
        data_map["res"] = res
        data_map["obs"] = observatory
        insert_record(data_map)
    
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

def insert_record(data_map):
    dbAdapter = runtimeConfigs["db"]
    dbAdapter.insert_geostat(data_map)


def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return days, hours, minutes, seconds

def make_data_list(res, delay, filter):
    return_list = []
    for obs in runtimeConfigs["observatories"]:
        data_set = runtimeConfigs["db"].get_stats(delay.seconds, res, obs, datetime.date.today()-filter)
        sum_count = 0
        sum_h = 0
        sum_d = 0
        sum_z = 0
        sum_f = 0
        for point in data_set:
            sum_h = sum_h + point["h_fail"]
            sum_d = sum_d + point["d_fail"]
            sum_z = sum_z + point["z_fail"]
            sum_f = sum_f + point["f_fail"]
            sum_count = sum_count + point["point_count"]
        stat_h = ((sum_count - sum_h)/sum_count)*100
        stat_d = ((sum_count - sum_d)/sum_count)*100
        stat_z = ((sum_count - sum_z)/sum_count)*100
        stat_f = ((sum_count - sum_f)/sum_count)*100
        return_list.append({"obs": obs, "delay": delay.seconds, "h": stat_h, "d": stat_d, "z": stat_z, "f": stat_f, "filter": filter.days})
    return return_list

def printTable():
    log = open(runtimeConfigs["html_file"], "w")
    header_file = open("head.html")
    header = header_file.read()
    log.write(header)
    header_file.close()
    uptime =  datetime.datetime.now() - runtimeConfigs["program_start"]

    days, hours, minutes, seconds = convert_timedelta(uptime)
    uptime2 = '{} day{}, {} hour{}, {} minute{}, {} second{}'.format(days, 's' if days != 1 else '', hours, 's' if hours != 1 else '', minutes, 's' if minutes != 1 else '', seconds, 's' if seconds != 1 else '')

    print_str = "<tr> <td>{}</td> <td>{:.2f}%</td> <td>{:.2f}%</td> <td>{:.2f}%</td> <td>{:.2f}%</td> </tr>\n"
    title_str = "<tr> <th>Observatory</th> <th>H</th> <th>D</th> <th>Z</th> <th>F</th> <th>Delay: {:2.0f} Minutes </th> </tr>\n"
    div_str = "<div class=\"delay{delay} delays {res} filter{filter}\">\n"
    filter_str = "<p> Average for last {} days </p>\n"
    filter_str_2 = "<p> Average for today </p>\n"

    log.write("<div class=\"select_box\">\n<select onchange=\"showTime(this)\">\n")
    option_str = "<option value=\"{0}\">{0} Minute(s)</option>\n"
    for d in runtimeConfigs["delays"]:
        if int(d.seconds/60) == 10:
            log.write("<option selected=\"selected\" value=\"10\"> 10 Minute(s) </option>\n")
        else:
            log.write(option_str.format(str(int(d.seconds/60))))
    log.write("</select>\n</div>\n")

    # This sections prints out the tables for Seconds Data
    log.write("<h2> Second Data </h2>\n")
    for d in runtimeConfigs["delays"]:
        for f in runtimeConfigs["filters"]:
            log.write(div_str.format( delay = int(d.seconds/60), res = "second", filter = f) )
            if f.days == 0:
                log.write(filter_str_2)
            else:
                log.write(filter_str.format(f.days))
            log.write( "<table>\n")
            all_stats = make_data_list( "sec", d, f )
            log.write( title_str.format( d.seconds/60) )
            for item in all_stats:
                log.write(print_str.format(item["obs"], item["h"], item["d"], item["z"], item["f"]))
            log.write("</table>\n")
            log.write("</div>\n")

    # This section prints out the tables for Minute Data
    log.write("<h2> Minute Data </h2>\n")
    for d in runtimeConfigs["delays"]:
        for f in runtimeConfigs["filters"]:
            log.write( div_str.format( delay = int(d.seconds/60), res = "minute", filter = f) )
            log.write( "<table>\n")
            if f.days == 0:
                log.write(filter_str_2)
            else:
                log.write(filter_str.format(f.days))
            all_stats = make_data_list( "min", d, f )
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
runtimeConfigs["db"].delete_old(datetime.datetime.utcnow()-datetime.timedelta(days=30))
for obs in runtimeConfigs["observatories"]:
    start_http_session( obs )

printTable()
try:
    subprocess.call(["rsync", "-avz", "-e", "ssh -i maguser.key", "statistics.html", "maguser@magweb1.cr.usgs.gov:/webinput/vhosts/magweb/htdocs/data/"])
except FileNotFoundError as e:
    print("Error calling rsync", e)

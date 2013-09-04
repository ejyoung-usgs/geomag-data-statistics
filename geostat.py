import urllib.request
import argparse
import datetime

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
    request = urllib.request.urlopen(url)
    magdata = open("magdata.sec", "w")
    #print ( request.read() )
    magfile = request.read().decode("utf-8")
    magfile.splitlines()
    for line in magfile:
        line = line.strip()
        magdata.write(line+"\n")
    #magdile = request.split()
    #SSfor x in magfile
    
runtimeConfigs = setupEnv()
requestString = "{url}/{observatory}/{type}/{file}"

#Make dynamic later
start_http_session( requestString.format( url = runtimeConfigs["url"], observatory = runtimeConfigs["observatory"], type = "OneMinute", file="frd20130402vmin.min") )
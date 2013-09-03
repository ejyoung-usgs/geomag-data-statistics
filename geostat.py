import urllib
import argparse
import datetime

def setupEnv():
    argParser = argparse.ArgumentParser(description = "Gather information from Geomag HTTP site")
    argParser.add_argument("observatory", help = "Observatory to gather data on")
    args = argParser.parse_args();
    
    configs = dict()
    
    ## Setup all runtime configurations here ##
    configs["observatory"] = args.observatory
    configs["url"] = "http://magweb.cr.usgs.gov/data/magnetometer/"
    return configs
    
def start_http_session( url ):
    
    
runtimeConfigs = setupEnv()
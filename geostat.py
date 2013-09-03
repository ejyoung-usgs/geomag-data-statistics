import http.client
import argparse
import datetime

def setupEnv():
    argParser = argparse.ArgumentParser(description = "Gather information from Geomag HTTP site")
    argParser.add_argument("observatory", help = "Observatory to gather data on")
    args = argParser.parse_args();
    
    configs = dict()
    configs["observatory"] = args.observatory
    return configs
    
    
runtimeConfigs = setupEnv()
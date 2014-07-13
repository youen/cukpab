#-*- coding:utf-8 -*-
'''
Created on 11 juil. 2014

@author: youen

'''

import argparse
import ConfigParser
import os.path
import simplejson
import sys
import logging

def readConfigFile(specifyFile = None):
    """
    Read configuration files from ~/config/cukpab 
    """
    config_files = [os.path.expanduser('~/.config/cukpab')]
    if specifyFile:
        config_files.insert(0, specifyFile)
        
    config = ConfigParser.SafeConfigParser()
    config.read(config_files)
    
    try :
        defaults_config_file = dict(config.items("Defaults"))
        defaults_config_file["excludes"] = simplejson.loads(defaults_config_file.get("excludes", "[]"))
        defaults_config_file["mongo-port"] = int(defaults_config_file.get("mongo-port", 27017))
    except ConfigParser.NoSectionError:
        return {}
    
    return defaults_config_file

def configureLog():
   
    logger = logging.getLogger('cukpab')
    
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('backup.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    #logger.addHandler(fh)
    logger.addHandler(ch)
    
def getConfiguration():
    """
    Actions :
    
        * backup : Look for modified files and save them in a new incremental tar and compute their sha1sum
        * check : Check the sha1sum for each files in the backup
        * restore : Restore the last backup
         
    """
    reload(sys).setdefaultencoding("ascii")

    conf_parser = argparse.ArgumentParser(
        # Turn off help, so we print all options in response to -h
            add_help=False
            )
    conf_parser.add_argument("-c", "--conf_file",
                             help="Specify config file", metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()
    defaults = {
        "source" : os.path.expanduser("~"),
        "excludes" : [],
        "mongo-host" : "localhost",
        "mongo-port" : 27017,
        "mongo-database" : "cuckpab"
        }
    
    
    defaults.update(readConfigFile(args.conf_file))

     
    # Don't surpress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        # Inherit options from config_parser
        parents=[conf_parser],
        # print script description with -h/--help
        description=getConfiguration.__doc__,
        # Don't mess with format of description
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    parser.set_defaults(**defaults)
    parser.add_argument("--restored", help="Directory where backup will be restored")
    parser.add_argument("--source", help="Directory to backup")
    parser.add_argument("--backup", help="Directory to store the backup")
    parser.add_argument("--excludes", help="Excludes pattern", nargs="*")
    parser.add_argument("command", choices=['backup', 'check', 'restore', 'log'], help="Command to execute with the backup")
    args = parser.parse_args(remaining_argv)
    
    if args.command == 'restore' and args.restored is None:
            parser.error('restored is required to restored a backup.')
    return args
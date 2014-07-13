#-*- coding:utf-8 -*-
import cukpab
import logging
import pprint
import cukpab.configuration
import sys

def check(config):
    """
    check the backup
    """
    backup = cukpab.Backup.load(config)
    
    for increment in backup.ListIncrements():
        print increment.computeSHA1()
    

def log(config):
    backup = cukpab.Backup.load(config)
    
    for increment in backup.ListIncrements():
        print increment.timestamp


def backup(config):
    backup = cukpab.Backup.load(config)
    
    backup.backup()
    
def restore(config):
    backup = cukpab.Backup.load(config)
    
    backup.restore(config.restored)

def main():
    commands = {
               "check" : check,
               "log" : log,
               "backup" : backup,
               "restore" : restore
               }
    config = cukpab.configuration.getConfiguration()
    
    cukpab.configuration.configureLog()
    
    commands.get(config.command)(config)
    exit()
        

#     stats =  backup.getStats(hour=True, minute=True)['result'][0]
#     pprint.pprint(stats)
#     pprint.pprint( stats['avg'] / (1024 *1024) * stats['count'])
    #backup.watchStat()
#    backup.backup()
#    backup.restore("/tmp/restored")
  
if __name__ == '__main__' :

    main()  
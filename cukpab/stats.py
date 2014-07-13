#!/usr/bin/python
#-*- coding:utf-8 -*-
'''
Created on 7 juil. 2014

@author: youen
'''


import pyinotify
import os
import datetime
import logging
from pymongo.mongo_client import MongoClient

logger = logging.getLogger(__name__)




class StatEventHandler(pyinotify.ProcessEvent):
    
    def __init__(self, mongodb):
        
        
        self.db =  MongoClient(mongodb['host'], mongodb['port'])[mongodb['database']]


    def process_IN_MODIFY(self, event):

        if event.dir:
            print "Modification de répertoire :", event.pathname
        else:
            try :
                stat = os.stat(event.pathname)
                size = stat.st_size
                timestamp = datetime.datetime.fromtimestamp(stat.st_mtime)
                print "Modification de fichier :", event.pathname, size, timestamp
                self.db.events.insert({
                                       'path' : event.pathname,
                                       'size' : size,
                                       'timestamp' : timestamp
                                       
                                       })
            except OSError :
                logger.info("path %s doesn't exist anymore"%event.pathname)
            
class Statistics(object):
    """
    Statistics backup utilities.
    """
    
    def watchStat(self):
        """
        watch the directory for statistics
        """
        wm = pyinotify.WatchManager() # Watch Manager
        mask = pyinotify.IN_MOVED_TO | pyinotify.IN_CREATE | pyinotify.IN_MODIFY   # watched events
        
        handler = StatEventHandler(self.mongoDB)
        notifier = pyinotify.Notifier(wm, handler)
        wdd = wm.add_watch(self.srcDir, mask, rec=True, auto_add=True)
        
        notifier.loop()
        
    def getStats(self, **interval_parameters):
        db =  MongoClient(self.mongoDB['host'], self.mongoDB['port'])[self.mongoDB['database']]
        #year=True , month=True, day=True, hour=True, minute = True
        interval = {}
        
        for attrib in ('year', 'month', 'dayOfMonth', 'hour', 'minute'):
            if interval_parameters.get(attrib, True) : 
                interval[attrib] = {'$'+attrib : '$timestamp'}
            
        

        query = [
            {   
                "$group": {'_id' : {'path': '$path' , 'interval' :interval }, "max_size":{"$max":'$size'}}
            },                 
            {   
                "$group": {'_id' : '$_id.interval', "total_size":{"$sum":'$max_size'}}
            },
            {
                "$group": {'_id' : None,  'count' : { '$sum' : 1}, 'avg' : { '$avg' : '$total_size'}  }
            }
        ]        
        return db.events.aggregate(query)
            
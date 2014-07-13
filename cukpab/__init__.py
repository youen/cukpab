#-*- coding:utf-8 -*-
'''
Created on 6 juil. 2014

@author: youen
'''
import os
import subprocess
from datetime import datetime
import simplejson
import logging
from itertools import groupby
from cukpab.stats import StatEventHandler
import pyinotify
from pymongo.mongo_client import MongoClient
import codecs
from fileinput import filename

logger = logging.getLogger(__name__)


class Backup(object):
    '''
    A Backup configuration
    '''
  
    listedIncrementalFileName = 'save.list'
    prefix = 'backup'
    dateFormat = '%Y-%m-%d_%H_%M_%S'
    max_size = '100m'
    excludesFileName = 'excludes.txt'
    
    
    def __init__(self, srcDir, backupDir, excludes, mongodb = None):
        '''
        src : Fullpath to the directory to backup
        '''
        self.srcDir = srcDir
        self.backupDir = backupDir
        self.mongoDB = mongodb
        self.excludes = excludes 
        self._timestamp = None

    def backup(self):
        """
        Run script to backup with tar --create --listed-incremental
        """
        
        Increment(self).create()
        
    
    def ListIncrements(self):
        """
        Return the list of increments
        """
        result = []
        for group, filenames in groupby(self.listBackupFile(), lambda x:x[:-2]) :
            timestamp = os.path.basename(list(filenames)[0]).split('_',1)[1].split('.')[0]
            result.append(Increment(self, timestamp))
        return result       
        
    @property
    def listedIncremental(self):
        """
        return the file use by tar
        """
        
        return os.path.join(self.backupDir, self.listedIncrementalFileName)


    @property
    def excludesFile(self):
        """
        return the file use by tar
        """
        
        return os.path.join(self.backupDir, self.excludesFileName)

    
    def listBackupFile(self):
        """
        List all backup files in the backup dir ordered by date
        """
        return sorted(os.path.join(self.backupDir, filename) for filename in os.listdir(self.backupDir) if filename.startswith(self.prefix))
    
    def restore(self, outputDir = None):
        """
        Restore the backup to the src dir or to a specific dir
        """
        if outputDir is None:
            outputDir = self.srcDir
            
        for increment in self.ListIncrements():
            increment.restore(outputDir)
        

        
            
            
    @property
    def componentsPath(self):
        """
        Compute the number of components in the srcDir path
        """
        nbComponents = 0
        path = self.srcDir
        while 1:
            parts = os.path.split(path)
            if parts[0] == path:  # sentinel for absolute paths
                break
            elif parts[1] == path: # sentinel for relative paths
                break
            else:
                path = parts[0]
                nbComponents += 1
        return nbComponents
    

        
    @classmethod
    def load(cls, config):
        """
        Create an Backup object from  configuration
        """
        return Backup(config.source, config.backup, config.excludes,  {})
        

class Increment(object):
    """
    A backup increment aka a tar file
    """    
    sha1FileNamePrefix = 'sha1sum'
    
    indexFileFileNamePrefix = 'index'
    
    def __init__(self, backup, timestamp =None):
        self.backup = backup
        if timestamp:
            self.timestamp = timestamp
        else :
            self.timestamp = self.getTimestamp()


    def create(self):
        """
        create a Tar increment file
        """
        filename = self.targetFile
        logger.info("generate backup file %s"%filename)
        with  codecs.open(self.backup.excludesFile, 'w', 'utf-8')  as f:
            for pattern in self.backup.excludes:
                print pattern
                f.write(pattern+ u'\n')
                
        tar_cmd = ["tar", "--exclude-vcs", "--create", "-C",  self.backup.srcDir,\
                   "--exclude-from=%s"%self.backup.excludesFile,\
                   "--listed-incremental", self.backup.listedIncremental,\
                   '--bzip', '--verbose', '--index-file', self.indexFile ,"."]
        
        split_cmd = ["split", "-d", "-b", self.backup.max_size, "-", filename + "."]
        
        logger.debug(" ".join(tar_cmd) + ' | ' + " ".join(split_cmd))
        tar =   subprocess.Popen(tar_cmd, 
                        stdout=subprocess.PIPE,
                        )
        split = subprocess.Popen(split_cmd,
                        stdin=tar.stdout,
                        stdout=subprocess.PIPE,
                        )
        
        for line in split.stdout:
            print line
            

        logger.info('Compute sha1 checksum for new files')
        self.computeSHA1()
        
    def restore(self, outputDir):
        
        tar_cmd = ["tar", "--extract","-C",  outputDir,  "--listed-incremental", self.backup.listedIncremental, '--bzip', '--']
        
        cat_cmd = ["cat"] + list(self.splitedFiles)
        logger.debug(" ".join(cat_cmd) + ' | ' + " ".join(tar_cmd))

        cat =   subprocess.Popen(cat_cmd, 
                        stdout=subprocess.PIPE,
                        )
        tar = subprocess.Popen(tar_cmd,
                        stdin=cat.stdout,
                        stdout=subprocess.PIPE,
                        )
                        
    @property
    def splitedFiles(self):
        """
        Liste splited files for this increment
        """
        return [filename for filename in self.backup.listBackupFile() if self.timestamp in filename]
    

    @property
    def indexFile(self):
        """
        return the filename to index files
        """
        
        return os.path.join(self.backup.backupDir, "%s_%s.txt"%(self.indexFileFileNamePrefix, self.timestamp))

    def getTimestamp(self):
        """
        Compute the current timestamp 
        """
        
        return datetime.now().strftime(self.backup.dateFormat)
    
    @property
    def targetFile(self):
        """
        Compute an unique name for a target file
        """

        return os.path.join(self.backup.backupDir,"%s_%s.tar.bz"%(self.backup.prefix, self.timestamp))
 
    
    def remove(self):
        """
        remove this increment
        """
        
        for filename in os.listdir(self.backup.backupDir) :
            if self.timestamp in filename:
                filepath = os.path.join(self.backup.backupDir, filename)
                logger.debug('rm %s'%filepath)
                os.remove(filepath)
            
    def checkEmpty(self):
        """
        Check if there is files in the last increment 
        """
        showFile = False
        
        with open(self.indexFile) as indexFile :
            for line in indexFile:
                filename = line[:-1]# last \n
                path = os.path.join(self.srcDir,filename) 
                showFile = os.path.isfile(path)

                if showFile:
                    return False
                
        return True


    @property
    def sha1File(self):
        """
        retrun the filename to the sha1 checksums files
        """
        return os.path.join(self.backup.backupDir, "%s_%s.txt"%(self.sha1FileNamePrefix, self.timestamp))
        
    
    
    def computeSHA1(self):
        """
        Compute the SHA1 check sum for new files
        """
        with open(self.sha1File,'w') as sha1File :
            with open(self.indexFile) as indexFile :
                for line in indexFile:
                    filename = line[:-1]# last \n
                    path = os.path.join(self.backup.srcDir,filename)   
                    if os.path.isfile(path):
                        sha1sum_cmd = ["sha1sum", path]
                        logger.debug(" ".join(sha1sum_cmd) )

                        sha1sum = subprocess.Popen(sha1sum_cmd, stdout=subprocess.PIPE).communicate()[0][:-1].split(' ')[0]
                        sha1File.write('%s\t%s\n'%(sha1sum, filename))
        
        
import tweepy
import json
import sys
import time
import logging.config
import os
from pathlib import Path

class Io:

    """
    Io class takes care of the input/output duties (reading and writing to the disk).
    """
    
    def __init__(self, ID, json_read_file, json_write_file, filter_output, is_filter = False):
        """
        Initialize the object.
        """
        self.ID = ID
        self.logger          = logging.getLogger("IO {0}".format(self.ID))
        self.filter_output   = filter_output
        self.is_filter       = is_filter
        self.json_write_file = json_write_file
        self.json_read_file  = json_read_file
        self.c_saved         = 0
        self.daily_c_saved   = 0
        self.stime           = time.time()
        self.inputs          = self.get_input()
        self.cities          = {}

    def _read_csv(self):
        with open(self.json_read_file, "r") as f:
            ids = list(f.read().splitlines())
            self.logger.debug("IO {0}: input file  {1} successfully read. Following keywords / userids initialized:".format(self.ID, self.json_read_file))
            self.logger.debug(ids)
        return ids
            
    def instantiate_file(self, filepath):
        if not Path(filepath).is_file():
            self.daily_c_saved = 0
            with open(filepath, 'w+') as f: 
                pass

    def get_input(self):
        """
        reads lines from a file and creates a list object
        """
        self.logger.info("Reading user_ids.")
        try:
            self.inputs = list(set(self._read_csv()))
            return self.inputs
        except Exception as ex:
            self.logger.error("Error while reading user_ids: %s",repr(ex))
            self.logger.info("Exiting program.")
            exit()

    def update(self):
        ids = self._read_csv()
        if set(ids) == set(self.inputs):
            return False
        self.inputs = list(set(ids))
        return True

    def save_status(self, data, jsonfilename):
        for at_i in range(3):        
            try: 
                f = open(jsonfilename, "a", encoding='utf-8', newline='')
                f.write(json.dumps(data._json))
                f.write('\n')
                self.c_saved += 1
                self.daily_c_saved += 1
                self.logger.debug('Tweet saved, total count: {}'.format(self.c_saved))
                return True
            except Exception as ex:
                self.logger.error("Save was unsuccessful:", ex)
                time.sleep(0.5)
        return False

    def save_uid(self, userid, name):
        # If separate filenames, then name accordingly
        fname = None
        if len(self.filter_output) == len(self.cities.keys()):
            for f,k in zip(filter_output, self.cities.keys()):
                if k == name:
                    fname = f
        # If not, then handle as common folder
        else:
            fname = '{0}/{1}.csv'.format(self.filter_output[0], name) 

        self.cities[name] += 1 
        for _ in range(3):        
            try: 
                f = open(fname, "a+", encoding='utf-8', newline='')
                f.write(str(userid))
                f.write('\n')
                self.logger.debug('UserID {0} saved to file: {1}'.format(userid, fname))
                if self.c_saved % 10000 == 0: 
                    self.logger.info('{0} tweets collected.'.format(self.c_saved))
                return True
            except Exception as ex:
                self.logger.error("Save was unsuccessful:", ex)
                time.sleep(0.5)
        return False
            
    def set_filename(self, filename):
        self.jsonfilename = filename

    def initialize_city_counts(self, cities):
        for city in cities:
            self.cities[city] = 0
        

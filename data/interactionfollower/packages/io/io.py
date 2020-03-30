import tweepy
import json
import sys
import time
import logging
import os
from pathlib import Path

class Io:

    """
    Io class takes care of the input/output duties (reading and writing to the disk).
    ...

    Attributes
    ----------
    json_read_file : str
        Path to the json-data file for reading the original tweets.
    json_write_file : str
        Path to the json-data file for saving the downloaded replies.
    queried_path : str
        Path to the file containing the list of already queried tweet ids.
    
    """
    
    def __init__(self, ID, json_read_file, json_write_file):
        """
        Initialize the object.
        """
        self.ID = ID
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
            logging.debug("IO {0}: user ids successfully read for the input file {0}. They are:".format(self.ID, self.json_read_file))
            logging.debug(ids)
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
        logging.info("Reading user_ids.")
        try:
            self.inputs = list(set(self._read_csv()))
            return self.inputs
        except Exception as ex:
            logging.error("Error while reading user_ids: %s",repr(ex))
            logging.info("Exiting program.")
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
                f.write((str(data._json)))
                f.write('\n')
                self.c_saved += 1
                self.daily_c_saved += 1
                logging.debug('Tweet saved, total count: {}'.format(self.c_saved))
                return True
            except Exception as ex:
                logging.error("Save was unsuccessful:", ex)
                time.sleep(0.5)
        return False

    def save_uid(self, userid, W):
        fname = '{0}.csv'.format(W)
        if W not in self.cities.keys:
            self.cities[W] = 1
        else:
            self.cities[W] += 1
            
        for at_i in range(3):        
            try: 
                f = open(fname, "a", encoding='utf-8', newline='')
                f.write(userid)
                f.write('\n')
                logging.info('UserID {0} saved to file: {1}'.format(userid, fname))
                return True
            except Exception as ex:
                logging.error("Save was unsuccessful:", ex)
                time.sleep(0.5)
        return False

    def set_filename(self, filename):
        self.jsonfilename = filename

        
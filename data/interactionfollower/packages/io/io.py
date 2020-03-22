import tweepy
import json
import sys
import time
import logging
import os

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
        self.stime           = time.time()
        self.ids             = self.get_userids()

    def _read_userids(self):
        with open(self.json_read_file, "r") as f:
            ids = list(f.read().splitlines())
            logging.debug("IO {0}: user ids successfully read for the input file {0}. They are:".format(self.ID, self.json_read_file))
            logging.debug(ids)
        return ids
            
    def instantiate_file(self, filepath):
        with open(filepath, 'w+') as f: 
            pass

    def get_userids(self):
        """
        reads userids from a file and creates a list object
        """
        logging.info("Reading user_ids.")
        try:
            self.ids = list(set(self._read_userids()))
            return self.ids
        except Exception as ex:
            logging.error("Error while reading user_ids: %s",repr(ex))
            logging.info("Exiting program.")
            exit()

    def update(self):
        ids = self._read_userids()
        if set(ids) == set(self.ids):
            return False
        self.ids = list(set(ids))
        return True

    def save(self, data, jsonfilename):
        for at_i in range(3):        
            try: 
                f = open(jsonfilename, "a", encoding='utf-8', newline='')
                f.write(data)
                self.c_saved += 1
                logging.debug('Tweet saved, total count: {}'.format(self.c_saved))
                return True
            except Exception as ex:
                logging.error("Save was unsuccessful:", ex)
                time.sleep(0.5)
        return False

        
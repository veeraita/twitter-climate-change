import tweepy
import json
import sys
import time
import logging
import os

class Io:

    """
    Io class takes care of the input/output duties (reading and writing to the disk).
    It is able to read large files in batches by using generators.

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
    
    def __init__(self, json_read_file, json_write_file, queried_path):
        """
        Initialize the object.
        """
        self.__QUERIED_SIZE  = 5
        self.__BLOCK_SIZE    = 20

        self.json_read_file  = open(json_read_file, 'r')
        self.json_write_file = open(json_write_file, 'a')
        self.queried_path    = queried_path 
        self.process_count   = 0
        self.__query_count   = 0

        # If file doesn't exist, create new file to the same path
        if not os.path.exists(queried_path):
            open(queried_path, 'w').close()
            self.queried = []
        else:
            self.__load_queried_set(queried_path)
            
    def save(self, tweets):
        """
        Dumps tweets to the file in json format
        """
        try:
            data = "".join([str(tweet) + "\n" for tweet in tweets])
            if len(data) > 1:
                self.json_write_file.write(data)
                logging.info("Saved tweets successfully.")
            return True

        except Exception as ex:
            logging.error("Save was unsuccessful:", ex)
            return False

    def __read_next_block(self):
        """
        Read a batch of BLOCK_SIZE in generator mode from the file.
        Should be able to process large files in memory efficient way.
        
        return: (list) list of tweets
        """
        block = []
        i = 0
        for line in self.json_read_file:
            block.append(line)
            i += 1
            if i % self.__BLOCK_SIZE == 0:
                yield block
                self.process_count += self.__BLOCK_SIZE
                i = 0
                block = []

        if block:
            yield block
            self.process_count += i

    def __load_queried_set(self, path):
        try:
            self.queried = [line.strip() for line in open(path, 'r')]
            logging.info('Loaded queried set successfully.')
            logging.debug('Set contains: {0} ids'.format(len(self.queried)))
        except:
            logging.error('Error while reading the queried set file.')

    def __save_queried_set(self):
        """Save the non-empty intersection of original set and current set."""
        with open(self.queried_path, 'w') as queried_file:
            #ne_inters = set(self.queried) - set(line.strip() for line in queried_file)
            queried_file.write('\n'.join([id_str for id_str in self.queried]))
        
        logging.info("Saved the queried set to {0}.".format(self.queried_path))

    def next_tweet(self):
        for block in self.__read_next_block():
            logging.debug('Tweet generator object iterated.')
            for tweet in block:
                yield json.loads(tweet)
            
            logging.debug('Tweet generator object empty, calling next block.') 

    def add_queried(self, tweet_id):
        """Add tweet to queried set, store only periodically to save time on slow IO requests."""    
        self.__query_count += 1
        self.queried.append(tweet_id)
        
        if self.__query_count == self.__QUERIED_SIZE:
            logging.info("Saving the queried set.") 
            self.__save_queried_set()
            self.__query_count = 0

    def get_queried(self):
        return self.queried
import tweepy
import sys
import time
import json
import logging
from datetime import datetime, timedelta
import string

class Follower(tweepy.StreamListener):
    """
    Class for implementing the Streaming API user id following.
    Inherits Tweepy's Streamlistener and overwrites some of the
    original methods.
    """
    def __init__(self, io, filter_cities = False):
        # Create new json dump file every day at certain hour - Houston 3am = UTC 9am
        date_now = datetime.utcnow().strftime("%d/%m/%Y")
        self.filetime = datetime.strptime("{} 09:00".format(date_now), "%d/%m/%Y %H:%M") 
        self.io = io
        self.reconnection_attempts  = 0
        self.reconnections_limit    = 9
        self.last_reconnection_time = time.time()
        self._filter_cities         = filter_cities
        self.filter_words           = ['philadelphia','houston','chicago']
        self._update_file_name()
        super(Follower,self).__init__()
        logging.info("Follower {0} initialized successfully.".format(self.io.ID))

    def _update_file_name(self):
        without_ft = self.io.json_write_file.replace(".json",'')
        ftime_strf = self.filetime.strftime("%d-%m-%Y")
        new_filename = "{0}_{1}.json".format(without_ft, ftime_strf)
        self.io.set_filename(new_filename)
        self.io.instantiate_file(new_filename)
        
    def _set_new_date(self):
        date_now = datetime.utcnow().strftime("%d/%m/%Y")
        self.filetime = datetime.strptime("{} 09:00".format(date_now), "%d/%m/%Y %H:%M")

    def on_status(self,data):
        """
        Dumps statuses (ignores other update types) to a file in json format
        """
        # reset reconnection attempts
        self.reconnection_attempts = 0
        timenow   = datetime.utcnow()
        offset    = timenow - self.filetime
        save_flag = True

        if offset.days >= 1: # time to create a new file
            self._set_new_date()
            self._update_file_name()

        if self._filter_cities:
            save_flag = self._filter_and_save(data, save_flag)

        if not self.io.save_status(data, self.io.jsonfilename) or not save_flag:
            logging.error("Can't write to file, check available disk space and availability of the file {0}.".format(self.io.jsonfilename))
            logging.error("Disconnecting..")
            raise

    def _filter_and_save(self,data, save_flag):    
        try:
            user_loc = data.user.location.lower()
        
            for W in self.filter_words:
                if W in user_loc:
                    if not self.io.save_uid(data.user.id_str, W):
                        save_flag = False
                        
                    status_fname = self.io.jsonfilename.replace('.json', '_{0}.json'.format(W))
                    if not self.io.save_status(data, status_fname):
                        save_flag = False
            
            return save_flag
        except Exception as ex:
            return save_flag

    def on_limit(self, track):
        """Called when a limitation notice arrives"""
        logging.info('Stream {0} LIMIT notice.'.format(self.io.ID))
        return

    def on_error(self, status_code):
        """
        twitter recommends immediate reconnection attempt with exponential wait pattern>
        1. attempt to reconnect
        2. wait 1,2,4,8, limit seconds
        3. if limit exceeded, terminate program and notify user

        returning True reconnects the stream

        if disconnection is due to exceeded rate limit, 
        reset shoulf be waited for or the app might get blacklisted
        (API should take care of this)

        http://docs.tweepy.org/en/latest/streaming_how_to.html
        """
        logging.error("Encountered streaming error: %s",repr(status_code))
        logging.info("Reconnection attempts: %d",(self.reconnection_attempts))

        waittime = 2**self.reconnection_attempts
        if status_code in [420,429]: # rate limit exceeded
            logging.warning("Rate limit exceeded.")
            waittime = 60*15
        # if there is some other error (internet connection etc)
        if time.time() >= self.last_reconnection_time + 60*60*2:
            # null counter if two hours since last reconnection
            self.reconnection_attempts = 0
            logging.info("Over two hours since the last reconnection. Nullified reconnection attempt count.")
        self._wait(waittime)
        return True

    def _wait(self, waittime):
        logging.info("Waiting %d s and reconnecting.",waittime)
        time.sleep(waittime)
        self.reconnection_attempts += 1
        self.last_reconnection_time = time.time()
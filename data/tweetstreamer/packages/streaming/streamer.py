import tweepy
import sys
import time
import json
import logging
from datetime import datetime, timedelta
import string


class Streamer(tweepy.StreamListener):
    def __init__(self, json_dump):
        """
        define output files here
        """
        # create new json dump file every day at certain hour
        #self.newfiletime = time0.replace(day=x.day, hour=1, minute=0, second=0, microsecond=0) + timedelta(days=1)
        date_now = datetime.utcnow().strftime("%d/%m/%Y")
        self.filetime = datetime.strptime("{} 09:00".format(date_now), "%d/%m/%Y %H:%M") # Houston 3am = UTC 9am 

        # Gets or creates a logger
        # self.logger = logging.getLogger(__name__) 
        # self.logger.setLevel(logging.INFO) 
        # add file handler to logger
        # self.logger.addHandler(log_file_handler)
        # self.splittimeperiod = time
        try:
            self.json_dump = json_dump
            self.jsonfilename = "{0}_{1}.json".format(self.json_dump.replace(".json",""), str(self.filetime.strftime("%d-%m-%Y")))

            with open(self.jsonfilename, 'w+') as f:
                #create new file
                pass
            self.reconnection_attempts = 0 #count reconnection attempts
            self.last_reconnection_time = time.time()
            self.reconnections_limit = 9
            super(Streamer,self).__init__()
            #successfull initialization!
            logging.info("Streamer initialized successfully.")
        except Exception as ex:
            logging.error("Error: %s. Exiting program.",repr(ex))
            exit()

    def set_new_date():
        date_now = datetime.utcnow().strftime("&d/%m/%Y")
        self.filetime = datetime.strptime("{} 09:00".format(date_now), "%m/%j/%y %H:%M")

    def on_data(self,data):
        """
        Dumps everything to a file in json format
        """
        #reset reconnection attempts
        self.reconnection_attempts = 0

        timenow = datetime.utcnow()
        offset  = timenow - self.filetime

        if offset.days >= 1: #time to create new file
            self.set_new_date()

            self.jsonfilename = "{0}_{1}.json".format(self.json_dump.replace(".json",''), self.filetime.strftime("%d-%m-%Y"))

            with open(self.jsonfilename, 'w+') as f:
                #create new file
                pass

        with open(self.jsonfilename, "a", encoding='utf-8', newline='') as f:
            f.write(data)
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
            # wait until rate limit is reset
            # NOTE API (created by credentialhandler) should take care of rate limits automatically
            self.logger.warning("Rate limit exceeded.")
            waittime = 60*15
        # if there is some other error (internet connectione etc)
        if time.time() >= self.last_reconnection_time + 60*60*2:
            # null counter if two hours since last reconnection
            self.reconnection_attempts = 0
            logging.info("Over two hours since the last reconnection. Nullified reconnection attempt count.")

        logging.info("Waiting %d s and reconnecting.",waittime)
        time.sleep(waittime)
        self.reconnection_attempts += 1
        self.last_reconnection_time = time.time()
        return True
        #else:
        #    print("Reconnection attempts limit exceeded.")
        #    print("Terminating.")
        #    exit()


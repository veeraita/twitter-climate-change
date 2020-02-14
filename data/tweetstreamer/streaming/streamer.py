import tweepy
import sys
import time

class Streamer(tweepy.StreamListener):
    def __init__(self, json_dump, csv_out):
        """
        define output files here
        """
        self.json_dump = json_dump
        self.csv_out = csv_out
        self.reconnection_attempts = 0 #count reconnection attempts
        self.reconnections_limit = 9
        super(Streamer,self).__init__()
    def on_data(self,data):
        """
        Dumps everything to a file in json format
        """
        with open(self.json_dump, "ab") as f:
            f.write(data)
    def on_status(self, status):
        print(status.id_str)
        # if "retweeted_status" attribute exists, flag this tweet as a retweet.
        is_retweet = hasattr(status, "retweeted_status")

        # check if text has been truncated
        if hasattr(status,"extended_tweet"):
            text = status.extended_tweet["full_text"]
        else:
            text = status.text

        # check if this is a quote tweet.
        is_quote = hasattr(status, "quoted_status")
        quoted_text = ""
        if is_quote:
            # check if quoted tweet's text has been truncated before recording it
            if hasattr(status.quoted_status,"extended_tweet"):
                quoted_text = status.quoted_status.extended_tweet["full_text"]
            else:
                quoted_text = status.quoted_status.text

        # remove characters that might cause problems with csv encoding
        remove_characters = [",","\n"]
        for c in remove_characters:
            text.replace(c," ")
            quoted_text.replace(c, " ")

        with open(self.csv_out, "a", encoding='utf-8') as f:
            f.write("%s,%s,%s,%s,%s,%s\n" % (status.created_at,status.user.screen_name,is_retweet,is_quote,text,quoted_text))

    def on_error(self, status_code):
        """
        twitter recommends immediate reconnection attempt with exponential wait pattern>
        1. attempt to reconnect
        2. wait 1,2,4,8, limit seconds
        3. if limit exceeded, terminate program and notify user

        returning True reconnects the stream

        if disconnection is due to exceeded rate limit, 
        reset shoulf be waited for or the app might get blacklisted

        http://docs.tweepy.org/en/latest/streaming_how_to.html
        """
        print("Encountered streaming error (", status_code, ")")
        print(self.reconnection_attempts," reconnection attempts.")
        if status_code in [420,429]: # rate limit exceeded
            # wait until rate limit is reset

+

        elif self.reconnection_attempts < self.reconnections_limit:
            
            wait_time = 2**self.reconnection_attempts
            print("Waiting ",wait_time, "s and reconnecting.")
            time.sleep(wait_time)
            return True
        else:
            print("Reconnection attempts limit exceeded.")
            print("Terminating.")
            exit

        sys.exit()


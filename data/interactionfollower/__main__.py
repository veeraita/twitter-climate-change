import sys
import tweepy
import time
import logging

from packages.credentials import CredentialHandler
from packages.following import Follower
from packages.settings import Settings
from packages.statsmodule import StatsModule
from packages.io import Io

def input_interval():
    while True:
        try:
            return int(input('Input desired update interval (minutes) for userids >> '))
        except:
            print('Input not correct, please re-enter.')

def initialize(sts):
    # initialize required modules
    logging.info("Initializing modules...")
    streams, ios, chs, followers = [], [], [], []
    n_range = range(1,sts.n_inst+1)

    # initialize io modules
    for i,inp,outp in zip(n_range, sts.in_fps, sts.out_fps):
        logging.debug('Initializing io module {0}...'.format(i))
        ios.append(Io(i,inp,outp))
    
    # initialize credentialhandlers and decrypt (asks for passphrase)
    logging.info('Reading credentials')
    for i,cred_fp in zip(n_range, sts.cred_fps):
        logging.debug('Initializing CredentialHandler {0}...'.format(i)) 
        chs.append(CredentialHandler(cred_fp))        
    
    for i,ch in zip(n_range, chs):
        logging.info('Authenticating instance {0}...'.format(i))
        ch.authenticate()

    for cit,inp,outp,io in zip(sts.filter_cities,sts.in_fps,sts.out_fps,ios):
        logging.debug('Initializing StreamListener {0}...'.format(i)) 
        filter_cities = True if cit == 'filter' else False
        followers.append(Follower(io, filter_cities))

    logging.info('Initializing streaming modules...')       
    for i,ch,follower in zip(n_range,chs,followers):
        logging.debug('Initializing Stream object {0}...'.format(i)) 
        stream = tweepy.Stream(auth=ch.get_auth(), listener=follower,tweet_mode='extended')
        streams.append(stream)
    
    return streams, ios, chs, followers

def main(args = None):
    """
    TweetStreamer

    Application for storing Twitter streaming data
    """
    print("AALTO LST TweetStreamer\n")
    if args is None:
        SETTINGS_FILENAME = sys.argv[1] #settings file name
    
    # Ask user to input update interval
    UPDATE_INTERVAL = input_interval()

    # Logging config
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
    
    # read settings file
    sts = Settings(SETTINGS_FILENAME)
    
    # Initialize objects
    streams, ios, chs, followers = initialize(sts)
    time.sleep(0.2)
    stats = StatsModule(ios, UPDATE_INTERVAL)
    
    # app logic
    is_connecteds = [False for _ in range(len(streams))]
    logging.info('Opening {0} streams.'.format(len(streams)))
    while True:
        try:
            stime = time.time()

            mode_msg = None
            for mode,io,stream,i in zip(sts.modes, ios, streams, range(len(ios))):
                # start following
                if not is_connecteds[i]:
                    if mode == 'follow':
                        stream.filter(follow = io.inputs, languages=["en"], is_async=True)
                        mode_msg = 'ids followed'
                    else:
                        stream.filter(track = io.inputs, languages=["en"], is_async=True)    
                        mode_msg = 'keywords tracked'
                    logging.info('STREAM {0} successfully connected, number of {1}: {2}'.format(io.ID,mode_msg,len(io.inputs)))
                    is_connecteds[i] = True
            
            time.sleep(UPDATE_INTERVAL*60-(time.time() - stime))

            stats.log_stats()
                
            logging.info('Checking for new ids...')
            for io,stream,i in zip(ios,streams,range(len(ios))):
                if mode == 'follow':
                    if io.update():
                        logging.info('STREAM {0}: New user ids found. Disconnecting the stream.'.format(io.ID))
                        try:
                            stream.disconnect()
                            is_connecteds[i] = False
                        except Exception as ex:
                            logging.error('Disconnection failed.')
            
            if all(is_connecteds):
                logging.info('No new ids found.')

        except Exception as ex:
            waittime = 5
            logging.error('Error: %s',repr(ex))
            logging.info("Waiting %d seconds before attempting to open streams again",waittime)
            time.sleep(waittime)

# run application
if __name__ == "__main__":
    # define file handler and set formatter
    main()

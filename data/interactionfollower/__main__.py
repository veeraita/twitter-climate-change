import sys
import tweepy
import time
import logging

from packages.credentials import CredentialHandler
from packages.settings import Settings
from packages.following import Follower
from packages.io import Io

def input_interval():
    while True:
        try:
            return int(input('Input desired update interval (minutes) for userids >> '))
        except:
            print('Input not correct, please re-enter.')

def log_stats(ios):
    # Calculate run time so far
    m = 60
    h = m*60 
    d = h*24
    tweet_size_mb = 0.0072
    tweet_size_gb = tweet_size_mb/1000
    run_time = time.time() - ios[0].stime

    logging.info('\n\nUpdate interval saturated.')
    logging.info("Running time: {0:.0f} hours {1:.0f} minutes.".format(
                                                                run_time // h, 
                                                                (run_time % h) / m))
    for io in ios:
        logging.info("IO {0}: (STATS) ==================================".format(io.ID))
        logging.info("\t\t        Count: {0:>15.0f} tweets".format(io.c_saved))
        if run_time < d:
            logging.info("\t\t         Size: {0:>15.3f}     MB".format(tweet_size_mb*io.c_saved))
        else:
            logging.info("\t\t         Size: {0:>15.3f}     GB".format(tweet_size_gb*io.c_saved))
        logging.info("\t\tAvg data rate: {0:>15.0f} tweets / day".format(d*io.c_saved / (run_time)))
        logging.info("\t\t               {0:>15.0f} tweets / hour".format(h*io.c_saved / run_time))
        logging.info("\t\t               {0:>15.3f}     GB / day".format((d*io.c_saved*tweet_size_gb) / run_time))
        logging.info("\t\t               {0:>15.3f}     GB / hour".format((h*io.c_saved*tweet_size_gb) / run_time))
            

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

    for inp,outp,io in zip(sts.in_fps,sts.out_fps,ios):
        logging.debug('Initializing StreamListener {0}...'.format(i)) 
        followers.append(Follower(io))

    logging.info('Initializing streaming modules...')       
    for i,ch,follower in zip(n_range,chs,followers):
        logging.debug('Initializing Stream object {0}...'.format(i)) 
        stream = tweepy.Stream(auth=ch.get_auth(), listener=follower,tweet_mode='extended')
        streams.append(stream)
    
    return streams, ios, chs, followers

def main(args = None):
    """
    InteractionFollower

    Application for storing Twitter streaming data
    """
    print("AALTO LST InteractionFollower\n")
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
    
    # app logic
    is_connecteds = [False for _ in range(len(streams))]
    logging.info('Opening {0} streams.'.format(len(streams)))
    while True:
        try:
            stime = time.time()

            for io,stream,i in zip(ios, streams, range(len(ios))):
                # start following
                if not is_connecteds[i]:
                    stream.filter(follow = io.ids, languages=["en"], is_async=True)
                    logging.info('STREAM {0} successfully connected, number of ids: {1}'.format(io.ID,len(io.ids)))
                    is_connecteds[i] = True
            
            time.sleep(UPDATE_INTERVAL*60-(time.time() - stime))

            log_stats(ios)
                
            logging.info('Checking for new ids...')
            for io,stream,i in zip(ios,streams,range(len(ios))):
                if io.update():
                    logging.info('STREAM {0}: New user ids found. Disconnecting the stream.'.format(io.ID))
                    try:
                        stream.disconnect()
                        is_connecteds[i] = False
                    except Exception as ex:
                        logging.error('Disconnection failed, exiting.')
                        exit()
            
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

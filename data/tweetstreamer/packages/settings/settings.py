import logging
class Settings():
    def __init__(self, stsfile):
        """
        Settings should contain:
        credentialsfile: encrypted credentials binary file path
        keywordfile: txt file containing search keywords separated by newline
        location: location criterion in latitude, longitude : -122.75,36.8,-121.75,37.8
        json_dump: raw json dump file path
        
        # marks comments
        empty lines are removed
        """
        # Gets or creates a logger
        # self.logger = logging.getLogger(__name__)  
        # self.logger.setLevel(logging.INFO)
        # add file handler to logger
        # self.logger.addHandler(log_file_handler)
        logging.info("Reading settings file.")
        try:
            f = open(stsfile, "r")
            rawsts = {}
            for line in f.readlines():
                if len(line)>2:
                    s = line.rstrip().split()
                    rawsts[s[0]] = s[-1]
            f.close()
            self.credentialsfile = rawsts['credentialsfile']
            self.keywordfile = rawsts['keywordfile']
            #self.location = rawsts['location']
            self.json_dump = rawsts['json_dump']
        except Exception as ex:
            logging.error("Error while reading settings: %s",repr(ex))
            logging.info("Exiting program.")
            exit()
    def get_keywords(self):
        """
        reads keywords from a file and concatenates them
        keywords separarated with a newline
        """
        logging.info("Reading keywords.")
        try:
            with open(self.keywordfile, "r") as f:
                #sep = ' OR '
                #ret = sep.join(f.read().split())
                keywords = list(f.read().splitlines())
                logging.info("Keywords read successfully.")
                print("Keywords read in. They are:\n", keywords)
                return keywords
        except Exception as ex:
            logging.error("Error while reading keywords: %s",repr(ex))
            logging.info("Exiting program.")
            exit()
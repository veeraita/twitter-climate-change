import logging
import csv

class Settings():
    def __init__(self, stsfile):
        """
        If k is the number of streams that will be opened, then 
        settings file should contain k rows in the csv form:

        STREAMING_MODE,CREDENTIALS_PATH,INPUT_USERID_PATH,OUTPUT_RAW_JSON_PATH
        """
        # Gets or creates a logger
        logging.info("Reading settings file.")
        try:
            with open(stsfile, 'r') as set_f:
                sts_rows = csv.reader(set_f, delimiter=',')

                self.modes, self.filter_cities, self.cred_fps, self.in_fps, self.out_fps = [], [], [], [], []
                self.n_inst = 0
                for row in sts_rows:
                    assert (row[0] == 'follow') or (row[0] == 'track')
                    self.modes.append(row[0])
                    assert (row[1] == 'filter') or (row[1] == 'direct')
                    self.filter_cities.append(row[1]) # Expects "filter" or "direct"
                    for i in range(2,5):
                        assert len(row[i]) > 2,"Filenames are not of correct format, need to be longer than 2 characters!" 
                    self.cred_fps.append(row[2])
                    self.in_fps.append(row[3])
                    self.out_fps.append(row[4])
                    self.n_inst += 1
                    
            logging.debug('Path to credentials stored as: {0}'.format(self.cred_fps))
            logging.debug('Path to input files stored as: {0}'.format(self.in_fps))
            logging.debug('Path to output files stored as: {0}'.format(self.out_fps))
        except Exception as ex:
            logging.error("Error while reading settings: %s",repr(ex))
            logging.info("Exiting program.")
            exit()
    
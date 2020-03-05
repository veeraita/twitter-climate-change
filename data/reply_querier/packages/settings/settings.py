
class Settings():
    def __init__(self, stsfile):
        """
        Settings should contain:

        CREDENTIALS_PATH (str): path to encrypted credentials binary file 
        TIME_TRESHOLD    (int): time treshold in hours for initiating the reply query, max 7 days for Twitter Search API 
        JSON_READ_PATH   (str): path to the json dump file with the original tweets 
        JSON_WRITE_PATH  (str): path to raw json dump file for writing replies
        QUERIED_SET_PATH (str): path to a set of tweets
        """
        file   = open(stsfile, "r")
        rawsts = {}
        
        for line in file.readlines():
            if len(line)>2:
                s = line.rstrip().split()
                rawsts[s[0]] = s[-1]
        file.close()

        self.credentialsfile = rawsts['CREDENTIALS_PATH']
        self.json_read_path  = rawsts['JSON_READ_PATH']
        self.json_write_path = rawsts['JSON_WRITE_PATH']
        self.time_treshold   = int(rawsts['TIME_TRESHOLD'])
        self.queried         = rawsts['QUERIED_SET_PATH']

class Settings():
    def __init__(self, stsfile):
        """
        Settings should contain:
        credentialsfile: encrypted credentials binary file path
        keywordfile: txt file containing search keywords
        location: location criterion in latitude, longitude : -122.75,36.8,-121.75,37.8
        json_dump: raw json dump file path
        csv_out: csv output file path

        """
        f = open(stsfile, "r")
        rawsts = {}
        for line in f.readlines():
            if len(line)>2:
                s = line.rstrip().split()
                print(line)
                rawsts[s[0]] = s[-1]
        f.close()
        self.credentialsfile = rawsts['credentialsfile']
        self.keywordfile = rawsts['keywordfile']
        self.location = rawsts['location']
        self.json_dump = rawsts['json_dump']
        self.csv_out = rawsts['csv_out']
    def get_keywords(self):
        """
        reads keywords from a file and concatenates them
        keywords separarated with a newline
        """
        
        with open(self.keywordfile, "r") as f:
            sep = '&'
            ret = sep.join(f.read.split())
            return ret
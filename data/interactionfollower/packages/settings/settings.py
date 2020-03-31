import logging.config
import yaml

class Settings():
    def __init__(self, stsfile):
        """
        Reads YAML-setting file.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Reading settings file.")
        self.n_inst = 0
        ysts = None
        with open(stsfile, 'r') as set_f:
            try:
                ysts = yaml.safe_load(set_f)
            except yaml.YAMLError as ex:
                self.logger.error("Error while reading settings: %s",repr(ex))
                self.logger.info("Exiting program.")
                exit()
        
        self.configs = self._set_variables(ysts) 
    
    def _set_variables(self, ysts):
        # parse settings
        assert isinstance(ysts['update_interval'], int)
        self.update_interval = ysts['update_interval']
        assert '.log' == ysts['logfile'][-4:], 'Not a good logfile convention, use .log suffix.'
        self.logfile = ysts['logfile']

        configs= []
        for i in ysts['streams']:
            stream_i = ysts['streams'][i] 
            len_msg  =  "Filename not of correct format, need to be string" 
            len_msg += " with length of more than 3 characters." 
            ssts     = {}                
            
            assert (stream_i['mode'] == 'follow') or (stream_i['mode'] == 'track')
            ssts['mode'] = stream_i['mode']
            
            if not isinstance(stream_i['filter'], list):
                ssts['filter'] = False
                ssts['filter_output'] = None 
            else:
                for w in stream_i['filter']: 
                    assert isinstance(w, str) and (len(w) > 3)
                for w in stream_i['filter_output']: 
                    assert isinstance(w, str) and (len(w) > 3)

                ssts['filter'] = stream_i['filter']
                ssts['filter_output'] = stream_i['filter_output']

            for w in ['input','output','credentials']:
                assert len(stream_i[w]) > 3 and isinstance(stream_i[w], str), len_msg
                ssts[w] = stream_i[w]
            configs.append(ssts)
            self.n_inst += 1
        return configs   
        
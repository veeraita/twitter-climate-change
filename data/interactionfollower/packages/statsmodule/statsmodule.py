import statistics as st
import termtables as tt
import termplotlib as tpl
import logging
import time
import os
import numpy as np

def div(n, d):
    # Avoid Division by Zero
    return (1.0*n) / d if d else 0.0

class StatsModule():
    def __init__(self, ios, update_interval):
        """
        Initialize StatsModule, takes list of IO modules as an input parameter.
        """
        logging.info("Initializing StatsModule...")
        self.ios             = ios
        self.update_interval = update_interval
        self.curr_filesizes  = self._get_filesizes()
        self.run_data_gb     = [s / 1024**3 for s in self.curr_filesizes]
        self.last_cs         = [0  for _ in range(len(self.ios))]
        self.last_filesizes  = None
        self.iter_sizes_mb   = [[] for _ in range(len(self.ios))]
        self.iter_tweets     = [[] for _ in range(len(self.ios))]
        logging.info("StatsModule initialized successfully.")
    
    def _get_filesizes(self):
        filesizes = []
        try: 
            for io in self.ios:
                filesize = os.path.getsize(io.jsonfilename)
                filesizes.append(filesize)
                logging.debug('Filesize read, {0} : {1}'.format(io.jsonfilename, filesize))
            return filesizes
        except Exception as ex:
            logging.error("Error while initializing StatsModule: %s",repr(ex))
            logging.info("Exiting program.")
            exit()

    def _update_iter_filesizes(self):
        # Update filesize variables
        last_filesizes = self.curr_filesizes
        self.curr_filesizes = self._get_filesizes()
        if last_filesizes[0] > self.curr_filesizes[0]:
            self.last_filesizes = [0 for _ in range(len(self.ios))]
        else:
            self.last_filesizes = last_filesizes
    
    def _calculate_iter_stats(self,i,io,curr,last,is_seq):
        iter_stats = {}

        # Aggregate stats
        iter_stats['total_size_gb'] = curr / 1024**3 
        iter_stats['avg_daily_tweet_size_mb'] = ( curr / 1024**2 ) / io.daily_c_saved        
        # Iteration stats
        iter_stats['size_gained_mb'] = (curr - last) / (1024**2)
        iter_stats['tweets_gained'] = io.daily_c_saved - self.last_cs[i] if self.last_cs[i] <= io.daily_c_saved else io.daily_c_saved 

        self.run_data_gb[i] += (iter_stats['size_gained_mb'] / 1024)
        iter_stats['avg_tweet_size_mb'] = ( self.run_data_gb[i] * 1024 ) / io.c_saved  
        self.last_cs[i] = io.c_saved
        
        self.iter_sizes_mb[i].append(iter_stats['size_gained_mb'])
        self.iter_tweets[i].append(iter_stats['tweets_gained'])
        iter_stats['avg_size_mb'] = st.mean(self.iter_sizes_mb[i])
        iter_stats['avg_tweets']  = st.mean(self.iter_tweets[i])
        
        # Requires events >= 2 
        if is_seq:
            # Size
            iter_stats['sd_size_mb']      = st.stdev(self.iter_sizes_mb[i])
            iter_stats['dev_size_mb']     = iter_stats['size_gained_mb'] - iter_stats['avg_size_mb']
            iter_stats['dev_size_mb_pc']  = div(iter_stats['dev_size_mb'],iter_stats['avg_size_mb'])
            sigma_curr_size               = div(iter_stats['dev_size_mb'],iter_stats['sd_size_mb'])
            iter_stats['sigma_curr_size'] = sigma_curr_size if iter_stats['dev_size_mb'] > 0 else sigma_curr_size *-1 
            
            # Volume
            iter_stats['sd_tweets']         = st.stdev(self.iter_tweets[i])
            iter_stats['dev_tweets']        = iter_stats['tweets_gained'] - iter_stats['avg_tweets']
            iter_stats['dev_tweets_pc']     = div(iter_stats['dev_tweets'],iter_stats['avg_tweets'])
            sigma_curr_tweets               = div(iter_stats['dev_tweets'],iter_stats['sd_tweets'])
            iter_stats['sigma_curr_tweets'] = sigma_curr_tweets if iter_stats['dev_tweets'] > 0 else sigma_curr_tweets *-1 
            
            # Changes wrt previous iteration
            iter_stats['change_size_pc']    = div((iter_stats['size_gained_mb'] - self.iter_sizes_mb[i][-2]),self.iter_sizes_mb[i][-2]) 
            iter_stats['change_tweets_pc']  = div((iter_stats['tweets_gained'] - self.iter_tweets[i][-2]),self.iter_tweets[i][-2])
        
        return iter_stats
    
    def _plot_volume(self,i):
        x = range(len(self.iter_tweets[i]))
        y = self.iter_tweets[i]

        fig = tpl.figure()
        fig.plot(x, y, label="Stream {0} volume".format(i+1), width=150, height=12)
        fig.show()

    def log_stats(self):
        # Calculate run time 
        m = 60
        h = m*60 
        d = h*24
        w = d*7
        run_time = time.time() - self.ios[0].stime

        logging.info('\n\nUpdate interval saturated.')
        logging.info("Running time: {0:.0f} hours {1:.0f} minutes.".format(
                                                                    run_time // h, 
                                                                    (run_time % h) / m))
        
        self._update_iter_filesizes()
        for i, io, curr, last in zip(range(len(self.ios)),self.ios, self.curr_filesizes, self.last_filesizes):
            if io.c_saved > 0:
                is_seq     = len(self.iter_sizes_mb[i]) > 1
                upint_s    = self.update_interval*60
                iter_stats = self._calculate_iter_stats(i,io,curr,last,is_seq)
                
                logging.info("\n"+120*'=')
                print("\nIO {0}: (STATS) ".format(io.ID))
                print("")
                if iter_stats['total_size_gb'] < 1.0:
                    print("\nDAILY\t|\tData collected: {0:>15.3f} MB / {1:<12,.0f} tweets".format(iter_stats['total_size_gb'] * 1024,io.daily_c_saved))
                else:
                    print("\tData collected: {0:>15.3f} GB / {1:<12,.0f} tweets".format(iter_stats['total_size_gb'],io.daily_c_saved))
                
                print("ITERATION: {0}".format(len(self.iter_sizes_mb[i])))
                l_base = self._format_base_stats(iter_stats, io, is_seq)
                l_base.append([27*"=" for L in range(len(l_base[0]))])
                l_iter = self._format_iter_stats(iter_stats, run_time, upint_s,m,h,d,w)
                
                l_dev = None
                if is_seq:
                    l_dev = self._format_deviation(iter_stats)

                l_agg = self._format_agg_stats(iter_stats, run_time, io, i, upint_s,m,h,d,w)    
                
                for L in l_iter: l_base.append(L)
                if is_seq: 
                    for L in l_dev: l_base.append(L)
                for L in l_agg: l_base.append(L) 
                
                tt.print(np.array(l_base))
            else:
                logging.info('No tweets recorded yet.')    
        
        if len(self.iter_sizes_mb[0]) > 5: 
            print("\nVolume of tweets as a function of iterations:")
            for i,_ in enumerate(self.ios):
                self._plot_volume(i)    
        
    def _format_base_stats(self, iter_stats, io, is_seq):
        stats_base = []
        stats_base.append(['ITERATION MEASURES  ','Volume','Data','Volume change %', 'Data change %'])
        base_1 = ["", "{0:>22.0f}".format(iter_stats['tweets_gained']),
                      "{0:>22.3f} MB".format(iter_stats['size_gained_mb'])]
        if is_seq:
            base_1.append("{0:>22.3f}".format(iter_stats['change_tweets_pc']*100))
            base_1.append("{0:>22.3f}".format(iter_stats['change_size_pc']*100))
        else:
            base_1.append('NaN')
            base_1.append('NaN')
        stats_base.append(base_1)
        return stats_base

    def _format_iter_stats(self, iter_stats, run_time, upint_s,m,h,d,w):
        stats_i = []
        stats_i.append(['ITERATION DATA RATES','second','hour','day', 'week'])
        stats_i.append(['Tweet volume', 
                        "{0:>22.1f}".format(iter_stats['tweets_gained'] / upint_s),
                        "{0:>22,.0f}".format(h*iter_stats['tweets_gained'] / upint_s),
                        "{0:>22,.0f}".format(d*iter_stats['tweets_gained'] / upint_s),
                        "{0:>22,.0f}".format(w*iter_stats['tweets_gained'] / upint_s)
                        ])
        stats_i.append(['Size',
                        "{0:>22.3f} KB".format(iter_stats['size_gained_mb'] * 1024 / upint_s),
                        "{0:>22.3f} MB".format((h*iter_stats['size_gained_mb'] / upint_s)),
                        "{0:>22.3f} GB".format((d*iter_stats['size_gained_mb'] / 1024 / upint_s)),
                        "{0:>22.3f} GB".format((w*iter_stats['size_gained_mb'] / 1024 / upint_s))
        ])
        return stats_i

    def _format_deviation(self, iter_stats):
        stats_dev = []
        stats_dev.append(['DEVIATIONS','SD','Deviation from mean (tweets)','Deviation from mean (σ)','Deviation from mean (%)'])

        stats_dev.append(['Tweet volume',
                         "{0:>22.3f}   ".format(iter_stats['sd_tweets']),  
                         "{0:>22.3f}   ".format(iter_stats['dev_tweets']),
                         "{0:>22.3f} σ".format(iter_stats['sigma_curr_tweets']),
                         "{0:>22.3f} %".format(iter_stats['dev_tweets_pc']*100)
        ])
        stats_dev.append(['Size',
                        "{0:>22.3f} MB".format(iter_stats['sd_size_mb']),
                        "{0:>22.3f} MB".format(iter_stats['dev_size_mb']),
                        "{0:>22.3f} σ".format(iter_stats['sigma_curr_size']),
                        "{0:>22.3f} %".format(iter_stats['dev_size_mb_pc']*100)
        ])
        return stats_dev

    def _format_agg_stats(self, iter_stats, run_time, io, i, upint_s,m,h,d,w):
        stats_agg = []
        srate_s = io.c_saved * iter_stats['avg_tweet_size_mb'] / run_time
        trate_s = io.c_saved / run_time
        
        stats_agg.append(['AGGREGATE MEASURES','Total volume','Total data','Avg tweet size','Avg iter size'])
        stats_agg.append(['', "{0:>22.0f} tw".format(io.c_saved),
                         "{0:>22.3f} GB".format(self.run_data_gb[i]),
                         "{0:>22.0f} KB".format(iter_stats['avg_tweet_size_mb']*1024),
                         "{0:>22.3f} MB".format(iter_stats['avg_size_mb'])
                        ])
        stats_agg.append(['DATA RATES','second','hour','day', 'week'])
        stats_agg.append(['Tweet volume', 
                        "{0:>22,.1f}".format(trate_s),
                        "{0:>22,.0f}".format(h*trate_s),
                        "{0:>22,.0f}".format(d*trate_s),
                        "{0:>22,.0f}".format(w*trate_s)
                        ])
        stats_agg.append(['Size',
                        "{0:>22,.3f} MB".format(srate_s),
                        "{0:>22.1f} MB".format(srate_s*h),
                        "{0:>22.3f} GB".format(srate_s/1024*d),
                        "{0:>22,.3f} GB".format(srate_s/1024*w)
        ])
        return stats_agg
            

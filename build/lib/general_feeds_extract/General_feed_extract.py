"""
    General feeds extract.
    Use for extracting feeds such as financial/stocks news from various sites.

Updates:
    Oct 04 2015: Resolve bug in print_com_data_to_file function
    Jan 21 2015: Enable multiple category segregation
    Dec 06 2014: Add in class for feedsreader.

Modules required:
    python pattern

learning:
    sentiment analysis in feeds
    http://ceur-ws.org/Vol-862/FEOSWp4.pdf

    sentiment analysis
    http://neuro.imm.dtu.dk/wiki/Sentiment_analysis
    http://www.cs.cornell.edu/home/llee/omsa/omsa.pdf
    http://www.time.mk/msaveski/sentiment-analysis.htm
    http://sentimentforfinance.blogspot.sg/

    dict
    https://github.com/hanzhichao2000/pysentiment/

Todo:
    Include sentiment
    Break into various segment
    News classifications --> change the various rss_sites lsit
    Display only news that are greater than certain date
    Enable more of the printing format.
    Include

    additional filtering to detect news of particular company (company of interest)
    may not be as good as the google search...

may not be able to use as seek by phrases
or use pattern to get the noun phrases first
closest_match = difflib.get_close_matches(x, stockcom_list, n=1, cutoff = 0.85 )
    

Bugs some of date is still not deal correctly


"""

import os, re, sys, time, datetime, copy, calendar
import difflib
from pattern.web import URL, extension, cache, plaintext, Newsfeed
from pattern.en import parse, Sentence, parsetree, tokenize, singularize
from pattern.search import taxonomy, search , WordNetClassifier


class FeedsReader(object):
    def __init__(self):

        #For grouping to various category
        self.rss_sites_by_category_dict = {
                                            'SG':   [
                                                        'http://sbr.com.sg/rss2/news',
                                                        'http://feeds.theedgemarkets.com/theedgemarkets/sgtopstories.rss',
                                                        'http://feeds.theedgemarkets.com/theedgemarkets/sgmarkets.rss',
                                                        'http://www.channelnewsasia.com/rss/latest_cna_sgbiz_rss.xml'
                                                        #'http://feeds.feedburner.com/blogspot/wKTe?format=xml',
                                                        
                                                        #'http://feeds.theedgemarkets.com/theedgemarkets/sgproperty.rss',
                                                      ],
                                            'World':[
                                                        'http://www.ft.com/rss/home/asia',
                                                        'http://rss.cnn.com/rss/money_news_economy.rss', 
                                                        'http://feeds.reuters.com/reuters/businessNews',
                                                        'https://sg.finance.yahoo.com/news/sector-financial/?format=rss',
                                                        'https://sg.finance.yahoo.com/news/category-stocks/?format=rss',
                                                        'http://www.channelnewsasia.com/rss/latest_cna_biz_rss.xml',
                                                        'http://www.channelnewsasia.com/rss/latest_cna_frontpage_rss.xml',
                                                        'http://feeds.reuters.com/reuters/businessNews',
                                                        'http://feeds.reuters.com/reuters/companyNews',
                                                        'http://feeds.reuters.com/news/economy',
                                                        'http://feeds.reuters.com/news/usmarkets',
                                                        
                                                      ],      
                                            }
        self.rss_sites = []
        
        ## num of feeds to parse_per_site
        self.num_feeds_parse_per_site = 100

        ## individual group storage of feeds.
        self.rss_results_dict = {} # dict with date as key
        self.rss_title_list = []

        ## full results set consist of category
        self.rss_results_dict_by_cat ={} # dict of dict
        self.rss_title_list_by_cat = {}  # dict of list

        ##desired company data
        self.rss_news_company_dict = {} #dict containing the title and desc --> may add in the date later.

        ##company data file storage --> keep appending the date
        self.company_data_store_path = r'c:\data\temp\com_data.txt'

    def set_rss_sites(self, rss_site_urls):
        """ Set to self.rss_sites.
            Args:
                rss_site_urls (list): list of rss site url for getting feeds.
        """
        self.rss_sites = rss_site_urls

    def convert_date_str_to_date_key(self, date_str):
        """ Convert the date str given by twiiter [created_at] to date key in format YYYY-MM-DD.
            Args:
                date_str (str): date str in format given by twitter. 'Mon Sep 29 07:00:10 +0000 2014'
            Returns:
                (int): date key in format YYYYMMDD
        """
        date_list = date_str.split()
        
        month_dict = {v: '0'+str(k) for k,v in enumerate(calendar.month_abbr) if k <10}
        month_dict.update({v:str(k) for k,v in enumerate(calendar.month_abbr) if k >=10})

        return int(date_list[3] + month_dict[date_list[2]] + date_list[1])

    def parse_rss_sites(self):
        """ Function to parse the RSS sites.
            Results are stored in self.rss_results_dict with date as key.
        """
        self.rss_results_dict = {} 
        self.rss_title_list = []
        
        cache.clear()
        
        for rss_site_url in self.rss_sites:
            print "processing: ", rss_site_url
            try:
                results_list = Newsfeed().search(rss_site_url)[:self.num_feeds_parse_per_site]
            except:
                print 'Particular feeds have problems: ', rss_site_url
                continue
            for result in results_list:
                date_key = self.convert_date_str_to_date_key(result.date)
                self.rss_title_list.append(result.title)
                if self.rss_results_dict.has_key(date_key):
                    self.rss_results_dict[date_key].append([result.title,  plaintext(result.text)])
                else:
                    self.rss_results_dict[date_key] = [[result.title,  plaintext(result.text)]]
        print 'done'

    def parse_rss_sites_by_cat(self):
        """ Iterate over the list of categories and parse the list of rss sites.
        """
        self.rss_results_dict_by_cat ={} # dict of dict
        self.rss_title_list_by_cat = {}  # dict of list

        for cat in self.rss_sites_by_category_dict:
            print 'Processing Category: ', cat
            self.set_rss_sites(self.rss_sites_by_category_dict[cat])
            self.parse_rss_sites()
            self.rss_results_dict_by_cat[cat] = self.rss_results_dict
            self.rss_title_list_by_cat[cat] = self.rss_title_list
            
    def set_date_extract_limit(self, days):
        """ Set the limit place on the date to display. It is set based on current date - number of days.
            days (int): days duration from current date.

        """

    def get_last_effective_date(self, num_days):
        """ Return the start and end (default today) based on the interval range in tuple.
            Returns:
                start_date_tuple : tuple in yyyy mm dd of the past date
                end_date_tuple : tupe in yyyy mm dd of current date today
        """
        last_eff_date_list = list((datetime.date.today() - datetime.timedelta(num_days)).timetuple()[0:3])

        if len(str(last_eff_date_list[1])) == 1:
            last_eff_date_list[1] = '0' + str(last_eff_date_list[1])

        if len(str(last_eff_date_list[2])) == 1:
            last_eff_date_list[2] = '0' + str(last_eff_date_list[2])
    
        return int(str(last_eff_date_list[0]) + str(last_eff_date_list[1]) + str(last_eff_date_list[2]))

    def print_feeds(self, rss_results_dict):
        """ Print the RSS data results. Required the self.rss_results_dict.
            Args:
                rss_results_dict (dict): dict containing date as key and title, desc as value. 
        """
        for n in rss_results_dict.keys():
            if n < self.get_last_effective_date(1): #get the last effective date??
                continue
            print 'Results of date: ', n
            dataset = rss_results_dict[n]
            print '_______'*10
            for title,desc in dataset:
                try:
                    print title
                    result_match = self.scan_title_for_com_name(title)
                    if result_match: #if have resulst 
                        self.rss_news_company_dict[n] = (title,desc)
                    print desc
                    print '--'*5
                    print
                except:
                    print "problem printing"

    ## for company names checking
    def retrieve_company_names_to_check(self, filename):
        """ Retrieve from filename list of company to checks.
            set to self.company_namelist.
            Args:
                filename(str): filename containing list of company names.
        """
        with open(filename, 'r') as f:
            namelist =  f.read()
        self.company_namelist = namelist.split('\n')          

    def scan_title_for_com_name(self, title):
        """ Scan the list of keywords in the title.
            Separately store the interested company data.
            Use self.company_namelist
        """
        #for company_name in self.company_namelist:
        #print "noun phrase retreive: ", self.get_noun_phrase_fr_title(title)
        closest_match = difflib.get_close_matches(self.get_noun_phrase_fr_title(title), self.company_namelist, n=1, cutoff = 0.80 )
        #print 'found match: ',closest_match

        return closest_match

    def get_noun_phrase_fr_title(self,title):
        """ Get the NP from title. Use for comparing to company names to extract specific news.

        """
        t = parsetree(title, lemmata=True)
        target_search = search('NP', t)
        return target_search[0].group(0).string

    def print_feeds_for_all_cat(self):
        """ Print feeds for all the category specified by the self.rss_results_dict_by_cat

        """
        for cat in self.rss_results_dict_by_cat:
            print 'Printing Category: ', cat
            self.print_feeds(self.rss_results_dict_by_cat[cat])
            print
            print "####"*18
    
    ## saving all data to file
    def print_com_data_to_file(self):
        """ print those data related to interested company.

        """
        with open(self.company_data_store_path, 'w') as f:
            for date in self.rss_news_company_dict.keys():
                f.write(str(date))
                for title_desc in self.rss_news_company_dict[date]:
                    if len(title_desc) ==2:
                        title,desc = title_desc
                        f.write(title)
                        f.write(desc)
                        f.write('\n')
            



## for sentiment analyiss
## convert the file str to list...
                ## put the sentiment anlayiss here.
def get_strlist_fr_file(filename):
    """ Take in filename and read the str.capitalize
        Convert the str to list.
    """
    with open(filename, 'r') as f:
        data = f.readlines()
    return data
        

                   
if __name__ == '__main__':
    """ Use this method to print to file python General_feed_extract.py > C:\Users\356039\Dropbox\Stocks\stocks_feeds.txt"""

    choice  = 2

    if choice ==2:

        companyfilename = r'c:\data\temp\companyname.txt'

        f = FeedsReader()
        f.retrieve_company_names_to_check(companyfilename)
        
        f.parse_rss_sites_by_cat()
        print '=='*19
        f.print_feeds_for_all_cat()
        f.print_com_data_to_file()

    if choice ==3:
        """Try out sentiment???
            Using textblob and positive classifiier
            Need to create to take in file as training set...
            see can do it with different label

        """
        filename = r"C:\Users\Tan Kok Hua\Dropbox\Notes\stock_notes\relevency_classifier2.csv"
        data = get_strlist_fr_file(filename)

    if choice == 1:
        rss_sites  = [
                        'http://business.asiaone.com/rss.xml',


                    ]

        cache.clear()
        print
        for rss_site_url in rss_sites:
            for result in Newsfeed().search(rss_site_url)[:10]:
                print rss_site_url
                print result.date
                print result.title
                print plaintext(result.text)

                print
            print '-'*18
            print

    if choice ==4:
        
        #f = FeedsReader()
        #print f.get_last_effective_date(0)
        
        #f.parse_rss_sites_by_cat()

        """ If date is not present, then skip
            also provide the url to go to
            save all data to file.
        """


        SG_news_list = f.rss_results_dict_by_cat['SG'][f.get_last_effective_date(2)]
        SG_news_str = '\n********************\n'.join(['\n'.join(n) for n in SG_news_list])




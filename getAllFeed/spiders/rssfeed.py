# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urljoin
from rich import print
import pandas as pd
class RssfeedSpider(scrapy.Spider):
    name = 'rssfeed'
    # allowed_domains = ['cryptoflings.com']
    # start_urls = ['https://cryptoflings.com/']
    def __init__(self):    
        self.commentList = []
        self.finalFeed=[]
        self.headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"} 
        self.df=pd.read_excel('/home/roopchand/Documents/allfeeds_with_data.xlsx',sheet_name='domain1')

    def start_requests(self):
        # urls=self.df["Domain"].to_list() 
        urls=[

                'http://www.alankabout.com/'

        ]  
        for url in urls:
            try:
                yield scrapy.Request(url, headers=self.headers,callback=self.parse)  
            except Exception as error:
                
                print("Domain url error :", error)
                      
    def parse(self, response):
        # if self.df['Name'].isnull().values.all():
            # print("inside00000000000000000000000000000000000000000000000000000000000000000000")
            # title = response.xpath('//title/text()').get()
            # description = response.xpath('//meta[@name="description"]/@content').get()
            # if description is None or len(description) == 0:
            #     description = "Description not available"
            # if title is None or len(title) == 0:
            #     title = response.url.replace('https://', '').replace('.com', '').replace('/', '').replace('www.','').replace('.',' ')
            # name=response.url.replace('https://', '').replace('.com', '').replace('/', '').replace('www.','').replace('.',' ').replace(' ','_')
            # if name[0].isdigit():
            #     digi = ''
            #     alpha = ''
            #     for i in name:
            #         if i.isalpha():
            #             alpha += i
            #         if i.isdigit():
            #             digi += i
            #     name = alpha+'_'+digi
            # name =name.lower() 
            # print(f"title: {title},    Discription: {description}")    
            # self.df.loc[self.df["Domain"] == response.url, "Name"] = name
            # self.df.loc[self.df["Domain"] == response.url, "Display_Name"] = title.title()
            # self.df.loc[self.df["Domain"] == response.url, "Description"] = description
            # self.df.to_excel('/home/roopchand/Documents/allfeeds_with_data.xlsx',sheet_name='domain1', index=False)
            # print("Data saved successfully.")    
        link_extractor = LinkExtractor()
        all=[]
        for link in link_extractor.extract_links(response):
            all.append(link.url)
        allHref=response.xpath("//@href").extract()
        all.extend(allHref)
        all1=set(all)
        all2=list(all1)
        for i in all2:
            if '/feed' in i:
                self.finalFeed.append(i)
                all2.remove(i)
            elif 'https' not in i:
                all2.remove(i)
        for l in all2: 
            try:   
                yield scrapy.Request(l,headers=self.headers,callback=self.parse_links)
            except Exception as error:
                print(f"{type(l)}")
                if "rss" in l or "feed" in l:
                    errorurl=response.url+l
                    print(f"eeeeeeeeeeeeeeeeeeeeee {errorurl}")
                    # yield scrapy.Request(errorurl,headers=self.headers,callback=self.parse_links)
                print(f"parse link request error: {error} {l}")    

    def parse_links(self,response):
        try:
            print("----------------------------------PARSE_LINK ------------------")
            rss_link = response.xpath('//link[@type="application/rss+xml"]/@href').extract()
            if rss_link:
                for i in rss_link:
                    yield scrapy.Request(i,headers=self.headers, callback=self.parsefeedLonk)

        except Exception as error:
            print("parse link error:", error)
    
    def parsefeedLonk(self,response):
        try:
            print(".................................... PARSEFEEDLINK.................................")
            all=response.xpath('//channel/item')
            if all and response.url not in self.finalFeed:
               self.finalFeed.append(response.url)   
        except Exception as error:
                print("final parse feeed error:", error) 
        print(f"finalLiist$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$           {self.finalFeed}       $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        # for i in self.finalFeed:
        #     print(int(i))


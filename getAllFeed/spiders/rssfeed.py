import scrapy
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urljoin, urlparse
from rich import print
import pandas as pd

class RssfeedSpider(scrapy.Spider):
    name = 'rssfeed'

    def __init__(self):
        self.finalFeed = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
        self.df = pd.read_excel('/home/roopchand/Documents/collect_data_sheet.xlsx', sheet_name='Data')
        self.BaseUrl = ''
        self.mainfeed=[]

    def start_requests(self):
        urls = self.df["Domain"].to_list()
        # urls=[

        #     # 'https://www.andoveradvertiser.co.uk/'
        # ]
        for url in urls:
            try:
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)
            except Exception as error:
                print("Domain url error :", error)

    def parse(self, response):
            # if self.df['Name'].isnull().values.all():
        title = response.url.replace('https://', '').replace('http://', '').replace('.com', '').replace('/', '').replace('www.','').replace('.',' ')
        # title = response.xpath('//title/text()').get()
        description = response.xpath('//meta[@name="description"]/@content').get()
        if description is None or len(description) == 0:
            description = "Description not available"
        if title is None or len(title) == 0:
            title="title not available"
        name=response.url.replace('https://', '').replace('http://', '').replace('.com', '').replace('/', '').replace('www.','').replace('.',' ').replace(' ','_')
        print(f"     name: {name},    title: {title},    Discription: {description}")    
        if response.url in self.df["Domain"].values:
            # Update the DataFrame based on the condition
            self.df.loc[self.df["Domain"] == response.url, "Name"] = name
            self.df.loc[self.df["Domain"] == response.url, "Display_Name"] = title.title()
            self.df.loc[self.df["Domain"] == response.url, "Description"] = description
        else:
            # Handle the case where 'response.url' is not found in the DataFrame
            print(f"'{response.url}' not found in the 'Domain' column of the DataFrame.")

        self.df.to_excel('/home/roopchand/Documents/collect_data_sheet.xlsx',sheet_name='Data', index=False)
        print("[dark_olive_green3]Data saved successfully.................................................................................................................")    
        self.BaseUrl = response.url
        link_extractor = LinkExtractor()
        all_links = []
        # Extract all links from the page
        for link in link_extractor.extract_links(response):
            all_links.append(link.url)
        all_href = response.xpath("//@href").extract()
        all_links.extend(all_href)

        # Remove duplicate links and make them absolute
        all_filtered_links = set(all_links)
        all_filtered_links = [urljoin(response.url, link) for link in all_filtered_links]

        for i in all_filtered_links.copy():
            if '/feed' in i  and 'comments' not in i:
                self.mainfeed.append(i)

            if not (i.startswith('http://') or i.startswith('https://')):
                all_filtered_links.remove(i)

        def is_valid_url(url):
            parsed_url = urlparse(url)
            return all([parsed_url.scheme, parsed_url.netloc])
        valid_urls = [url for url in all_filtered_links if is_valid_url(url)]
        valid_urls.append(urljoin(self.BaseUrl, '/rss'))
        # print(valid_urls)
        for link in valid_urls:
            try:
                if '/rss' in link or '.rss' in link:
                    yield scrapy.Request(link, headers=self.headers, callback=self.parse_rss_links)
                elif '/rss' not in link:  
                    yield scrapy.Request(link, headers=self.headers, callback=self.parse_links)
            except Exception as error:
                print(f"Parse link request error: {error}")
    def parse_rss_links(self,response):
        # print(response.url)
        try:
            print("[red]------------------------------get all feed in rss----------------------------------")
            if response.xpath('//channel'):
                self.finalFeed.append(response.url)          
            else:
                print(f"fffffffffffffffffffffffffffffffffffffffff {response}")
                get_link=response.xpath('//ul[@class="rss_list"]//a/@href |\
                //div[@class="rss"]//a/@href').extract()
                # print(get_link)
                if get_link:
                    for link in get_link:
                        yield scrapy.Request(link, headers=self.headers, callback=self.parse_feed_link)
        except Exception as error:
            print(f"rss feed error {error}")
    def parse_links(self, response):
        try:
            print("[bright_cyan]----------------------------------PARSE_LINK ------------------")
            rss_links = response.xpath('//link[@type="application/rss+xml"]/@href').extract()
            rss_links = [urljoin(self.BaseUrl, link) if link.startswith('/') else link for link in rss_links]
            if rss_links:
                for link in rss_links:
                    yield scrapy.Request(link, headers=self.headers, callback=self.parse_feed_link)
        except Exception as error:
            print("Parse link error:", error)

    def parse_feed_link(self, response):
        try:
            print("[bright_yellow].................................... PARSEFEEDLINK.................................")
            items = response.xpath('//channel')
            # print(f"item   {items}")
            count = 0

            # Iterate through each 'item' in the feed
            for item in items.xpath('//item'):
                title = item.xpath('./title/text()').get()
                pubDate = item.xpath('./pubDate/text()').get()
                link = item.xpath('./link/text()').get()
     
                # Check if 'title', 'pubDate', and 'link' are all present in the item
                # print(f"title  {title} {pubDate} {link}")
                if title and pubDate and link:
                    count += 1

            if count > 4:
                if 'author' not in response.url and self.BaseUrl in response.url and 'comment' not in response.url:
                    if response.url not in self.finalFeed:
                        self.finalFeed.append(response.url)
                else:
                    name=self.BaseUrl.replace('https://', '').replace('http://', '').replace('www.','').replace('rss','')
                    if 'author' not in response.url and name in response.url and 'comment' not in response.url:
                        if response.url not in self.finalFeed:
                            self.finalFeed.append(response.url)

        except Exception as error:
            print("Final parse feed error:", error)
        print(f"Appending feed in List of Finalfeed: {self.finalFeed}")

    def closed(self, reason):
        if len(self.finalFeed)==0:
            self.finalFeed.append("No feed Found") 
        sorted_urls = sorted(self.finalFeed, key=len)
        
        clear_list = []
        while sorted_urls:
            current_url = sorted_urls.pop(0)
            clear_list.append(current_url)  
            substring = current_url[:-5]
            sorted_urls = [url for url in sorted_urls if substring not in url]
        clear_list=clear_list+self.mainfeed    
        for url in range(len(clear_list)):
            print(clear_list[url])
            index=url
            self.df.at[index, "Source_Link"] = clear_list[url]
        self.df.to_excel('/home/roopchand/Documents/collect_data_sheet.xlsx', index=False, sheet_name='Data')
        print(f"Save to all data to the sheet succesfully !")

# Run your spider using 'scrapy crawl rssfeed' in your terminal
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

    def start_requests(self):
        # urls = self.df["Domain"].to_list()
        urls=[

            # 'https://www.andoveradvertiser.co.uk/'
        ]
        for url in urls:
            try:
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)
            except Exception as error:
                print("Domain url error :", error)

    def parse(self, response):
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
            if ('/feed' in i or '/rss' in i) and 'comments' not in i:
                self.finalFeed.append(i)
                # self.df = pd.concat([self.df, pd.DataFrame({'Source_Link': [i]})], ignore_index=True)  # Append to DataFrame

            if not (i.startswith('http://') or i.startswith('https://')):
                all_filtered_links.remove(i)

        def is_valid_url(url):
            parsed_url = urlparse(url)
            return all([parsed_url.scheme, parsed_url.netloc])

        valid_urls = [url for url in all_filtered_links if is_valid_url(url)]
        for link in valid_urls:
            try:
                yield scrapy.Request(link, headers=self.headers, callback=self.parse_links)
            except Exception as error:
                print(f"Parse link request error: {error}")

    def parse_links(self, response):
        try:
            print("----------------------------------PARSE_LINK ------------------")
            rss_links = response.xpath('//link[@type="application/rss+xml"]/@href').extract()
            rss_links = [urljoin(self.BaseUrl, link) if link.startswith('/') else link for link in rss_links]
            if rss_links:
                for link in rss_links:
                    yield scrapy.Request(link, headers=self.headers, callback=self.parse_feed_link)
        except Exception as error:
            print("Parse link error:", error)

    def parse_feed_link(self, response):
        try:
            print(".................................... PARSEFEEDLINK.................................")
            items = response.xpath('//channel')
            count = 0

            # Iterate through each 'item' in the feed
            for item in items.xpath('//item'):
                title = item.xpath('./title/text()').get()
                pubDate = item.xpath('./pubDate/text()').get()
                link = item.xpath('./link/text()').get()

                # Check if 'title', 'pubDate', and 'link' are all present in the item
                if title and pubDate and link:
                    count += 1

            if count > 4:
                if 'author' not in response.url and self.BaseUrl in response.url and 'comment' not in response.url:
                    if response.url not in self.finalFeed:
                        self.finalFeed.append(response.url)
                        # self.df = pd.concat([self.df, pd.DataFrame({'Source_Link': [response.url]})], ignore_index=True)  # Append to DataFrame
        except Exception as error:
            print("Final parse feed error:", error)
        print(f"Final List of Feed URLs: {self.finalFeed}")

    # def closed(self, reason):
    #     self.df.to_excel('/home/roopchand/Documents/collect_data_sheet.xlsx', index=False, sheet_name='Data')

# Run your spider using 'scrapy crawl rssfeed' in your terminal

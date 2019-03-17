import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import HtmlXPathSelector, Selector

import re
from scrapy.http.request import Request
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from ..items import TripadvisorItem

class TripAdvisor(CrawlSpider):
    name = 'tripadvisor'

    # allowed_domains = ['https://www.tripadvisor.com']

    start_urls = [
        'https://www.tripadvisor.com/SiteIndex',
        # 'https://www.tripadvisor.com/Tourism-g8-South_Pacific-Vacations.html'
        # 'https://www.tripadvisor.com/TourismChildrenAjax?geo=294225&offset=0&desktop=true'
        # https://www.tripadvisor.com/Tourism-g294445-Albania-Vacations.html
    ]

    rules = (
        # если у меня страница = https://www.tripadvisor.com/Tourism\w+
        # если страница равна site_map
        # Rule(LinkExtractor(allow=('https://www.tripadvisor.com/Tourism-g8-South_Pacific-Vacations.html')), callback='parse_back'),
        Rule(LinkExtractor(allow=('SiteIndex')), callback='start_url'),
        # Rule(LinkExtractor(allow=('Tourism-*'), deny=('//*[contains(concat( " ", @class, " " ), concat( " ", "photo_image", " " ))]')), callback='parse_children'),
    )


    def start_url(self, response):
        # print("eeeeee")
        continents = [
            'Europe', 'Asia', 'South_America', 'Central_America', 'Africa',
            'Middle_East', 'South_Pacific', 'Antarctica', 'World', 'Site'
        ]

        country_link = response.url
        country_name = country_link[:-5]
        try:
            country_name = re.search(r'\w+$', country_name).group(0)
        except:
            return
        if country_name in continents:
            return

        country_link = country_link.replace('SiteIndex', 'Tourism')
        yield response.follow(country_link, callback=self.parse_back, meta={'country_name': country_name})


    # def parse_country(self, response):
    #     country_name = response.meta.get('country_name')
    #     continent = response.css('li.breadcrumb a span::text').extract()
    #     block = response.css('.popularCitiesSection').extract()
    #     if block:
    #         geo = re.search(r'[0-9]+', response.url).group(0)
    #         url = 'https://www.tripadvisor.com/TourismChildrenAjax?geo=' + geo + '&offset=0&desktop=true'
    #         yield response.follow(url, callback=self.parse_children, meta={'country_name':country_name,
    #                                                                        'continent':continent,
    #                                                                        'links': [],
    #                                                                        'page_number': 0,
    #                                                                        'geo': geo,
    #                                                                        'region_name': []})
    #     print("country exit")
    #
    #
    # def parse_children(self, response):
    #     country_name = response.meta.get('country_name')
    #     continent = response.meta.get('continent')
    #     page_number = response.meta.get('page_number')
    #     hxs = Selector(response)
    #     region_name = hxs.css('.name::text').extract()
    #
    #     last_page = hxs.xpath("//script/text()").extract()
    #     last_page = re.search(r'[0-9]+', last_page[0]).group(0)
    #
    #     # item = TripadvisorItem()
    #     #
    #     # item['continent'] = continent
    #     # item['country_name'] = country_name
    #     # item['region_name'] = region_name
    #
    #     # yield item
    #     while page_number != int(last_page):
    #         links = hxs.xpath('//@href').extract()
    #         links = response.meta.get('links') + links
    #         region_name = hxs.css('.name::text').extract()
    #         region_name = response.meta.get('region_name') + region_name
    #         geo = response.meta.get('geo')
    #         url = 'https://www.tripadvisor.com/TourismChildrenAjax?geo={}&offset={}&desktop=true'.format(geo, page_number + 1)
    #         yield response.follow(url, callback=self.parse_children, meta={'country_name': country_name,
    #                                                                        'continent':continent,
    #                                                                        'links': links,
    #                                                                        'page_number': page_number + 1,
    #                                                                        'geo': geo,
    #                                                                        'region_name': region_name})
    #         break




    def parse_back(self, response):
        continent = response.css('.breadcrumb:nth-child(1) .link span::text').extract()
        country_name = response.meta.get('country_name')
        # city_name = response.css('.breadcrumb:nth-child(5)::text').extract()
        # if not city_name:
        #     city_name = response.css('.breadcrumb:nth-child(4)::text').extract()
        # country_name = response.css('.breadcrumb:nth-child(2) .link span::text').extract()
        block = response.css('.popularCitiesSection').extract()

        if block:
            geo = re.search(r'[0-9]+', response.url).group(0)
            url = 'https://www.tripadvisor.com/TourismChildrenAjax?geo=' + geo + '&offset=0&desktop=true'
            yield response.follow(url, callback=self.parse_child, meta={'page_number': 0,
                                                                        'geo': geo,
                                                                        'continent': continent,
                                                                        'country_name': country_name,
                                                                        'links': []})
        else:
            item = TripadvisorItem()
            item['continent'] = continent
            item['country_name'] = country_name
            yield item


    def parse_child(self, response):
        page_number = response.meta.get('page_number')
        hxs = Selector(response)
        last_page = hxs.xpath("//script/text()").extract()
        last_page = re.search(r'[0-9]+', last_page[0]).group(0)

        # region_rank = response.css('.rankNum::text').extract()
        region_name = response.meta.get('region_name')

        links = response.meta.get('links')

        country_name = response.meta.get('country_name')
        continent = response.meta.get('continent')

        for i, link in enumerate(links):
            url = 'https://www.tripadvisor.com' + link
            yield response.follow(url, callback=self.parse_city, meta={'country_name': country_name,
                                                                       'region_name': region_name[i],
                                                                       'continent': continent,
                                                                       })

        while page_number != int(last_page):
            geo = response.meta.get('geo')
            links = hxs.xpath('//@href').extract()
            url = 'https://www.tripadvisor.com/TourismChildrenAjax?geo={}&offset={}&desktop=true'.format(geo,
                                                                                                         page_number + 1)
            region_name = hxs.css('.name::text').extract()
            yield response.follow(url, callback=self.parse_child, meta={'page_number': page_number + 1,
                                                                        'geo': geo,
                                                                        'links': links,
                                                                        'region_name': region_name,
                                                                        'country_name': country_name,
                                                                        'continent': continent})
            break

    def parse_city(self, response):
        block = response.css('.popularCitiesSection').extract()
        continent = response.meta.get('continent')
        country_name = response.meta.get('country_name')
        region_name = response.meta.get('region_name')
        if block:
            geo = re.search(r'[0-9]+', response.url).group(0)
            url = 'https://www.tripadvisor.com/TourismChildrenAjax?geo=' + geo + '&offset=0&desktop=true'
            yield response.follow(url, callback=self.parse_last, meta={'page_number': 0,
                                                                        'geo': geo,
                                                                        'continent': continent,
                                                                        'country_name': country_name,
                                                                        'region_name': region_name,
                                                                        'links': []
                                                                        })
        else:
            item = TripadvisorItem()
            item['continent'] = continent
            item['country_name'] = country_name
            item['region_name'] = region_name
            yield item


    # Нужно сделать так, чтоб уровень добавлялся, но не перезаписывался append
    # проверить на дупликаты
    def parse_last(self, response):
        page_number = response.meta.get('page_number')
        hxs = Selector(response)
        last_page = hxs.xpath("//script/text()").extract()
        last_page = re.search(r'[0-9]+', last_page[0]).group(0)

        hxs = Selector(response)
        region_name = response.meta.get('region_name')
        country_name = response.meta.get('country_name')
        continent = response.meta.get('continent')
        city_name = hxs.css('.name::text').extract()
        item = TripadvisorItem()

        item['continent'] = continent
        item['country_name'] = country_name
        item['region_name'] = region_name
        item['city_name'] = city_name
        yield item

        while page_number != int(last_page):
            geo = response.meta.get('geo')
            links = hxs.xpath('//@href').extract()
            url = 'https://www.tripadvisor.com/TourismChildrenAjax?geo=' + geo + '&offset=0&desktop=true'
            yield response.follow(url, callback=self.parse_last, meta={'page_number': page_number + 1,
                                                                        'geo': geo,
                                                                        'links': links,
                                                                        'region_name': region_name,
                                                                        'country_name': country_name,
                                                                        'continent': continent})
            break
        # # перейти на след страницу
        # print('********************')
        # print(links)
        # print('********************')

        # print(response.url)
        # country_name = response.meta.get('country_name')
        # continent = response.css('li.breadcrumb a span::text').extract()
        # block = response.css('.popularCitiesSection').extract()

        # print("*********************************")
        # print("Parse_block")
        # # print(LinkExtractor(allow=(), deny=('//*[contains(concat( " ", @class, " " ), concat( " ", "popularCitiesSection", " " ))]')).)
        # hxs = Selector(response)
        # names = hxs.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "name", " " ))]/text()').extract()
        # try:
        #     names = names.remove('\n')
        # except:
        #     names = names
        # print(hxs.response.url)
        # print(names)
        # print("*********************************")
        # return names


    # def parse_second(self, response):
    #     """
    #     Now bot on country page
    #     Parse regions/cities
    #     """
    #     # BASE
    #     country_name = response.meta.get('country_name')
    #     region_name = response.css('div.popularCities .name::text').extract()
    #     region_link = response.css('div.popularCities a').xpath("@href").extract()
    #     region_number = response.css('.rankNum::text').extract()
    #     continent = response.css('li.breadcrumb a span::text').extract()
    #
    #
    #     for i, url in enumerate(region_link):
    #         url = 'https://www.tripadvisor.com' + url
    #         yield response.follow(url, callback=self.parse_third, meta={'region_name': region_name[i],
    #                                                                     'region_number': region_number[i],
    #                                                                     'country_name': coutry_name,
    #                                                                     'continent': continent})
    #
    # #in region
    # def parse_third(self, response):
    #     """
    #     Now bot on city/region page
    #     parse cities
    #     if cities is it:
    #         make one row for one city
    #     else:
    #         make row with Nan city
    #     """
    #     items = TripadvisorItem()
    #
    #     region_name = response.meta.get('region_name')
    #     region_number = response.meta.get('region_number')
    #     coutry_name = response.meta.get('country_name')
    #     continent = response.meta.get('continent')
    #     city_name = response.css('div.popularCities .name::text').extract()
    #     city_number = response.css('.rankNum::text').extract()
    #
    #     if not city_name:
    #         items['continent'] = continent
    #         items['country_name'] = coutry_name
    #         items['region_name'] = region_name
    #         items['continent'] = continent
    #         items['region_number'] = region_number
    #         items['city_number'] = city_number
    #         yield items
    #     else:
    #         for i, city in enumerate(city_name):
    #             items['continent'] = continent
    #             items['country_name'] = coutry_name
    #             items['region_name'] = region_name
    #             items['city_name'] = city
    #             items['continent'] = continent
    #             items['region_number'] = region_number
    #             items['city_number'] = city_number[i]
    #             yield items



    def get_countries(self, response):
        """
        Parse site map and take all counties and continents
        Then delete continents
        Then make links for all countries
        :return:
            Name of countries
            Link to countries
        """
        continents = {
            'Europe', 'Asia', 'South America', 'Central America', 'Africa',
            'Middle East', 'South Pacific', 'Antarctica', 'World'
        }

        country_link = response.css('.world_destinations a').xpath("@href").extract()
        country_name = response.css('.world_destinations a::text').extract()

        for continent in continents:
            index = country_name.index(continent)
            del country_name[index]
            del country_link[index]

        country_link = ['https://www.tripadvisor.com' + link.replace('SiteIndex', 'Tourism') for link in country_link]
        return country_name, country_link





        # for i, url in enumerate(country_link):
        #     yield response.follow(url , callback=self.test_load_more)
        #
        #
        #
        #     def test_load_more(self, response):
        #         print(response.url)
        #         geo = re.search(r'[0-9]+', response.url).group(0)
        #         url = 'https://www.tripadvisor.com/TourismChildrenAjax?geo=' + str(geo) + '&offset=2&desktop=true'
        #         yield Request(url, callback=self.test)
        #         # region_name = response.css('div.popularCities .name::text').extract()
        #
        #     def test(self, response):
        #         print("********************************")
        #         region_name = response.css('.name::text').extract()
        #         print(region_name)



        # def parse_country(self, response):
        #     print("3")
        #     country_name = response.meta.get('country_name')
        #     continent = response.css('li.breadcrumb a span::text').extract()
        #     block = response.css('.popularCitiesSection').extract()
        #     while block:
        #         geo = re.search(r'[0-9]+', response.url).group(0)
        #         url = 'https://www.tripadvisor.com/TourismChildrenAjax?geo=' + geo + '&offset=0&desktop=true'
        #         Request(url, callback=self.test, meta={'country_name': country_name,
        #                                                 'continent': continent})


        # country_name = response.meta.get('country_name')
        # block = response.css('.popularCitiesSection').extract()
        # if block:
        #     geo = re.search(r'[0-9]+', response.url).group(0)
        #     json_counter = response.meta.get('json_counter')
        #     json_link = 'https://www.tripadvisor.com/TourismChildrenAjax?geo=' + geo + '&offset=' + json_counter + '&desktop=true'
        #     yield response.follow(json_link, callback=self.parse_item, meta={'country_name': country_name,
        #                                                                         'json_counter': json_counter + 1,
        #                                                                         'json_request': False})

        # json_button = response.css('.chevron::text').extract()
        # json_request = response.meta.get('json_request')
        # if json_button and json_request:
        #     geo = re.search(r'[0-9]+', response.url).group(0)
        #     json_counter = response.meta.get('json_counter')
        #     country_name = response.meta.get('country_name')
        #     json_link = 'https://www.tripadvisor.com/TourismChildrenAjax?geo=' + geo + '&offset=' + json_counter +'&desktop=true'
        #     yield response.follow(json_link, callback=self.parse_second, meta={'country_name': country_name,
        #                                                                         'json_counter': json_counter + 1,
        #                                                                         'json_request': False})

        # geos = [re.search(r'[0-9]+', link).group(0) for link in country_link]

    # rules = (
    #     Rule(LinkExtractor(allow='https://www.tripadvisor.com/TourismChildrenAjax?geo={}&offset={}&desktop=true'), 'test2'),
    # )


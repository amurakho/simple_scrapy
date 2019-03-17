# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TripadvisorItem(scrapy.Item):
    continent = scrapy.Field()
    country_name = scrapy.Field()
    region_name = scrapy.Field()
    # region_number = scrapy.Field()
    city_name = scrapy.Field()
    # city_number = scrapy.Field()

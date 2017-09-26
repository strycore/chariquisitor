# -*- coding: utf-8 -*-
import re
import scrapy


class ChairsSpider(scrapy.Spider):
    name = 'chairs'
    allowed_domains = ['linuxgamecast.com']
    start_urls = ['https://linuxgamecast.com/category/linuxgamecastweekly/']

    def parse(self, response):
        for url in response.css('#paginate > a::attr("href")'):
            full_url = response.urljoin(url.extract())
            yield scrapy.Request(full_url, callback=self.parse)

        for url in response.css('#posts a.thumbnail-frame-video::attr("href")'):
            full_url = response.urljoin(url.extract())
            yield scrapy.Request(full_url, callback=self.parse_charis)

    def get_game_title(self, response):
        title_text = response.xpath('//p/b[starts-with(., "Game:")]/text()').extract_first()
        if not title_text:
            raise ValueError("No game name!")
        return title_text.split(' ', 1)[1]

    def parse_charis(self, response):
        episode_title = response.xpath('//div[@class="post-details"]/h2/a/text()').extract_first()
        episode_title_match = re.search(r'(\d+)', episode_title)
        if episode_title_match:
            episode = int(episode_title_match.groups()[0])
        else:
            raise ValueError("Could not find episode number in %s" % episode_title)
        game_title = self.get_game_title(response)
        segments = ['workings', 'shinies', 'controls', 'fun']
        current_segment = 0

        elements = response.xpath(
            '//div[@class="post-content"]/p/b[starts-with(.//text(), "Makes with the working")]/parent::*/following-sibling::p'
        )
        scores = {}
        for segment in segments:
            scores[segment] = {}

        for element in elements:
            text = element.xpath('.//text()').extract_first().strip()
            if 'shin' in text.lower():
                current_segment = 1
                continue
            if 'control' in text.lower():
                current_segment = 2
                continue
            if 'fun' in text.lower():
                current_segment = 3
                continue
            num_charis = len(element.xpath('./b/a'))
            if not num_charis:
                num_charis = len(element.xpath('./b/span'))
            if not num_charis:
                num_charis = len(element.xpath('./b/img'))
            if num_charis > 4:
                raise ValueError('Illegal number of charis')
            if text == 'V-':
                reviewer = 'venn'
            elif text == 'J-':
                reviewer = 'jordan'
            elif text == 'P-':
                reviewer = 'pedro'
            else:
                # Deal with guests here
                continue
            scores[segments[current_segment]][reviewer] = num_charis

        yield {
            'name': game_title,
            'episode': episode,
            'scores': scores
        }

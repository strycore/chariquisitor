# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy.exceptions import CloseSpider, DropItem
from scrapy.shell import inspect_response


class ChairsSpider(scrapy.Spider):
    name = 'chairs'
    allowed_domains = ['linuxgamecast.com']
    start_urls = ['https://linuxgamecast.com/category/linuxgamecastweekly/']

    def parse(self, response):
        self.processed_episodes = set()
        for url in response.css('#paginate > a::attr("href")'):
            full_url = response.urljoin(url.extract())
            yield scrapy.Request(full_url, callback=self.parse)

        for url in response.css('#posts a.thumbnail-frame-video::attr("href")'):
            full_url = response.urljoin(url.extract())
            if 'category' not in full_url:
                yield scrapy.Request(full_url, callback=self.parse_charis)

    def get_game_title(self, response):
        title_text = response.xpath(
            '//p//*[starts-with(., "Game:")]/text()'
        ).extract_first()
        if title_text == 'Game:':
            try:
                title_text = response.xpath('//p/*[starts-with(., "Game:")]/parent::p//text()').extract()[1]
            except IndexError:
                inspect_response(response, self)
                raise CloseSpider("Invalid name %s" % title_text)

        if not title_text:
            title_text = response.xpath('//p/*[starts-with(., "Game")]/parent::p//text()').extract_first()

        if not title_text:
            title_text = response.xpath('//p[starts-with(., "Game:")]/text()').extract_first()
        if not title_text:
            if response.url in [
                'https://linuxgamecast.com/2017/08/linuxgamecast-weekly-262-youre-all-idiots/',
                'https://linuxgamecast.com/2015/12/linuxgamecast-weekly-ep174-sriracha-novella/',
                'https://linuxgamecast.com/2015/09/linuxgamecast-weekly-ep159-five-dudes/',
                'https://linuxgamecast.com/2016/12/linuxgamecast-weekly-227-dongle-inside/',
            ]:
                return False
            raise DropItem("No game name in %s!" % response.url)
        try:
            return title_text.replace('&nbsp;', ' ').split(' ', 1)[1]
        except IndexError:
            # inspect_response(response, self)
            # raise CloseSpider("Invalid name %s" % title_text)
            raise DropItem("Invalid name %s" % title_text)

    def get_episode_number(self, response):
        episode_title = response.xpath('//div[@class="post-details"]/h2/a/text()').extract_first()
        episode_title_match = re.search(r'(\d+)', episode_title)
        if episode_title_match:
            return int(episode_title_match.groups()[0])
        else:
            raise ValueError("Could not find episode number in %s" % episode_title)

    def get_reviewer(self, text):
        if text == 'V-':
            return 'venn'
        elif text == 'J-':
            return 'jordan'
        elif text == 'P-':
            return 'pedro'
        else:
            # TODO Deal with guests here
            return

    def parse_charis(self, response):
        episode = self.get_episode_number(response)
        if episode in self.processed_episodes:
            return
        self.processed_episodes.add(episode)
        game_title = self.get_game_title(response)
        if game_title is False:
            return
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

            candidates = ['./b/a', './b/b/a', './b/span', './b/b/span', './b/img', './b/b/img', './b/strong/img', './b/b/b/img']
            num_charis = len(element.xpath('|'.join(candidates)))
            reviewer = self.get_reviewer(text)
            if not reviewer:
                continue

            segment = segments[current_segment]
            if num_charis > 4 or num_charis == 0:
                # inspect_response(response, self)
                # raise CloseSpider('Illegal number of charis in %s section for %s on %s (text: %s)' % (segment, reviewer, response.url, text))
                raise DropItem('Illegal number of charis in %s section for %s on %s (text: %s)' % (segment, reviewer, response.url, text))
            scores[segment][reviewer] = num_charis

        yield {
            'name': game_title,
            'episode': episode,
            'scores': scores
        }

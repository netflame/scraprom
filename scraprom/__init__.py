#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__            = 'scraprom'
__version__         = '1.0.1'
__description__     = 'Scrapy stats collector for prometheus'
__author__          = 'ilpan'
__author_email__    = 'pna.dev@outlook.com'


from .collector import PromStatsCollector

__all__ = (
    'PromStatsCollector',
)
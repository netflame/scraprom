# scraprom

scrapy stats exporter for prometheus

### how to use
0. pip3 install -U scraprom
1. STATS_CLASS = 'scraprom.exporter.PromStatsCollector'
2. SCRAPROM_BIND_HOST = string      # default is '0.0.0.0'
3. SCRAPROM_BIND_PORT = int         # default is 3590
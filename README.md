# scraprom

scrapy stats collector for prometheus

### how to use
0. ```pip3 install -U scraprom```
1. ```STATS_CLASS = 'scraprom.PromStatsCollector'```
2. ```SCRAPROM_PUSHGATEWAY_URL = 'host:port'    # default is '0.0.0.0:9091'```
3. ```SCRAPROM_JOB_NAME = 'job_name'    # default is scrapy```
4.  ```SCRAPROM_PUSH_TIMEOUT = 'timeout_in_seconds'  # default is 3```
5.  ```SCRAPROM_UPDATE_INTERVAL = 'interval_in_seconds' # default is 5```
6. ```SCRAPROM_METRICS_PREFIX = 'metrics_prefix'    # default is 'scraprom'```

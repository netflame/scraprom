#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import defaults
from . import myapp
from prometheus_client import Counter, Gauge, CollectorRegistry, start_http_server
from scrapy import signals
from scrapy.statscollectors import MemoryStatsCollector


class PromStatsCollector(MemoryStatsCollector):
    """
    For collect more stats, please make sure related extensions and middlewares enabled.
    eg:
        downloadermiddlewares:
            - DOWNLOADER_STATS (.stats.DownloaderStats):
                - downloader/request_count
                - downloader/request_method_count/%s % request.method
                - downloader/request_bytes
                - downloader/response_count
                - downloader/response_status_count/%s % response.status
                - downloader/response_bytes
                - downloader/exception_count
                - downloader/exception_type_count/%s % ex_class
            - RETRY_ENABLED (.retry.RetryMiddleware):
                - retry/count
                - retry/reason_count/%s % reason
                - retry/max_reached
        
        spidermiddlewares:
            - DEPTH_STATS_VERBOSE (.depth.DepthMiddleware):
                - request_depth_count/%s % depth
                - request_depth_max
                - request_depth_count/0     # depth=0
            - httperror.HttpErrorMiddleware:
                - httperror/response_ignored_count
                - httperror/response_ignored_status_count/%s % response.status
            - offsite.OffsiteMiddleware:
                - offsite/domains
                - offsite/filtered

        extensions:
            - corestats.CoreStats:
                - start_time
                - finish_time
                - finish_reason
                - item_scraped_count
                - response_received_count
                - item_dropped_count
                - item_dropped_reasons_count/%s % reason
            - MEMDEBUG_ENABLED (.memdebug.MemoryDebugger):
                - memdebug/gc_garbage_count
                - memdebug/live_refs/%s % cls.__name__
            - MMEUSAGE_ENABLED (.memusage.MemoryUsage):
                - memusage/startup
                - memusage/max

        dupfilter:
            - wscrape.bloom_scrapy_redis.dupfilter.BloomFilter
                - dupefilter/filtered

        scheduler:
            - wscrape.bloom_scrapy_redis.scheduler.BloomScheduler
                - scheduler/enqueued/redis
                - scheduler/dequeued/redis
        
        utils:
            - log.LogCounterHandler
                - 'log_count/{}'.format(record.levelname)

    """

    def __init__(self, crawler):

        print("#"*20, "init stats collector...", "#"*20)

        super().__init__(crawler)
        self.crawler = crawler
        self.metrics = {}
        # self.registry = CollectorRegistry(auto_describe=True)
        self.registry = myapp.MY_REGISTRY
        
        self.crawler.signals.connect(self.engine_started, signals.engine_started)
        self.crawler.signals.connect(self.engine_stopped, signals.engine_stopped)

    def engine_started(self):
        print("#"*20, "engine started", "#"*20)
        host = self.crawler.settings.get('SCRAPROM_BIND_ADDR', defaults.SCRAPROM_BIND_HOST)
        port = self.crawler.settings.getint('SCRAPROM_BIND_PORT', defaults.SCRAPROM_BIND_PORT)
        start_http_server(port, host, registry=self.registry)
        # metrics_path = self.crawler.settings.get('SCRAPROM_METRIC_PATH', defaults.SCRAPROM_METRICS_PATH)
        # myapp.init_app(metrics_path)
        # myapp.run_app(host, port)
        pass

    def engine_stopped(self):
        pass

    def set_value(self, key, value, spider=None):
        # if spider is None:
            # spider = self.crawler.spider
        super().set_value(key, value, spider=spider)
        self._set_gauge_value(key, spider)

    def inc_value(self, key, count=1, start=0, spider=None):
        # if spider is None:
            # spider = self.crawler.spider
        super().inc_value(key, count=count, start=start, spider=spider)

        labelnames, labelvalues = ['spider'], [spider.name if spider else '']
        # if 'request_method_count' in key:
        #     labelnames.append('method')
        #     labelvalues.append(key[key.rindex('/')+1:])
        # elif 'response_status_count' in key:
        #     labelnames.append('status')
        #     labelvalues.append(key[key.rindex('/')+1:])
        pmetric = self.__get_parent_metric(key, Counter, labelnames)#, labelvalues)
        pmetric.labels(*labelvalues).inc(count)

    def max_value(self, key, value, spider=None):
        # if spider is None:
            # spider = self.crawler.spider
        super().max_value(key, value, spider=spider)
        self._set_gauge_value(key, spider)

    def min_value(self, key, value, spider=None):
        # if spider is None:
            # spider = self.crawler.spider
        super().min_value(key, value, spider=spider)
        self._set_gauge_value(key, spider)

    def _set_gauge_value(self, key, spider):
        labelnames, labelvalues = ['spider'], [spider.name if spider else '']
        value = self._stats[key]
        if isinstance(value, (int, float)):     # ignore start_time and finish_time ...
            pmetric = self.__get_parent_metric(key, Gauge, labelnames)#, labelvalues)
            pmetric.labels(*labelvalues).set(value)

    def __get_parent_metric(self, key, metric_type, labelnames=()): #, labelvalues=()):
        metric_prefix = self.crawler.settings.get('SCRAPROM_METRIC_PREFIX', defaults.SCRAPROM_METRICS_PREFIX)
        metric_name = '{0}_{1}'.format(metric_prefix, key.replace('/', '_')).lower()
        # metric_key = tuple([key] + list(labelvalues))
        metric_key = tuple([key])
        if metric_key not in self.metrics:
            # > Register the multi-wrapper parent metric, or if a label-less metric, the whole shebang. (from prometheus/client_python.metrics.py)
            self.metrics[metric_key] = metric_type(metric_name, key, labelnames=labelnames, registry=self.registry)#, labelvalues=labelvalues)
        return self.metrics[metric_key]

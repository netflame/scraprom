#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from . import defaults
from prometheus_client import Counter, Gauge, CollectorRegistry, pushadd_to_gateway
from scrapy import signals
from scrapy.statscollectors import MemoryStatsCollector
from twisted.internet import task


class PromMixIn:
    
    def update(self):
        """
        update metrics registered by registry
        """
        gateway = self.crawler.settings.get("SCRAPROM_PUSHGATE_URL", defaults.SCRAPROM_PUSHGATEWAY_URL)
        job = self.crawler.settings.get("SCRAPROM_JOB_NAME", defaults.SCRAPROM_JOB_NAME)
        timeout = self.crawler.settings.get("SCRAPROM_PUSH_TIMEOUT", defaults.SCRAPROM_PUSH_TIMEOUT)
        grouping_key = self._get_grouping_key()
        pushadd_to_gateway(gateway, job, self.registry, grouping_key, timeout)

    def set_gauge_value(self, key, spider):
        labelnames, labelvalues = ['spider'], [spider.name if spider else '']
        value = self._stats[key]
        if isinstance(value, (int, float)):     # ignore start_time and finish_time ...
            pmetric = self.get_parent_metric(key, Gauge, labelnames)
            pmetric.labels(*labelvalues).set(value)

    def get_parent_metric(self, key, metric_type, labelnames=()):
        metric_prefix = self.crawler.settings.get('SCRAPROM_METRIC_PREFIX', defaults.SCRAPROM_METRICS_PREFIX)
        metric_name = '{0}_{1}'.format(metric_prefix, key.replace('/', '_')).lower()
        metric_key = tuple([key])
        if metric_key not in self.metrics:
            # > Register the multi-wrapper parent metric, or if a label-less metric, the whole shebang. (from prometheus/client_python.metrics.py)
            self.metrics[metric_key] = metric_type(metric_name, key, labelnames=labelnames, registry=self.registry)
        return self.metrics[metric_key]

    def _get_grouping_key(self):
        grouping_key = {}
        try:
            grouping_key['instance'] = socket.gethostname()
        except:
            grouping_key['instance'] = ''
        
        return grouping_key


class PromStatsCollector(PromMixIn, MemoryStatsCollector):
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
        super().__init__(crawler)
        self.crawler = crawler
        
        self.metrics = {}
        self.registry = CollectorRegistry(auto_describe=True)
        
        self.tasks = []
        self.update_interval = self.crawler.settings.get("SCRAPROM_UPDATE_INTERVAL", defaults.SCRAPROM_UPDATE_INTERVAL)

        self.crawler.signals.connect(self.engine_started, signals.engine_started)
        self.crawler.signals.connect(self.engine_stopped, signals.engine_stopped)

    def engine_started(self):
        tsk = task.LoopingCall(self.update)
        self.tasks.append(tsk)
        tsk.start(self.update_interval, now=True)

    def engine_stopped(self):
        for tsk in self.tasks:
            if tsk.running:
                tsk.stop()

    def set_value(self, key, value, spider=None):
        spider = self._checked_spider(spider)
        super().set_value(key, value, spider=spider)
        self.set_gauge_value(key, spider)

    def inc_value(self, key, count=1, start=0, spider=None):
        spider = self._checked_spider(spider)
        super().inc_value(key, count=count, start=start, spider=spider)

        labelnames, labelvalues = ['spider'], [spider.name if spider else '']
        pmetric = self.get_parent_metric(key, Counter, labelnames)
        pmetric.labels(*labelvalues).inc(count)

    def max_value(self, key, value, spider=None):
        spider = self._checked_spider(spider)
        super().max_value(key, value, spider=spider)
        self.set_gauge_value(key, spider)

    def min_value(self, key, value, spider=None):
        spider = self._checked_spider(spider)
        super().min_value(key, value, spider=spider)
        self.set_gauge_value(key, spider)

    def _checked_spider(self, spider):
        if spider is None:
            spider = getattr(self.crawler, 'spider', None)
        return spider

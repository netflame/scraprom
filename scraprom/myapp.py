#!/usr/bin/env python
# -*- coding: utf-8 -*-

from aiohttp import web
from prometheus_client import CollectorRegistry, generate_latest
from multiprocessing import Process

MY_REGISTRY = CollectorRegistry(auto_describe=True)

app, running = None, False

async def metrics(request):
    data = generate_latest(registry=MY_REGISTRY)
    return web.Response(body=data, content_type='text/plain')

def init_app(metrics_path, *args, **kwargs):
    global app
    if app is None:
        mpath = '/' + metrics_path.lstrip('/')
        app = web.Application()
        app.add_routes([web.get(mpath, metrics)])
    return app

def run_app(host, port):
    def run():
        web.run_app(app, host=host, port=port)

    global running
    if running:
        return

    p = Process(target=run)
    p.daemon = True
    p.start()
    running = True

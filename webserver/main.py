# -*- coding:utf8 -*-
import os
import tornado.ioloop
import tornado.web

import httpserver


def make_app():
    return tornado.web.Application([
        ('/', httpserver.MainHandler),
        ('/status', httpserver.StatusHandler),
        ('/init', httpserver.InitHandler),
        ('/clock', httpserver.ClockHandler),
        (r"/uploads/(.*)", tornado.web.StaticFileHandler, dict(path=os.path.join(os.path.dirname(__file__), "uploads")))
    ])


if __name__ == '__main__':
    print('WebServer Start ...')
    # 启动WEB站点
    app = make_app()
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()

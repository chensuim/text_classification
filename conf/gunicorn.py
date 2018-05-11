# encoding: utf-8
bind = '0.0.0.0:5000'
workers = 1
threads = 1
# 在fork出woker进程前，加载app.py代码(主要是读取大量图片费时)，加快启动时间
preload_app = True
daemon = True
pidfile = '../gunicorn.pid'

def post_worker_init(worker):
    pass

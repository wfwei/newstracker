# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 12, 2012

@author: plex
'''

from django.conf import settings
settings.configure(
    DATABASE_ENGINE=u'django.db.backends.mysql',
    DATABASE_NAME=u'newstracker',
    DATABASE_USER=u'wangfengwei',
    DATABASE_PASSWORD=u'wangfengwei',
    DATABASE_HOST=u'110.76.40.188',
)
from dbop import *


if __name__ == '__main__':
    from newstracker.newstrack.models import Weibo, Topic, News, Task
    rtasks = get_tasks(type=u'remind', count=3)
    print 'get remind tasks:', rtasks

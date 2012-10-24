#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 12, 2012

@author: plex
'''

from django.conf import settings
settings.configure(
    DATABASE_ENGINE = 'django.db.backends.mysql',
    DATABASE_NAME = 'newstracker',
    DATABASE_USER = 'root',
    DATABASE_PASSWORD = 'wangfengwei',
    DATABASE_HOST = 'localhost',
    TIME_ZONE = 'America/New_York',
)
from dbop import *
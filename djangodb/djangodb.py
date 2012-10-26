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
    DATABASE_USER = 'wangfengwei',
    DATABASE_PASSWORD = 'wangfengwei',
    DATABASE_HOST = 'localhost',
)
from dbop import *

#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 6, 2012

@author: plex
'''

from libgreader import GoogleReader
from libgnews import googlenews
from djangodb import djangodb
from djangodb import dbop
from libweibo import weiboAPI

from newstracker.account.models import Account
from django.contrib.auth.models import User

from datetime import datetime
import re
import os
import json

_DEBUG = True

### Init google reader
#reader = GoogleReader()
#if _DEBUG:
#    print 'Google Reader 登录信息:\t' , reader.getUserInfo()['userName']
#
### Init weibo
#weibo = weiboAPI.weiboAPI()
#if _DEBUG:
#    print 'Sina Weibo 登录信息:\t' , weibo.getUserInfo()['id']



if __name__ == '__main__':
    print str(os.getcwd()) + '/../newstracker/newstrack/static/news.timeline/'
    pass
    

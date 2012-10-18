#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 6, 2012

@author: plex
'''

from libgreader import GoogleReader
from libgnews import googlenews
from djangodb import djangodb
from libweibo import weiboAPI

from newstracker.account.models import Account
from django.contrib.auth.models import User

from datetime import datetime
import re

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
#    weibo.postComment(weibo_id = 3502066586256490, content = 'post succeed！')
    i = djangodb.Weibo.objects.get(id=12)
    i.delete()
    a = Account.objects.get(id = 4)
    a.delete()
    pass
    

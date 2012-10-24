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

import json

_DEBUG = True

### Init google reader
#reader = GoogleReader()
#if _DEBUG:
#    print 'Google Reader 登录信息:\t' , reader.getUserInfo()['userName']
#
### Init weibo
weibo = weiboAPI.weiboAPI()
#if _DEBUG:
#    print 'Sina Weibo 登录信息:\t' , weibo.getUserInfo()['id']



if __name__ == '__main__':
    print dbop.get_last_mention_id()
#    weibo.postComment(weibo_id = 3504267275499498, content = 'post succeed！')
#    i = djangodb.Weibo.objects.get(id=12)
#    i.delete()
#    a = Account.objects.get(id = 4)
#    a.delete()
    news = {"startDate":"2011,12,10",
            "endDate":"2011,12,11",
            "headline":"Headline Goes Here",
            "text":"<p>Body text goes here, some HTML is OK</p>",
            "tag":"This is Optional",
            "asset": {
                "media":"http://twitter.com/ArjunaSoriano/status/164181156147900416",
                "thumbnail":"optional-32x32px.jpg",
                "credit":"Credit Name Goes Here",
                "caption":"Caption text goes here"
            }
    }
    f = open('/home/plex/wksp/eclipse/newstracker/newstracker/newstrack/static/news.timeline/tmp.jsonp', 'w+')
    f.write('storyjs_jsonp_data = ')
    f = open('/home/plex/wksp/eclipse/newstracker/newstracker/newstrack/static/news.timeline/tmp.jsonp', 'a')
    json.dump(news, f)
    print news
    pass
    

# !/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on Oct 12, 2012

@author: plex
'''

class GoogleNews(object):
    '''
    根据topic,生成GoogleNews的RSS
    '''


    def __init__(self, topic):
        '''
        Constructor
        '''
        self.topic = topic
        self.rss = None
        self.sort = None

    def getRss(self):
        return u'feed/http://news.google.com.hk/news?hl=zh-CN&gl=cn&q=%s&um=1&ie=UTF-8&output=rss' % self.topic

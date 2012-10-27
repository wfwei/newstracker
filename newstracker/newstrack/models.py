#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 12, 2012

@author: plex
'''

from django.db import models
from newstracker.account import models as account_models
import datetime


class Weibo(models.Model):
    weibo_id = models.BigIntegerField(unique=True, db_index=True)
    created_at = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    text = models.CharField(max_length=400)
    in_reply_to_status_id = models.BigIntegerField(default = 0)
    in_reply_to_user_id = models.BigIntegerField(default = 0)
    in_reply_to_screen_name = models.CharField(max_length=100)
    reposts_count = models.IntegerField(default = 0)
    comments_count = models.IntegerField(default = 0)
    
    user = models.ForeignKey(account_models.Account, blank=True, null=True)
    
    def __unicode__(self):
        return '[Weibo , ' + str(self.weibo_id) + ']'
    
    class Meta:
        ordering = ["-created_at"]

class Topic(models.Model):
    '''
    话题模块，话题只有watcher,没有保存创建者信息
    '''
    title = models.CharField(max_length=200, unique=True, db_index=True)
    rss = models.CharField(max_length=400)
    time = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    ##　recent_news_title, recent_news_link都是属性，数据库中无
    recent_news_title = ''
    recent_news_link = ''
    watcher = models.ManyToManyField(account_models.Account)
    watcher_weibo = models.ManyToManyField(Weibo)
    
    def __unicode__(self):
        return '[Topic , ' + self.title + ']'
    
    class Meta:
        ordering = ["-time"]

class News(models.Model):

    title = models.CharField(max_length=100, db_index=True)
    link = models.CharField(max_length=400)
    pubDate = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    summary = models.TextField(blank=True)
    page = models.TextField(blank=True)
    content = models.TextField(blank=True)

    topic = models.ManyToManyField(Topic)

    def __unicode__(self):
        return '[News, ' + self.title + ']'
    
    class Meta:
        ordering = ["-pubDate"]
   


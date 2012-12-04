# !/usr/bin/python
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
    in_reply_to_status_id = models.BigIntegerField(default=0)
    in_reply_to_user_id = models.BigIntegerField(default=0)
    in_reply_to_screen_name = models.CharField(max_length=100)
    reposts_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)

    user = models.ForeignKey(account_models.Account, blank=True, null=True)

    def __unicode__(self):
        return '[Weibo , ' + str(self.weibo_id) + ']'

    class Meta:
        ordering = ["-weibo_id"]

class AliveTopicManager(models.Manager):
    def get_query_set(self):
        return super(AliveTopicManager, self).get_query_set().exclude(state=0)

class Topic(models.Model):
    '''
    话题模块，话题只有watcher,没有保存创建者信息
    '''
    title = models.CharField(max_length=200, unique=True, db_index=True)
    rss = models.CharField(max_length=400)
    time = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    # 　recent_news_title, recent_news_link都是属性，数据库中无
    timeline_ready = True
    recent_news = {}  # 这是一个类变量！！！ [{title:title, link:link},...,{title:title, link:link}]
    watcher = models.ManyToManyField(account_models.Account, blank=True)
    watcher_weibo = models.ManyToManyField(Weibo, blank=True)

    # 话题状态 0:dead;1:normal;2:active...
    state = models.IntegerField(default=1, db_index=True)

    objects = models.Manager()  # The default manager.
    alive_objects = AliveTopicManager()  # The Dahl-specific manager.

    def __unicode__(self):
        return '[Topic , ' + self.title + ']'

    class Meta:
        ordering = ["-time"]

    def count_watcher(self):
        return self.watcher.count()

    def alive(self):
        return self.state > 0

    def activate(self):
        self.state += 1

    def delete(self, *args, **kwargs):
        # 将话题状态改为死亡
        self.state = 0
        self.save()
#        super(Topic, self).delete(*args, **kwargs)  # Call the "real" save() method.

class News(models.Model):

    title = models.CharField(max_length=100, db_index=True, unique=True)
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

class Task(models.Model):
    # remind:remind user topic updates; subscribe:subscribe topic; unsubscribe:unsubscribe
    type = models.CharField(max_length=50, db_index=True)
    # topic to remind or subscribe
    topic = models.ForeignKey(Topic, blank=True)
    status = models.IntegerField(default=1, db_index=True)  # 0:dead;1:alive;2:important;3...more important
    time = models.DateTimeField(default=datetime.datetime.now, db_index=True)

    def __unicode__(self):
        return '[Task, ' + str(self.type) + ',' + self.topic.title + ']'

    class Meta:
        ordering = ["-status"]

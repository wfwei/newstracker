#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Nov 1, 2012

@author: plex
'''
from djangodb import djangodb
from libgnews import googlenews
from newstimeline import create_or_update_news_timeline

from datetime import datetime
import time

import __builtin__
reader = __builtin__.reader
reader_lock = __builtin__.reader_lock
readerlogger = __builtin__.readerlogger
_DEBUG = __builtin__._DEBUG

def fetchRssUpdates():
    '''
    检查更新rss订阅源,并存储更新的新闻,之后标记rss为已读
    debug模式下,如果数据库中找不到订阅的rss,则会创建之
    '''
    readerlogger.debug('Start fetch rss update')
    reader_lock.acquire()
    unreadFeedsDict = reader.getUnreadFeeds()
    reader_lock.release()
    readerlogger.debug('keys of unreadFeedsDict:\t' + str(unreadFeedsDict.keys()))
    for feed in unreadFeedsDict.keys():
        if(feed.startswith('feed')):
            excludeRead = True
            continuation = None
            over = False

            while not over:
                reader_lock.acquire()
                feedContent = reader.fetchFeedItems(feed, excludeRead, continuation)
                reader_lock.release()
                try:
                    continuation = feedContent['continuation']
                    if not continuation:
                        raise KeyError
                except KeyError:
                    over = True

                itemSet = feedContent['items']
                ## title的形式:"镜头里的萝莉 - Google 新闻"  要截断后面的
                feedTopic = feedContent['title'][0:feedContent['title'].find(' - Google ')]

                readerlogger.debug('feed topic:\t', feedTopic, '\t item size:\t', len(itemSet))

                try:
                    topic = djangodb.Topic.objects.get(title = feedTopic)
                except djangodb.Topic.DoesNotExist:
                    if _DEBUG:
                        ## debug 模式下，如果数据库中不存在reader中订阅的话题，则本地重建
                        topicrss = googlenews.GoogleNews(feedTopic).getRss()
                        topic = djangodb.Topic.objects.create(title = feedTopic,
                                                              rss = topicrss,
                                                              time = datetime.now())
                        readerlogger.warn('#' + feedTopic + '# 不存在, 重建后保存数据库')
                    else:
                        readerlogger.error('无法在数据库中找到对应话题,跳过该feed:' + feedTopic)
                        break

                for item in itemSet:
                    title = item['title']
                    pubDate = datetime.fromtimestamp(float(item['published']))
                    summary = item['summary']
                    try:
                        link = item['alternate'][0]['href']
                    except:
                        readerlogger.warn('fail to extract link from alternate attr\n' + str(item))
                        link = 'http://www.fakeurl.com'
                    if '&url=http' in link:
                        link = link[link.find('&url=http')+5:]
                    nnews, created = djangodb.News.objects.get_or_create(title = title)
                    if created:
                        nnews.link = link
                        nnews.pubDate = pubDate
                        nnews.summary = summary
                    nnews.topic.add(topic)
                    nnews.save()


            ## 标记该feed为全部已读
            try:
                reader_lock.acquire()
                if not reader.markFeedAsRead(feed):
                    readerlogger.error('Error in mark ' + feedTopic + ' as read!!!')
                else:
                    readerlogger.debug('Succeed mark ' + feedTopic + ' as read')
                reader_lock.release()
            except:
                readerlogger.error('fail to mark feed as read:' + feedTopic)
                readerlogger.error('reader.auth:\n', reader.auth)
                return

            ##　更新话题的news timeline
            readerlogger.debug('begin update news.timeline for:' + feedTopic + '#')
            create_or_update_news_timeline(feedTopic)

            ## 添加提醒任务
            readerlogger.debug('add remind user topic(#%s#) updates task to taskqueue' % feedTopic)
            djangodb.add_task(topic = topic, type = 'remind')

    readerlogger.debug('Fetch rss update over')

def t_checkreader():
    while True:
        readerlogger.info('Start fetching rss updates')
        fetchRssUpdates()
        readerlogger.info('Start sleep for 3 hours' )
        time.sleep(3*60*60)

        if time.localtime().tm_hour > 0 and time.localtime().tm_hour < 7:
            readerlogger.info('night sleep for ' + str(7-time.localtime().tm_hour) +' hours')
            time.sleep((7-time.localtime().tm_hour) * 60 *60)

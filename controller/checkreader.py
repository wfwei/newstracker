# !/usr/bin/python
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
readerlogger = __builtin__.readerlogger

_DEBUG = False

def fetchRssUpdates():
    '''
    检查更新rss订阅源,并存储更新的新闻,之后标记rss为已读
    debug模式下,如果数据库中找不到订阅的rss,则会创建之
    '''
    readerlogger.debug('Start fetch rss update')
    unreadFeedsDict = reader.getUnreadFeeds()
    time.sleep(20)  # set request interval
    readerlogger.debug('keys of unreadFeedsDict:\t' + str(unreadFeedsDict.keys()))
    for feed in unreadFeedsDict.keys():
        if(feed.startswith('feed')):
            excludeRead = True
            continuation = None
            over = False
            topic = None

            while not over:
                feedContent = reader.fetchFeedItems(feed, excludeRead, continuation)
                time.sleep(20)  # set request interval
                try:
                    continuation = feedContent['continuation']
                    if not continuation:
                        raise KeyError
                except KeyError:
                    over = True

                itemSet = feedContent['items']
                # title的形式:"镜头里的萝莉 - Google 新闻"  要截断后面的
                feedTopic = feedContent['title'][0:feedContent['title'].find(' - Google ')]

                readerlogger.debug('feed topic:\t' + feedTopic + '\t item size:\t' + str(len(itemSet)))

                try:
                    topic = djangodb.Topic.objects.get(title=feedTopic)
                    if not topic.alive():
                        readerlogger.info('topic %s is already dead, unsubscribe!' % topic.title)
                        djangodb.add_task(topic=topic, type='unsubscribe')
                        break
                except djangodb.Topic.DoesNotExist:
                    readerlogger.warn('无法在数据库中找到对应话题,建议手动取消订阅：' + feedTopic)
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
                        link = link[link.find('&url=http') + 5:]
                    nnews, created = djangodb.News.objects.get_or_create(title=title)
                    if created:
                        nnews.link = link
                        nnews.pubDate = pubDate
                        nnews.summary = summary
                    nnews.topic.add(topic)
                    readerlogger.info("add news:%s to topic:%s" % (nnews.title, topic.title))
                    nnews.save()

            if topic:
                # 标记该feed为全部已读
                try:
                    if not reader.markFeedAsRead(feed):
                        readerlogger.error('Error in mark ' + feedTopic + ' as read!!!')
                    else:
                        readerlogger.debug('Succeed mark ' + feedTopic + ' as read')
                except:
                    readerlogger.error('fail to mark feed as read:' + feedTopic)
                    readerlogger.error('reader.auth:' + str(reader.auth))
                    return  # TODO: 会执行finally么？？
                finally:
                    time.sleep(20)  # set request interval

                # 　更新话题的news timeline
                readerlogger.debug('begin update news.timeline for:' + feedTopic + '#')
                create_or_update_news_timeline(feedTopic)

                # 添加提醒任务
                readerlogger.debug('add remind user topic(#%s#) updates task to taskqueue' % feedTopic)
                djangodb.add_task(topic=topic, type='remind')

    readerlogger.debug('Fetch rss update over')

def t_checkreader():
    while True:
        readerlogger.info('Start fetching rss updates')
        try:
            fetchRssUpdates()
        except:
            readerlogger.exception('Except in fetchRssUpdates')
        readerlogger.info('Start sleep for 3 hours')
        time.sleep(6 * 60 * 60)

        if time.localtime().tm_hour > 0 and time.localtime().tm_hour < 7:
            readerlogger.info('night sleep for ' + str(7 - time.localtime().tm_hour) + ' hours')
            time.sleep((7 - time.localtime().tm_hour) * 60 * 60)

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
import __builtin__
import time
import logging
logger = logging.getLogger('checkreader')
hdlr = logging.FileHandler('checkreader.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
hdlr2 = logging.FileHandler('main.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr2.setFormatter(formatter)
logger.addHandler(hdlr2)
logger.setLevel(logging.DEBUG)

reader = __builtin__.reader
reader_lock = None
_DEBUG = True

def fetchRssUpdates():
    '''
    检查更新rss订阅源,并存储更新的新闻,之后标记rss为已读
    debug模式下,如果数据库中找不到订阅的rss,则会创建之
    '''
    logger.debug('Start fetch rss update')
    reader_lock.acquire()
    unreadFeedsDict = reader.getUnreadFeeds()
    reader_lock.release()
    logger.debug('keys of unreadFeedsDict:\t', unreadFeedsDict.keys())
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

                logger.debug('feed topic:\t', feedTopic, '\t item size:\t', len(itemSet))

                try:
                    topic = djangodb.Topic.objects.get(title = feedTopic)
                except djangodb.Topic.DoesNotExist:
                    if _DEBUG:
                        ## debug 模式下，如果数据库中不存在reader中订阅的话题，则本地重建
                        topicrss = googlenews.GoogleNews(feedTopic).getRss()
                        topic = djangodb.Topic.objects.create(title = feedTopic,
                                                              rss = topicrss,
                                                              time = datetime.now())
                        logger.warn('#' + feedTopic + '# 不存在, 重建后保存数据库')
                    else:
                        logger.error('无法在数据库中找到对应话题,跳过该feed:' + feedTopic)
                        break

                for item in itemSet:
                    title = item['title']
                    pubDate = datetime.datetime.fromtimestamp(float(item['published']))
                    summary = item['summary']
                    try:
                        link = item['alternate'][0]['href']
                    except:
                        logger.warn('fail to extract link from alternate attr\n' + str(item))
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
                    logger.error('Error in mark ' + feedTopic + ' as read!!!')
                else:
                    logger.debug('Succeed mark ' + feedTopic + ' as read')
                reader_lock.release()
            except:
                logger.error('fail to mark feed as read:' + feedTopic)
                logger.error('reader.auth:\n', reader.auth)
                return

            ##　更新话题的news timeline
            logger.debug('begin update news.timeline for:' + feedTopic + '#')
            create_or_update_news_timeline(feedTopic)

            ## 添加提醒任务
            logger.debug('add remind user topic(#%s#) updates task to taskqueue' % feedTopic)
            djangodb.add_remind_user_task(topic = topic)

    logger.debug('Fetch rss update over')

def t_checkreader(r_lock):
    global reader_lock
    reader_lock = r_lock

    while True:
        logger.info('Start fetching rss updates')
        fetchRssUpdates()
        logger.info('Start sleep for 2 hours' )
        time.sleep(2*60*60)

        if time.localtime().tm_hour > 0 and time.localtime().tm_hour < 7:
            logger.info('night sleep for ' + str(7-time.localtime().tm_hour) +' hours')
            time.sleep((7-time.localtime().tm_hour) * 60 *60)

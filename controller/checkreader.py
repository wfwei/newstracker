# !/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Nov 1, 2012

@author: plex
'''
from newstimeline import create_or_update_news_timeline
from djangodb import djangodb
from datetime import datetime
from utils import reqInterval
import logging
import time


# setup logging
logger = logging.getLogger(u'reader-logger')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(u'../logs/checkreader.log')
fh.setLevel(logging.DEBUG)
# create console handler with warn log level
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
# create logger output formater
formatter = logging.Formatter(u'%(asctime)s %(name)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

# setup google reader
from libgreader import readerAPI
[access_token, refresh_token, access_expires] = djangodb.get_google_auth_info(u_id=1)
reader = readerAPI.readerAPI(u_id=1, access_token=access_token, \
                   refresh_token=refresh_token, expires_access=access_expires)
logger.info(u'Google Reader 登录信息:%s' % reader.getUserInfo()[u'userName'])
reqInterval(31)


def fetchRssUpdates():
    '''
    检查更新rss订阅源,并存储更新的新闻,之后标记rss为已读
    '''
    logger.info(u'\nStart fetch rss update\n')
    unreadFeedsDict = reader.getUnreadFeeds()
    logger.info(u'get %d unread feeds' % len(unreadFeedsDict))
    reqInterval()
    for feed in unreadFeedsDict.keys():
        if(feed.startswith(u'feed')):
            excludeRead = True
            continuation = None
            topic = None
            over = False
            while not over:
                try:
                    feedContent = reader.fetchFeedItems(feed, excludeRead, continuation)
                    # title的形式:"镜头里的萝莉 - Google 新闻"  要截断后面的
                    feedTopic = feedContent[u'title'][0:-12]
                    itemSet = feedContent[u'items']
                except:
                    logger.exception(u'failed to fetch feed items, sleep 123s and retry again')
                    reqInterval(123)
                    continue
                else:
                    logger.info('Fetch %d feed items of topic %s' % (len(itemSet), feedTopic))
                    reqInterval(31)

                try:
                    continuation = feedContent[u'continuation']
                    if not continuation:
                        over = True
                except:
                    logger.info(u'fail to extract continuation, may well be normal(over)')
                    over = True
                else:
                    logger.info('Extract continuation:%s' % continuation)


                try:
                    topic = djangodb.Topic.objects.get(title=feedTopic)
                    if not topic.alive():
                        logger.warn(u'topic %s is already dead, unsubscribe!' % topic.title)
                        djangodb.add_task(topic=topic, type=u'unsubscribe')
                        break
                except:
                    logger.exception(u'topic:%s not found in database, manually unsubscribe!' % feedTopic)
                    break

                for item in itemSet:
                    title = item[u'title']
                    pubDate = datetime.fromtimestamp(float(item[u'published']))
                    try:
                        summary = item[u'summary']
                    except:
                        logger.exception(u'fail to extract summary from: %s' % item)
                        summary = u'Fail to extract summary==!'
                    link = item[u'alternate'][0][u'href']
                    if '&url=http' in link:
                        link = link[link.find(u'&url=http') + 5:]
                    nnews, created = djangodb.News.objects.get_or_create(title=title)
                    if created:
                        nnews.link = link
                        nnews.pubDate = pubDate
                        nnews.summary = summary
                    nnews.topic.add(topic)
                    nnews.save()
                    logger.info("add news:%s to topic:%s" % (nnews.title, topic.title))

            if topic:
                # 标记该feed为全部已读
                try:
                    sucInMarkAsRead = reader.markFeedAsRead(feed)
                except:
                    sucInMarkAsRead = False
                    logger.exception(u'Fail to mark feedtopic:%s as read!!!' % feedTopic)
                finally:
                    if sucInMarkAsRead:
                        logger.info(u'Succeed to mark feedtopic:%s as read!!!' % feedTopic)
                    else:
                        logger.error(u'Fail to mark feedtopic:%s as read!!!' % feedTopic)
                    reqInterval(31)

                # 　更新话题的news timeline
                logger.info(u'Update news timeline for topic:%s' % feedTopic)
                create_or_update_news_timeline(feedTopic)

                # 添加提醒任务
                logger.debug(u'Add remind task for topic:%s' % feedTopic)
                djangodb.add_task(topic=topic, type=u'remind')

    logger.debug(u'\nFetch rss update over\n')

if __name__ == u'__main__':
    while True:
        try:
            fetchRssUpdates()
        except Exception, e:
            logger.exception(u'Except in fetchRssUpdates')
            logger.info(u'Sleep for 10 minutes to restart fetch rss updates')
            reqInterval(600)
        else:
            logger.info(u'Start sleep for 6 hours')
            reqInterval(6 * 60 * 60)

        if time.localtime().tm_hour > 0 and time.localtime().tm_hour < 7:
            logger.info(u'night sleep for %d hours' % (7 - time.localtime().tm_hour))
            reqInterval((7 - time.localtime().tm_hour) * 60 * 60)

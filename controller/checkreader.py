# !/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Nov 1, 2012

@author: plex
'''
from newstimeline import create_or_update_news_timeline
from djangodb import djangodb
from datetime import datetime
import logging
import time

# setup logging
logger = logging.getLogger('reader-logger')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('../logs/checkreader.log')
fh.setLevel(logging.DEBUG)
# create console handler with warn log level
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
# create logger output formater
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

# setup google reader
from libgreader import readerAPI
[access_token, refresh_token, access_expires] = djangodb.get_google_auth_info(u_id=1)
reader = readerAPI.readerAPI(u_id=1, access_token=access_token, \
                   refresh_token=refresh_token, expires_access=access_expires)
time.sleep(31)
logger.info(u'Google Reader 登录信息:\t' + reader.getUserInfo()['userName'])


def fetchRssUpdates():
    '''
    检查更新rss订阅源,并存储更新的新闻,之后标记rss为已读
    '''
    logger.info('\nStart fetch rss update\n')
    unreadFeedsDict = reader.getUnreadFeeds()
    time.sleep(20)  # set request interval
    logger.info('keys of unreadFeedsDict:\n\t' + str(unreadFeedsDict.keys()))
    for feed in unreadFeedsDict.keys():
        if(feed.startswith('feed')):
            excludeRead = True
            continuation = None
            topic = None
            over = False
            while not over:
                try:
                    feedContent = reader.fetchFeedItems(feed, excludeRead, continuation)
                except TypeError, te:
                    logger.warn('feedContent fetch error:\n\t' + str(te))
                    logger.warn('sleep 123s and retry once')
                    time.sleep(123)
                    try:
                        feedContent = reader.fetchFeedItems(feed, excludeRead, continuation)
                    except Exception, e:
                        logger.error('fail again to fetch feedContent:\n\t' + str(e))
                        break
                finally:
                    time.sleep(31)

                try:
                    continuation = feedContent['continuation']
                    if not continuation:
                        raise KeyError
                except (KeyError, Exception), e:
                    logger.info('Info:\n\t%s is None:' % str(e))
                    over = True

                itemSet = feedContent['items']
                # title的形式:"镜头里的萝莉 - Google 新闻"  要截断后面的
                feedTopic = feedContent['title'][0:feedContent['title'].find(' - Google ')]

                logger.info('feed topic:\t' + feedTopic + '\t item size:\t' + str(len(itemSet)))

                try:
                    topic = djangodb.Topic.objects.get(title=feedTopic)
                    if not topic.alive():
                        logger.info('topic %s is already dead, unsubscribe!' % topic.title)
                        djangodb.add_task(topic=topic, type='unsubscribe')
                        break
                except djangodb.Topic.DoesNotExist, dne:
                    logger.warn('topic(%s) not found in database,manually unsubscribe!\n\t%s' % (feedTopic, str(dne)))
                    break

                for item in itemSet:
                    title = item['title']
                    pubDate = datetime.fromtimestamp(float(item['published']))
                    try:
                        summary = item['summary']
                    except:
                        logger.warn('fail to extract summary:\n' + str(item))
                        summary = ''
                    link = item['alternate'][0]['href']
                    if '&url=http' in link:
                        link = link[link.find('&url=http') + 5:]
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
                    if not reader.markFeedAsRead(feed):
                        logger.error('Error in mark ' + feedTopic + ' as read!!!')
                    else:
                        logger.info('Succeed mark ' + feedTopic + ' as read')
                except Exception, e:
                    logger.error('fail to mark feed(%s) as read!!!\n\t%s' % (feedTopic, str(feedTopic)))
                finally:
                    time.sleep(31)

                # 　更新话题的news timeline
                logger.info('begin update news.timeline for:#' + feedTopic + '#')
                create_or_update_news_timeline(feedTopic)

                # 添加提醒任务
                logger.debug('add remind task for topic(#%s#) ' % feedTopic)
                djangodb.add_task(topic=topic, type='remind')

    logger.debug('\nFetch rss update over\n')

if __name__ == '__main__':
    while True:
        try:
            fetchRssUpdates()
        except Exception, e:
            logger.error('Except in fetchRssUpdates:\n\t' + str(e))
            logger.info('Sleep for 10 minutes to restart fetch rss updates')
            time.sleep(600)
        else:
            logger.info('Start sleep for 6 hours')
            time.sleep(6 * 60 * 60)

        if time.localtime().tm_hour > 0 and time.localtime().tm_hour < 7:
            logger.info('night sleep for ' + str(7 - time.localtime().tm_hour) + ' hours')
            time.sleep((7 - time.localtime().tm_hour) * 60 * 60)

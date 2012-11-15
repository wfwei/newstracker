#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 1, 2012

@author: plex
'''
from djangodb import djangodb

import __builtin__
import time

weibo = __builtin__.weibo
reader = __builtin__.reader
logger = __builtin__.tasklogger
readerlogger = __builtin__.readerlogger
weibologger = __builtin__.weibologger

def remindUserTopicUpdates(topicTitle):
    logger.debug('Start remind user for topic: ' + topicTitle)
    try:
        topic = djangodb.Topic.objects.get(title = topicTitle)
        topic_news = topic.news_set.all()[0]
    except djangodb.Topic.DoesNotExist:
        logger.error('Topic:\t' + topicTitle + ' not exist!!!')
        return False
    except:
        logger.debug('No news update for topic:\t' + topicTitle)
        return False
    topicWatchers = topic.watcher.all()
    topicWatcherWeibo = topic.watcher_weibo.all()

    postMsg = '#' + str(topicTitle) + '# 有新进展：' + str(topic_news.title) + \
    '『' + weibo.getShortUrl("http://110.76.40.188:81/news_timeline/" + str(topic.id)) + '』'
    time.sleep(61) ## 间隔两次请求
    if len(postMsg) > 139:
        postMsg = postMsg[:139]

    logger.debug('topicWatchers: \n' + str(topicWatchers))
    logger.debug('topicWatcherWeibo:\n' + str(topicWatcherWeibo))

    _user_reminded = []

    for watcherWeibo in topicWatcherWeibo:
        targetStatusId = watcherWeibo.weibo_id
        logger.debug('\tpostMsg:\n' + postMsg)
        ## 如果微博不存在，则将该微博记录从topic的链接中删除,否则添加到已经提醒的用户列表中
        if not weibo.postComment(weibo_id = targetStatusId, content = postMsg):
            topic.watcher_weibo.remove(watcherWeibo)
            logger.debug('post comment failed...target status id:%s, postMsg:%s' % (targetStatusId, postMsg))
        else:
            logger.info('Succeed post comment to weibo:' + str(targetStatusId))
            _user_reminded.append(watcherWeibo.user.weiboId)
        time.sleep(61) ## 间隔两次请求
        
    ## 有些用户没有发微博关注该事件(将原有微博删除了)，但也要提醒，首先要剔除已经提醒的_user_commented
    for watcher in topicWatchers:
        weiboId = watcher.weiboId
        if weiboId != 0 and weiboId not in _user_reminded:
            ## 如果用户绑定了微博帐号，且没有发微博订阅该话题
            ## 目前做法：主帐号有一条专门提醒用户话题更新的公用微博，每当用户有要更新的话题时，评论该微博，并＠用户和新闻更新信息
            _postMsg = '@' + watcher.weiboName + ' 您关注的事件' + postMsg
            if len(postMsg) > 139:
                _postMsg = _postMsg[:139]
            logger.info('\tpostMsg:\n' + _postMsg)
            if not weibo.postComment(weibo.REMIND_WEIBO_ID, _postMsg):
                logger.error('post comment failed...target status id:%s, postMsg:%s' % (weibo.REMIND_WEIBO_ID, _postMsg))
            else:
                logger.info('Succeed post comment to (static)weibo:' + str(weibo.REMIND_WEIBO_ID))
            time.sleep(61) ## 间隔两次请求

    logger.info('remindUserTopicUpdates(%s): OK' % topicTitle)
    return True

def subscribeTopic(topicRss, topicTitle = None):
    ## 订阅的时候即便是加了title,最后谷歌还是会在后面加上' - Google 新闻'
    try:
        if not reader.subscribe(feedUrl = topicRss, title = topicTitle):
            logger.error('Fail to subscribed ' + topicRss)
            readerlogger.error('in exetask:Fail to subscribed ' + topicRss)
            return False
        else:
            logger.debug('Succeed to subscribe ' + topicRss)
            readerlogger.debug('in exetask:Succeed to subscribe ' + topicRss)
    except:
        logger.error('Fail to subscribed ' + topicRss)
        return False

    return True

def t_exetask():
    while True:
        subs_tasks = djangodb.get_tasks(type='subscribe', count = 5)
        logger.info('Start execute %d subscribe tasks' % len(subs_tasks))
        for t in subs_tasks:
            try:
                subscribeTopic(topicRss = t.topic.rss, topicTitle = t.topic.title)
                time.sleep(61) ## 间隔两次请求
            except:
                logger.exception("Except in subscribeTopic()")
                break
            t.status = 0 ##更新成功，设置标志位
            t.save()

        remind_tasks = djangodb.get_tasks(type='remind', count = 10)
        logger.info('Start execute %d remind tasks' % len(remind_tasks))
        for t in remind_tasks:
            try:
                remindUserTopicUpdates(topicTitle = t.topic.title)
                time.sleep(61) ## 间隔两次请求
            except:
                logger.exception("Except in remindUserTopicUpdates()")
                break
            t.status = 0 ##更新成功，设置标志位
            t.save()

        logger.info('long sleep for 30 minutes')
        time.sleep(30*60)

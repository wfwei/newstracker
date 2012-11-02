#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 1, 2012

@author: plex
'''

from djangodb import djangodb
from newstimeline import update_all_news_timeline

import __builtin__
import time
import logging
logger = logging.getLogger('exetask')
hdlr = logging.FileHandler('exetask.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
hdlr2 = logging.FileHandler('main.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr2.setFormatter(formatter)
logger.addHandler(hdlr2)
logger.setLevel(logging.DEBUG)

weibo = __builtin__.weibo
reader = __builtin__.reader
weibo_lock = None
reader_lock = None

def remindUserTopicUpdates(topicTitle):
    logger.debug('Start remind user for topic: ' + topicTitle)
    try:
        topic = djangodb.Topic.objects.get(title = topicTitle)
        topic_news = topic.news_set.all()[0]
    except djangodb.Topic.DoesNotExist:
        logger.error('Topic:\t' + topicTitle + ' not exist!!!')
        return
    except:
        logger.debug('No news update for topic:\t' + topicTitle)
        return
    topicWatchers = topic.watcher.all()
    topciWatcherWeibo = topic.watcher_weibo.all()
    ## TODO: 把链接具体到特定的时间线
    weibo_lock.acquire()
    postMsg = '#' + str(topicTitle) + '# 有新进展：' + str(topic_news.title) + '(' + str(weibo.getShortUrl("http://110.76.40.188:81/")) + ')'
    weibo_lock.release()
    if len(postMsg) > 139:
        postMsg = postMsg[:139]

    logger.debug('topicWatchers: \n' + str(topicWatchers))
    logger.debug('topciWatcherWeibo:\n' + str(topciWatcherWeibo))

    _user_reminded = []
    
    for watcherWeibo in topciWatcherWeibo:
        targetStatusId = watcherWeibo.weibo_id
        logger.debug('postMsg:\n' + postMsg)
        ## 如果微博不存在，则将该微博记录从topic的链接中删除,否则添加到已经提醒的用户列表中
        weibo_lock.acquire()
        if not weibo.postComment(weibo_id = targetStatusId, content = postMsg):
            topic.watcher_weibo.remove(watcherWeibo)
            logger.debug('post comment failed...target status id:%s, postMsg:%s' % (targetStatusId, postMsg))
        else:
            _user_reminded.append(watcherWeibo.user.weiboId)
        weibo_lock.release()

    ## 有些用户没有发微博关注该事件(将原有微博删除了)，但也要提醒，首先要剔除已经提醒的_user_commented
    for watcher in topicWatchers:
        weiboId = watcher.weiboId
        if weiboId != 0 and weiboId not in _user_reminded:
            ## 如果用户绑定了微博帐号，且没有发微博订阅该话题
            ## 目前做法：主帐号有一条专门提醒用户话题更新的公用微博，每当用户有要更新的话题时，评论该微博，并＠用户和新闻更新信息
            _postMsg = '@' + watcher.weiboName + ' 您关注的事件' + postMsg + ' ps:登录后可取消关注'
            if len(postMsg) > 139:
                _postMsg = _postMsg[:139]
            logger.debug('postMsg:\n' + _postMsg)
            weibo_lock.acquire()
            if not weibo.postComment(weibo.REMIND_WEIBO_ID, _postMsg):
                logger.error('post comment failed...target status id:%s, postMsg:%s' % (weibo.REMIND_WEIBO_ID, _postMsg))
            weibo_lock.release()
        
    logger.debug('remindUserTopicUpdates(%s): OK' % topicTitle)

def subscribeTopic(topicRss, topicTitle = None):
    ## 订阅的时候即便是加了title,最后谷歌还是会在后面加上' - Google 新闻'
    reader_lock.acquire()
    try:
        if not reader.subscribe(feedUrl = topicRss, title = topicTitle):
            logger.error('Fail to subscribed ' + topicRss)
        else:
            logger.debug('Succeed to subscribe ' + topicRss)
    except:
        logger.error('Fail to subscribed ' + topicRss)
    reader_lock.release()

def t_exetask(w_lock, r_lock):
    global weibo_lock
    global reader_lock
    weibo_lock = w_lock
    reader_lock = r_lock
    
    while True:
        subs_tasks = djangodb.get_tasks(type='subscribe', count = 10)
        remind_tasks = djangodb.get_tasks(type='remind', count = 10)
        
        logger.info('Start execute %d subscribe tasks')
        for t in subs_tasks:
            time.sleep('61')
            subscribeTopic(topicRss = t.topic.rss, topicTitle = t.topic.title)
        logger.info('Start execute %d remind tasks')
        for t in remind_tasks:
            time.sleep('61')
            remindUserTopicUpdates(topicTitle = t.topic.title)
            
        logger.info('long sleep for 30 minutes')
        time.sleep(30*60)
        
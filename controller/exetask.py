# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 1, 2012

@author: plex
'''
from libweibo import weiboAPI
from libweibo.weibo import APIError

from djangodb import djangodb

import __builtin__
import time

weibo = __builtin__.weibo
reader = __builtin__.reader
logger = __builtin__.tasklogger
readerlogger = __builtin__.readerlogger
weibologger = __builtin__.weibologger

_DEBUG = True

def remindUserTopicUpdates(topicTitle):
    try:
        logger.debug('Start remind user for topic: ' + topicTitle)
        topic = djangodb.Topic.objects.get(title=topicTitle)
        if not topic.alive():
            logger.info('topic %s is already dead, add unsubscribe task!' % topicTitle)
            djangodb.add_task(topic=topic, type='unsubscribe')
            return False
        else:
            topic_news = topic.news_set.all()[0]
    except djangodb.Topic.DoesNotExist:
        logger.warn('无法在数据库中找到对应话题,建议手动取消订阅：' + topicTitle)
        return False
    except:
        logger.debug('No news update for topic:\t' + topicTitle)
        return False

    topicWatchers = topic.watcher.all()
    topicWatcherWeibo = topic.watcher_weibo.all()


    '''
    得到订阅该话题的所有用户，分两类，已经授权的和没有授权的
    '''
    watcherWithAuth = set()
    watcherWithoutAuth = set()
    for watcher in topicWatchers:
        if watcher.has_oauth():
            watcherWithAuth.add(watcher)
        else:
            watcherWithoutAuth.add(watcher)

    '''
    筛选出其中需要提醒的用户，分为四类：
    
    watcherWithoutStatusAndAuth
    watcherWithStatusAndAuth
    watcherWithStatusWithoutAuth
    watcherWithoutStatusWithAuth
    '''
    watcherWithStatusAndAuth = set()
    watcherWithStatusWithoutAuth = set()
    for watcherWeibo in topicWatcherWeibo:
        watcher = watcherWeibo.user
        if not watcher.to_remind():
            # 去掉不需要提醒的用户
            continue
        watcher.original_weibo = watcherWeibo  # 人工添加的字段
        if watcher in watcherWithAuth:
            watcherWithStatusAndAuth.add(watcher)
        elif watcher in watcherWithoutAuth:
            watcherWithStatusWithoutAuth.add(watcher)

    # 去掉不需要提醒的用户
    watcherWithoutStatusAndAuth = set([watcher for watcher in (watcherWithoutAuth - watcherWithStatusWithoutAuth) if watcher.to_remind()])
    watcherWithoutStatusWithAuth = set([watcher for watcher in (watcherWithAuth - watcherWithStatusAndAuth) if watcher.to_remind()])

    _msg = '#' + str(topicTitle) + '# 有新进展：' + str(topic_news.title) + \
    '『' + weibo.getShortUrl("http://110.76.40.188:81/news_timeline/" + str(topic.id)) + '』'
    time.sleep(61)  # 间隔两次请求

    if _DEBUG:
        logger.debug('topicWatcherWeibo:\n' + str(topicWatcherWeibo))
        logger.debug('topicWatchers: \n' + str(topicWatchers))
        logger.debug('watcherWithAuth\n' + str(watcherWithAuth))
        logger.debug('watcherWithoutAuth\n' + str(watcherWithoutAuth))
        logger.debug('posgMsg:\n' + _msg)

    _user_reminded = []

    '''
    先更新有授权同时也发过微博的用户的状态
    '''
    for watcher in watcherWithStatusAndAuth:
        '''
        自己转发或评论自己的原始微博提醒自己，如果允许提醒他人的话，顺带提醒～
        '''
        [access_token, expires_in] = djangodb.get_weibo_auth_info(watcher.weiboId)
        _weibo = weiboAPI.weiboAPI(access_token=access_token, \
                                   expires_in=expires_in, \
                                   u_id=watcher.weiboId)
        watcher_btw = None
        if watcher.allow_remind_others and watcherWithStatusWithoutAuth:
            watcher_btw = watcherWithStatusWithoutAuth.pop()
            postMsg = _msg + ' @' + watcher_btw.weiboName + ' 顺便提醒你一下～'
        else:
            postMsg = _msg

        logger.info('remind user:%s topic:%s update with msg:%s' % (watcher.weiboName, topicTitle, postMsg))
        logger.info("originalWeibo: " + str(watcher.original_weibo))
        res = {}
        try:
            if watcher.repost_remind:
                res['type'] = 'repost status'
                res['status'] = _weibo.repostStatus(weibo_id=watcher.original_weibo.weibo_id, content=postMsg)
            else:
                res['type'] = 'comment status'
                res['status'] = _weibo.postComment(weibo_id=watcher.original_weibo.weibo_id, content=postMsg)
        except APIError, err:
            logger.warn("%s failed:\t%s" % (res['type'], err.error))
            if err.error == 'target weibo does not exist!':
                topic.watcher_weibo.remove(watcher.original_weibo)
                topic.watcher.remove(watcher)
                logger.info('remove watcher:%s and delete watcherWeibo:%s' % (str(watcher), str(watcher.original_weibo)))
                watcher.original_weibo.delete()
        except:
            raise
        else:
            logger.info("%s Succeed!" % res['type'])
            if watcher_btw:
                watcher_btw.add_remind()
            watcher.add_remind()
            logger.info('added remind history for user: [%s, %s]' % (watcher.weiboName, str(watcher_btw)))

        time.sleep(61)  # 间隔两次请求

    '''
    更新有授权但没有发过微博的用户的状态
    '''
    for watcher in watcherWithoutStatusWithAuth:
        '''
        发布一条新的微博，如果允许提醒他人的话，顺带提醒～
        '''
        [access_token, expires_in] = djangodb.get_weibo_auth_info(watcher.weiboId)
        _weibo = weiboAPI.weiboAPI(access_token=access_token, \
                                   expires_in=expires_in, \
                                   u_id=watcher.weiboId)
        watcher_btw = None
        if watcher.allow_remind_others and watcherWithStatusWithoutAuth:
            watcher_btw = watcherWithStatusWithoutAuth.pop()
            postMsg = _msg + ' @' + watcher_btw.weiboName + ' 顺便提醒你一下～'
        else:
            postMsg = _msg

        logger.info('remind user:%s topic:%s update with msg:%s' % (watcher.weiboName, topicTitle, postMsg))
        res = {}
        try:
            res['status'] = _weibo.updateStatus(content=postMsg)
        except APIError, err:
            logger.warn("Update status failed:%t" + err.error)
        except:
            raise
        else:
            logger.info("Updating status Succeed!")
            if watcher_btw:
                watcher_btw.add_remind()
            watcher.add_remind()
            logger.info('added remind history for user: [%s, %s]' % (watcher.weiboName, str(watcher_btw)))
            _status = djangodb.get_or_create_weibo(res['status'])
            topic.watcher_weibo.add(_status)
            logger.info('added watcherWeibo:%s to topic:%s' % (_status.text, topicTitle))

        time.sleep(61)  # 间隔两次请求

    '''
    更新没有授权但发过或转发过微博的用户的状态
    '''
    for watcher in watcherWithStatusWithoutAuth:
        '''
        从watcherWithAuth中找个人评论他已有的微博提醒，找不到的话使用主帐号提醒
        '''
        if watcherWithAuth:
            _reminder = watcherWithAuth.pop()
            [access_token, expires_in] = djangodb.get_weibo_auth_info(_reminder.weiboId)
            _weibo = weiboAPI.weiboAPI(access_token=access_token, \
                                       expires_in=expires_in, \
                                       u_id=_reminder.weiboId)
            postMsg = '友情提示：' + _msg + ' PS:您的授权已过期，请登录狗狗追踪授权～'
        else:
            #  如果没有用户可以帮忙，主帐号提醒吧
            _reminder = '主帐号'
            _weibo = weibo
            postMsg = _msg + ' PS:您的授权已过期，请登录狗狗追踪授权～'

        logger.info('remind user:%s topic:%s update with msg:%s' % (watcher.weiboName, topicTitle, postMsg))
        logger.info("_reminder:%s\toriginalWeibo:%s" % (str(_reminder), str(watcher.original_weibo)))

        res = {}
        try:
            res['status'] = _weibo.postComment(weibo_id=watcher.original_weibo, content=postMsg)
        except APIError, err:
            logger.warn("comment failed:\t%s" % (err.error))
            if err.error == 'target weibo does not exist!':
                topic.watcher_weibo.remove(watcher.original_weibo)
                topic.watcher.remove(watcher)
                logger.info('remove watcher:%s and delete watcherWeibo:%s' % (str(watcher), str(watcher.original_weibo)))
                watcher.original_weibo.delete()
        except:
            raise
        else:
            logger.info("comment Succeed!")
            watcher.add_remind()
            logger.info('added remind history for user: %s' % watcher.weiboName)

        time.sleep(61)  # 间隔两次请求

    '''
    既没有授权也没有发过微博
    不再提醒
    '''

def subscribeTopic(topicRss, topicTitle=None):
    # 订阅的时候即便是加了title,最后谷歌还是会在后面加上' - Google 新闻'
    try:
        if not reader.subscribe(feedUrl=topicRss, title=topicTitle):
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

def unSubscribeTopic(topicRss):
    '''
    TODO:该方法不可用，API调用返回OK，但是没有取消订阅。。。
    '''
    try:
        if not reader.unsubscribe(feedUrl=topicRss):
            logger.error('Fail to unsubscribe ' + topicRss)
            readerlogger.error('in exetask:Fail to unsubscribe ' + topicRss)
            return False
        else:
            logger.debug('Succeed to unsubscribe ' + topicRss)
            readerlogger.debug('in exetask:Succeed to unsubscribe ' + topicRss)
    except:
        logger.error('Fail to unsubscribe ' + topicRss)
        return False

    return True

def delTopic(topicTitle):
    '''
    目前还没有用
    '''
    logger.debug('Start delete topic: ' + topicTitle)
    try:
        topic = djangodb.Topic.objects.get(title=topicTitle)
    except djangodb.Topic.DoesNotExist:
        logger.warn('Topic:\t' + topicTitle + ' not exist!!!')
        return False
    except:
        raise

    # 取消订阅
    logger.info('un substribe topic')
    unSubscribeTopic(topic.rss)
    # 数据库中删除该话题的信息
    logger.info('delete news')
    topic.news_set.all().delete()
    logger.info('delete topic(mark topic as dead)')
    topic.delete()
    logger.info('delete topic: ' + topicTitle + ' OK')


def t_exetask():
    while True:
# 　　　　由于取消订阅的API无法成功取消订阅，手动取消～＝＝！
#        unsubs_tasks = djangodb.get_tasks(type='unsubscribe', count=10)
#        logger.info('Start execute %d unsubscribe tasks' % len(unsubs_tasks))
#        for t in unsubs_tasks:
#            try:
#                unSubscribeTopic(topicRss=t.topic.rss)
#                time.sleep(61)  # 间隔两次请求
#            except:
#                logger.exception("Except in unsubscribeTopic()")
#                break
#            t.status = 0  # 更新成功，设置标志位
#            t.save()

        subs_tasks = djangodb.get_tasks(type='subscribe', count=5)
        logger.info('Start execute %d subscribe tasks' % len(subs_tasks))
        for t in subs_tasks:
            try:
                subscribeTopic(topicRss=t.topic.rss, topicTitle=t.topic.title)
                time.sleep(61)  # 间隔两次请求
            except:
                logger.exception("Except in subscribeTopic()")
                break
            t.status = 0  # 更新成功，设置标志位
            t.save()

        remind_tasks = djangodb.get_tasks(type='remind', count=3)
        logger.info('Start execute %d remind tasks' % len(remind_tasks))
        for t in remind_tasks:
            try:
                remindUserTopicUpdates(topicTitle=t.topic.title)
                time.sleep(61)  # 间隔两次请求
            except:
                logger.exception("Except in remindUserTopicUpdates()")
                break
            t.status = 0  # 更新成功，设置标志位
            t.save()

        logger.info('long sleep for 30 minutes')
        time.sleep(15 * 60)

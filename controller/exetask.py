# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 1, 2012

@author: plex
'''
from libweibo import weiboAPI
from libweibo.weibo import APIError
from djangodb import djangodb
from utils import reqInterval
import logging
import time

# setup logging
logger = logging.getLogger(u'task-logger')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(u'../logs/exetask.log')
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

# setup weibo
[access_token, expires_in] = djangodb.get_weibo_auth_info(3041970403)
if time.time() > float(expires_in):
    raise Exception(u'授权过期了，with expires_in:%s' % expires_in)
weibo = weiboAPI.weiboAPI(access_token=access_token, expires_in=expires_in, u_id=3041970403)
reqInterval(31)
logger.info(u'Sina Weibo 登录信息:\t' + weibo.getUserInfo()[u'name'])

# setup google reader
from libgreader import readerAPI
[access_token, refresh_token, access_expires] = djangodb.get_google_auth_info(u_id=1)
reader = readerAPI.readerAPI(u_id=1, access_token=access_token, \
                   refresh_token=refresh_token, expires_access=access_expires)
reqInterval(31)
logger.info(u'Google Reader 登录信息:\t' + reader.getUserInfo()[u'userName'])


def remindUserTopicUpdates(topicTitle):
    try:
        logger.debug(u'Start remind user for topic:%s' % topicTitle)
        topic = djangodb.Topic.objects.get(title=topicTitle)
        if topic.alive():
            topic_news = topic.news_set.all()[0]
        else:
            logger.warn(u'topic:%s is already dead, add unsubscribe task!' % topicTitle)
            djangodb.add_task(topic=topic, type=u'unsubscribe')
            return False
    except:
        logger.exception(u'topic or news may not exist in database')
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

    _shorturl = weibo.getShortUrl(u'http://110.76.40.188/news_timeline/%d' % topic.id)
    _msg = u'#%s#有新进展：%s 『%s』' % (topicTitle, topic_news.title, _shorturl)
    reqInterval(61)

    logger.debug(u'topicWatcherWeibo:%s' % topicWatcherWeibo)
    logger.debug(u'topicWatchers:%s' % topicWatchers)
    logger.debug(u'watcherWithAuth:%s' % watcherWithAuth)
    logger.debug(u'watcherWithoutAuth:%s' % watcherWithoutAuth)
    logger.debug(u'posgMsg:%s' % _msg)

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
            postMsg = _msg + u' @' + watcher_btw.weiboName + u' 顺便提醒你一下～'
        else:
            postMsg = _msg + u' @' + watcher.weiboName

        logger.info(u'remind user:%s \ntopic:%s \nupdate with msg:%s\noriginalWeibo:%s' % \
                     (watcher.weiboName, topicTitle, postMsg, watcher.original_weibo))
        res = {}
        try:
            if watcher.repost_remind:
                res[u'type'] = u'repost status'
                res[u'status'] = _weibo.repostStatus(weibo_id=watcher.original_weibo.weibo_id, content=postMsg)
            else:
                res[u'type'] = u'comment status'
                res[u'status'] = _weibo.postComment(weibo_id=watcher.original_weibo.weibo_id, content=postMsg)
        except APIError, err:
            logger.warn(u'%s failed:\t%s' % (res[u'type'], err.error))
            if err.error == u'target weibo does not exist!':
                topic.watcher_weibo.remove(watcher.original_weibo)
                topic.watcher.remove(watcher)
                logger.info(u'remove watcher:%s and delete watcherWeibo:%s' % (watcher, watcher.original_weibo))
                watcher.original_weibo.delete()
            else:
                logger.exception(u'')
        else:
            logger.info(u'%s Succeed!' % res[u'type'])
            if watcher_btw:
                watcher_btw.add_remind()
            watcher.add_remind()
            logger.info(u'added remind history for user: [%s, %s]' % (watcher.weiboName, watcher_btw))
        finally:
            reqInterval(61)

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
            postMsg = _msg + u' @' + watcher_btw.weiboName + u' 顺便提醒你一下～'
        else:
            postMsg = _msg + u' @' + watcher.weiboName

        logger.info(u'remind user:%s topic:%s update with msg:%s' % (watcher.weiboName, topicTitle, postMsg))
        res = {}
        try:
            res[u'status'] = _weibo.updateStatus(content=postMsg)
        except APIError, err:
            logger.warn(u'Update status failed:%t' % err.error)
        else:
            logger.info(u'Update status succeed!')
            if watcher_btw:
                watcher_btw.add_remind()
            watcher.add_remind()
            logger.info(u'add remind history for user: [%s, %s]' % (watcher.weiboName, watcher_btw))
            _status = djangodb.get_or_create_weibo(res[u'status'])
            topic.watcher_weibo.add(_status)
            logger.info(u'add watcherWeibo:%s to topic:%s' % (_status.text, topicTitle))
        finally:
            reqInterval(61)  # 间隔两次请求

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
            postMsg = u'友情提示：' + _msg + u' @' + watcher.weiboName
        else:
            #  如果没有用户可以帮忙，主帐号提醒吧
            _reminder = djangodb.get_root_account()
            _weibo = weibo
            postMsg = _msg + u' @' + watcher.weiboName

        logger.info(u'remind user:%s topic:%s update with msg:%s' % (watcher, topicTitle, postMsg))
        logger.info(u'_reminder:%s\toriginalWeibo:%s' % (_reminder, watcher.original_weibo))

        res = {}
        try:
            res[u'status'] = _weibo.postComment(weibo_id=watcher.original_weibo.weibo_id, content=postMsg)
        except APIError, err:
            logger.warn(u'comment failed:\t%s' % (err.error))
            if err.error == u'target weibo does not exist!':
                topic.watcher_weibo.remove(watcher.original_weibo)
                topic.watcher.remove(watcher)
                logger.info(u'remove watcher:%s and delete watcherWeibo:%s' % (watcher, watcher.original_weibo))
                watcher.original_weibo.delete()
        except:
            logger.exception(u'')
        else:
            logger.info(u'comment succeed!')
            watcher.add_remind()
            logger.info(u'added remind history for user: %s' % watcher.weiboName)
        finally:
            reqInterval(61)

    '''
    既没有授权也没有发过微博
    不再提醒
    '''
    return True

def subscribeTopic(topicRss, topicTitle=None):
    '''
    订阅的时候即便是加了title,最后谷歌还是会在后面加上' - Google 新闻'
    '''
    try:
        sucSubscribe = reader.subscribe(feedUrl=topicRss.encode('utf-8'), title=topicTitle.encode('utf-8'))
    except:
        sucSubscribe = False
        logger.exception(u'Fail to subscribed topicrss:%s' % topicRss)
    finally:
        if sucSubscribe:
            logger.debug(u'Succeed to subscribe topicrss:%s ' % topicRss)
        else:
            logger.error(u'Fail to subscribed topicrss:%s ' % topicRss)
        return sucSubscribe

def unSubscribeTopic(topicRss):
    '''
    TODO:该方法不可用，API调用返回OK，但是没有取消订阅。。。
    '''
    try:
        sucUnsubscribe = reader.unsubscribe(feedUrl=topicRss.encode('utf-8'))
    except:
        sucUnsubscribe = False
        logger.exception(u'Fail to unsubscribe %s' % topicRss)
    finally:
        if sucUnsubscribe:
            logger.debug(u'Succeed to unsubscribe topicrss:%s ' % topicRss)
        else:
            logger.error(u'Fail to unsubscribe topicrss:%s' % topicRss)
        return sucUnsubscribe

def delTopic(topicTitle):
    '''
    目前还没有用
    '''
    logger.debug(u'Start delete topic:%s' % topicTitle)
    try:
        topic = djangodb.Topic.objects.get(title=topicTitle)
    except djangodb.Topic.DoesNotExist:
        logger.warn(u'Topic:%s not exist!!!' % topicTitle)
    except:
        logger.exception(u'')
    else:
        # 取消订阅
        logger.info(u'unsubstribe topic:%s' % topicTitle)
        unSubscribeTopic(topic.rss)
        # 数据库中删除该话题的信息
        logger.info(u'delete news in databases')
        topic.news_set.all().delete()
        logger.info(u'delete topic(mark topic as dead)')
        topic.delete()
        return True
    return False


if __name__ == u'__main__':
    while True:
# 　　　　TODO: 由于取消订阅的API无法成功取消订阅，手动取消～＝＝！
#        unsubs_tasks = djangodb.get_tasks(type=u'unsubscribe', count=10)
#        logger.info(u'Start execute %d unsubscribe tasks' % len(unsubs_tasks))
#        for t in unsubs_tasks:
#            try:
#                unSubscribeTopic(topicRss=t.topic.rss)
#                reqInterval(61)  # 间隔两次请求
#            except:
#                logger.exception(u'Except in unsubscribeTopic()')
#                break
#            t.status = 0  # 更新成功，设置标志位
#            t.save()

        subs_tasks = djangodb.get_tasks(type=u'subscribe', count=5)
        logger.info('subscribe task number:%d' % len(subs_tasks))
        for t in subs_tasks:
            try:
                if subscribeTopic(topicRss=t.topic.rss, topicTitle=t.topic.title):
                    t.status = 0  # 更新成功，设置标志位
                    t.save()
                    logger.info(u'succeed to subscribe:%s' % t.topic.title)
                else:
                    logger.error(u'fail to subscribe topic:%s' % t.topic.title)
            except:
                logger.exception(u'')
            finally:
                reqInterval(61)

        remind_tasks = djangodb.get_tasks(type=u'remind', count=3)
        logger.info('remind tasks number:%d' % len(remind_tasks))
        for t in remind_tasks:
            try:
                if remindUserTopicUpdates(topicTitle=t.topic.title):
                    t.status = 0  # 更新成功，设置标志位
                    t.save()
                    logger.info(u'succeed to remind topic:%s' % t.topic.title)
                else:
                    logger.warn(u'fail to subscribe topic:%s' % t.topic.title)
            except:
                logger.exception(u'fail to remind user topic update')
            finally:
                reqInterval(61)

        logger.info(u'sleep for 20 minutes')
        reqInterval(20 * 60)

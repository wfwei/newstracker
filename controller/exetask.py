# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 1, 2012

@author: plex
'''
from libweibo import weiboAPI
from libweibo.weibo import APIError
from djangodb import djangodb
import logging
import time

# setup logging
logger = logging.getLogger('task-logger')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('../logs/exetask.log')
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

# setup weibo
[access_token, expires_in] = djangodb.get_weibo_auth_info(3041970403)
if time.time() > float(expires_in):
    raise Exception(u"授权过期了，with expires_in:" + str(expires_in))
weibo = weiboAPI.weiboAPI(access_token=access_token, expires_in=expires_in, u_id=3041970403)
time.sleep(31)
logger.info(u'Sina Weibo 登录信息:\t' + weibo.getUserInfo()['name'])

# setup google reader
from libgreader import readerAPI
[access_token, refresh_token, access_expires] = djangodb.get_google_auth_info(u_id=1)
reader = readerAPI.readerAPI(u_id=1, access_token=access_token, \
                   refresh_token=refresh_token, expires_access=access_expires)
time.sleep(31)
logger.info(u'Google Reader 登录信息:\t' + reader.getUserInfo()['userName'])


def remindUserTopicUpdates(topicTitle):
    try:
        logger.debug('Start remind user for topic: ' + topicTitle)
        topic = djangodb.Topic.objects.get(title=topicTitle)
        if not topic.alive():
            logger.warn('topic %s is already dead, add unsubscribe task!' % topicTitle)
            djangodb.add_task(topic=topic, type='unsubscribe')
            return False
        else:
            topic_news = topic.news_set.all()[0]
    except Exception, e:
        logger.error('topic or news not exists in database\n\t' + str(e))
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
        else:
            logger.info("%s Succeed!" % res['type'])
            if watcher_btw:
                watcher_btw.add_remind()
            watcher.add_remind()
            logger.info('added remind history for user: [%s, %s]' % (watcher.weiboName, str(watcher_btw)))
        finally:
            time.sleep(61)

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
        else:
            logger.info("Update status succeed!")
            if watcher_btw:
                watcher_btw.add_remind()
            watcher.add_remind()
            logger.info('add remind history for user: [%s, %s]' % (watcher.weiboName, str(watcher_btw)))
            _status = djangodb.get_or_create_weibo(res['status'])
            topic.watcher_weibo.add(_status)
            logger.info('add watcherWeibo:%s to topic:%s' % (_status.text, topicTitle))
        finally:
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
            postMsg = '友情提示：' + _msg
        else:
            #  如果没有用户可以帮忙，主帐号提醒吧
            _reminder = '主帐号'
            _weibo = weibo
            postMsg = _msg

        logger.info('remind user:%s topic:%s update with msg:%s' % (watcher.weiboName, topicTitle, postMsg))
        logger.info("_reminder:%s\toriginalWeibo:%s" % (str(_reminder), str(watcher.original_weibo)))

        res = {}
        try:
            res['status'] = _weibo.postComment(weibo_id=watcher.original_weibo.weibo_id, content=postMsg)
        except APIError, err:
            logger.warn("comment failed:\t%s" % (err.error))
            if err.error == 'target weibo does not exist!':
                topic.watcher_weibo.remove(watcher.original_weibo)
                topic.watcher.remove(watcher)
                logger.info('remove watcher:%s and delete watcherWeibo:%s' % (str(watcher), str(watcher.original_weibo)))
                watcher.original_weibo.delete()
        else:
            logger.info("comment succeed!")
            watcher.add_remind()
            logger.info('added remind history for user: %s' % watcher.weiboName)
        finally:
            time.sleep(61)

    '''
    既没有授权也没有发过微博
    不再提醒
    '''
    return True

def subscribeTopic(topicRss, topicTitle=None):
    # 订阅的时候即便是加了title,最后谷歌还是会在后面加上' - Google 新闻'
    try:
        if not reader.subscribe(feedUrl=topicRss, title=topicTitle):
            logger.error('Fail to subscribed ' + topicRss)
            return False
        else:
            logger.debug('Succeed to subscribe ' + topicRss)
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
            return False
        else:
            logger.debug('Succeed to unsubscribe ' + topicRss)
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


if __name__ == '__main__':
    while True:
# 　　　　TODO: 由于取消订阅的API无法成功取消订阅，手动取消～＝＝！
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
        for t in subs_tasks:
            try:
                subscribeTopic(topicRss=t.topic.rss, topicTitle=t.topic.title)
            except Exception, e:
                logger.error('fail to subscribe topic(%s) \n\t%s' % (t.topic.title, str(e)))
                continue
            else:
                t.status = 0  # 更新成功，设置标志位
                t.save()
                logger.info('succeed to subscribe:%s' % t.topic.title)
            finally:
                time.sleep(61)
        else:
            logger.info('no subscribe task!!!')

        remind_tasks = djangodb.get_tasks(type='remind', count=3)
        for t in remind_tasks:
            try:
                remindUserTopicUpdates(topicTitle=t.topic.title)
            except Exception, e:
                logger.error('fail to subscribe topic(%s) \n\t%s' % (t.topic.title, str(e)))
                continue
            else:
                t.status = 0  # 更新成功，设置标志位
                t.save()
                logger.info('succeed to remind topic:%s' % t.topic.title)
            finally:
                time.sleep(61)
        else:
            logger.info('no remind task!!!')

        logger.info('sleep for 20 minutes')
        time.sleep(20 * 60)

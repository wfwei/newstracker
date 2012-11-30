# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 1, 2012

@author: plex
'''

from djangodb import djangodb
from libgnews import googlenews
from libweibo.weibo import APIError

import datetime
import time
import re

import __builtin__
weibo = __builtin__.weibo
logger = __builtin__.weibologger

def fetchUserMention():
    '''
    获取微博上用户的订阅话题,之后更新订阅
    用户订阅话题的方式可以发布包含:@新闻追踪007 *订阅或取消订阅* #话题内容#的微博；或者转发上述微博

    TODO:
    1. mentions只获取了前50条，接下来要设法获取全部。。
    2. 修改mention_list的顺序，这样，中间出错，不影响后面的
    '''
    # 得到用户mentions
    lastMentionId = djangodb.get_last_mention_id()
    logger.info('\nget lastMentionId:' + str(lastMentionId))
    try:
        mentions = weibo.getMentions(since_id=lastMentionId)
    except APIError, err:
        logger.error('failed to get mentions:%s' % err.error)
        return False
    except:
        raise
    time.sleep(31)  # 间隔两次请求
    mention_list = mentions['statuses']
    logger.info('mention_list length:' + str(len(mention_list)))

    # 提取用户@的消息并进行解读,保存话题
    # 这里拟序mention_list，先访问序号较小的微博,参考TODO2
    for mention in reversed(mention_list):
        # step 1: 提取并构造微博对象
        mweibo = djangodb.get_or_create_weibo(mention)
        if 'retweeted_status' in mention:
            # 是不是存在retweeted_status就一定是转发的微博
            is_retweeted = True
            mweibo_retweeted = djangodb.get_or_create_weibo(mention['retweeted_status'])
        else:
            is_retweeted = False
        logger.info('\nstep1: is_retweeted=' + str(is_retweeted))

        # step 2: 提取并构造用户对象
        muser = djangodb.get_or_create_account_from_weibo(mention['user'])
        logger.info('step3: muser:' + str(muser))

        # step 3: 提取话题相关的信息
        mtopictitle = None
        _search_content = mweibo.text
        if is_retweeted:
            _search_content += ' / ' + mweibo_retweeted.text
        topic_res = re.search('#([^#]+)#', _search_content)
        if topic_res is not None:
            # 只能订阅一个话题，第一个井号标识的话题
            mtopictitle = topic_res.group(1)
            logger.info('step3: mtopictitle=' + mtopictitle)
        else:
            logger.debug('step3: 本条@微博不含有话题:\t' + _search_content + \
                              ' from user: @' + muser.weiboName)
            continue

        # step 4: 构建话题
        mtopic, created = djangodb.Topic.objects.get_or_create(title=mtopictitle)
        if created or not mtopic.alive():
            mtopic.activate()
            is_new_topic = True
            mtopic.rss = googlenews.GoogleNews(mtopic.title).getRss()
            mtopic.time = mweibo.created_at
            logger.debug('step4: add subscribe (#%s#) task to taskqueue' % mtopictitle)
            djangodb.add_task(topic=mtopic, type='subscribe')
        else:
            logger.debug('step4: topic #%s# already in track' % mtopictitle)
            is_new_topic = False

        mtopic.watcher.add(muser)
        mtopic.watcher_weibo.add(mweibo)
        mtopic.save()

        # step 5: 提醒用户订阅成功
        try:
            if is_new_topic:
                remind_msg = '订阅成功，我们正在整理资料，之后会将该事件的来龙去脉和最新消息推送给您！登录『' + weibo.getShortUrl("http://110.76.40.188:81") + '』了解更多...'
            else:
                remind_msg = '订阅成功，您可以到『' + weibo.getShortUrl("http://110.76.40.188:81/news_timeline/" + str(mtopic.id)) + '』获取该事件的来龙去脉，同时我们会将发展动态即时推送给您～'
        except APIError, err:
            logger.error('Failed to get short url' % err.error)
            remind_msg = '订阅成功～'
        except:
            raise

        time.sleep(31)  # 间隔两次请求
        try:
            weibo.postComment(mweibo.weibo_id, remind_msg)
        except APIError, err:
            logger.warn("post comment failed:\t%s" % err.error)
            if err.error == 'target weibo does not exist!':
                mtopic.watcher_weibo.remove(mweibo)
                mtopic.watcher.remove(muser)
                logger.info('remove watcher:%s and delete watcherWeibo:%s' % (str(muser), str(mweibo)))
                mweibo.delete()
        except:
            raise
        else:
            logger.info("Remind user Succeed!")


        time.sleep(31)  # 间隔两次请求

    logger.debug('getUserPostTopic() OK')

def fetchHotTopic():
    '''
    获取微博上*每周*的热门话题,之后更新订阅
    MARK: not in use
    '''
    # 获取,解析和存储话题
    try:
        weekHotTopics = weibo.getHotTopics()
    except APIError, err:
        logger.error('failed to get hot topics:%s' % err.error)
        return False
    except:
        raise

    time.sleep(61)  # 间隔两次请求
    for topictime in weekHotTopics.keys():
        for topic in weekHotTopics.get(topictime):
            topictitle = topic['query']
            hotopic, created = djangodb.Topic.objects.get_or_create(title=topictitle)
            if created or not hotopic.alive():
                hotopic.activate()
                hotopic.rss = googlenews.GoogleNews(hotopic.title).getRss()
                # hotopic.time = topictime #TODO: 目前使用默认值，但是最好可以解析时间字符串
                logger.debug('add to_filte task to taskqueue:  (#%s#)' % topictitle)
                djangodb.add_task(topic=hotopic, type='to_filte')
            else:
                logger.debug('topic #%s# already in track' % topictitle)


def t_checkweibo():
    while True:
        try:
            logger.info('Start fetching user mentions')
            fetchUserMention()
        except:
            logger.exception("Except in fetchUserMention()")
        finally:
            logger.info("Fetching today's user mentions over")

        logger.info('Start sleep for 15 minutes')
        time.sleep(15 * 60)

        if time.localtime().tm_hour > 0 and time.localtime().tm_hour < 7:

            try:
                logger.info("Start fetching today's hot topics:")
                fetchHotTopic()
            except:
                logger.exception("Except in fetchHotTopic()")
            finally:
                logger.info("Fetching today's hot topic over")

            logger.info('night sleep for ' + \
                             str(7 - time.localtime().tm_hour) + ' hours')
            time.sleep((7 - time.localtime().tm_hour) * 60 * 60)

# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Nov 1, 2012

@author: plex
'''

from djangodb import djangodb
from libgnews import googlenews

import time
import re

import __builtin__
weibo = __builtin__.weibo
weibologger = __builtin__.weibologger

def fetchUserMention():
    '''
    获取微博上用户的订阅话题,之后更新订阅
    用户订阅话题的方式可以发布包含:@新闻追踪007 *订阅或取消订阅* #话题内容#的微博；或者转发上述微博

    TODO:
    1. mentions只获取了前50条，接下来要设法获取全部。。
    2. 修改mention_list的顺序，这样，中间出错，不影响后面的
    '''
    # # 得到用户mentions
    lastMentionId = djangodb.get_last_mention_id()
    weibologger.info('\nget lastMentionId:' + str(lastMentionId))

    mentions = weibo.getMentions(since_id=lastMentionId)
    time.sleep(15)  # # 间隔两次请求
    mention_list = mentions['statuses']
    weibologger.info('mention_list length:' + str(len(mention_list)))

    # # 提取用户@的消息并进行解读,保存话题
    # # 这里拟序mention_list，先访问序号较小的微博,参考TODO2
    for mention in reversed(mention_list):
        # # step 1: 提取并构造微博对象
        mweibo = djangodb.get_or_create_weibo(mention)
        if 'retweeted_status' in mention:
            # 是不是存在retweeted_status就一定是转发的微博
            is_retweeted = True
            mweibo_retweeted = djangodb.get_or_create_weibo(mention['retweeted_status'])
        else:
            is_retweeted = False
        weibologger.info('\nstep1: is_retweeted=' + str(is_retweeted))

        # # step 2: 提取并构造用户对象
        muser = djangodb.get_or_create_account_from_weibo(mention['user'])
        weibologger.info('step3: muser:' + str(muser))

        # # step 3: 提取话题相关的信息
        mtopictitle = None
        _search_content = mweibo.text
        if is_retweeted:
            _search_content += ' / ' + mweibo_retweeted.text
        topic_res = re.search('#([^#]+)#', _search_content)
        if topic_res is not None:
            # #只能订阅一个话题，第一个井号标识的话题
            mtopictitle = topic_res.group(1)
            weibologger.info('step3: mtopictitle=' + mtopictitle)
        else:
            weibologger.debug('step3: 本条@微博不含有话题:\t' + _search_content + \
                              ' from user: @' + muser.weiboName)
            continue

        # # step 4: 构建话题
        mtopic, created = djangodb.Topic.objects.get_or_create(title=mtopictitle)
        if created or not mtopic.alive():
            mtopic.activate()
            is_new_topic = True
            mtopic.rss = googlenews.GoogleNews(mtopic.title).getRss()
            mtopic.time = mweibo.created_at
            weibologger.debug('step4: add subscribe (#%s#) task to taskqueue' % mtopictitle)
            djangodb.add_task(topic=mtopic, type='subscribe')
        else:
            weibologger.debug('step4: topic #%s# already in track' % mtopictitle)
            is_new_topic = False

        mtopic.watcher.add(muser)
        mtopic.watcher_weibo.add(mweibo)
        mtopic.save()

        # # step 5: 提醒用户订阅成功
        if is_new_topic:
            remind_msg = '订阅成功，我们正在整理资料，之后会将该事件的来龙去脉和最新消息推送给您！登录『' + weibo.getShortUrl("http://110.76.40.188:81") + '』了解更多...'
        else:
            remind_msg = '订阅成功，您可以到『' + weibo.getShortUrl("http://110.76.40.188:81/news_timeline/" + str(mtopic.id)) + '』获取该事件的来龙去脉，同时我们会将发展动态即时推送给您～'
        time.sleep(15)  # # 间隔两次请求
        try:
            if not weibo.postComment(mweibo.weibo_id, remind_msg):
                weibologger.error('step5: fail to weibo.postComment(%s, %s) ' % (mweibo.weibo_id, remind_msg))
            else:
                weibologger.info('step5: succeed remind user')
        except:
            weibologger.error('step5: error to weibo.postComment(%s, %s) maybe access key outdated ' % (str(mweibo.weibo_id), remind_msg))
        time.sleep(15)  # # 间隔两次请求

    weibologger.debug('getUserPostTopic() OK')

def fetchHotTopic():
    '''
    获取微博上*每周*的热门话题,之后更新订阅
    MARK: not in use
    有bug，当重建已删除的话题时候。。。
    '''
    # # 获取,解析和存储话题
    weekHotTopics = weibo.getHotTopics()
    time.sleep(15)  # # 间隔两次请求
    for topictime in weekHotTopics.keys():
        for topic in weekHotTopics.get(topictime):
            topictitle = topic['query']
            try:
                djangodb.Topic.objects.get(title=topictitle)
                weibologger.debug('topic #%s# already in track' % topictitle)
            except djangodb.Topic.DoesNotExist:
                topicrss = googlenews.GoogleNews(topictitle).getRss()
                _topic = djangodb.Topic.objects.create(title=topictitle, rss=topicrss, time=topictime)
                # # 添加订阅话题任务
                weibologger.debug('add subscribe (#%s#) task to taskqueue' % topictitle)
                djangodb.add_task(topic=_topic, type='subscribe')


def t_checkweibo():
    while True:
        weibologger.info('Start fetching user mentions')
        try:
            fetchUserMention()
        except:
            weibologger.exception("Except in fetchUserMention()")
        weibologger.info('Start sleep for 15 minutes')
        time.sleep(10 * 60)

        if time.localtime().tm_hour > 0 and time.localtime().tm_hour < 7:
            weibologger.info('night sleep for ' + \
                             str(7 - time.localtime().tm_hour) + ' hours')
            time.sleep((7 - time.localtime().tm_hour) * 60 * 60)

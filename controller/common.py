#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 10, 2012

@author: plex
'''
import sys
sys.path.append('/home/wangfengwei/wksp/newstracker')

from libgreader import GoogleReader
from libgnews import googlenews
from libweibo import weiboAPI
from djangodb import djangodb

import datetime
import json
import time
import re
import os

_DEBUG = True

# Init google reader
reader = GoogleReader()
if _DEBUG:
    print 'Google Reader 登录信息:\t' , reader.getUserInfo()['userName']

# Init weibo
[access_token, expires_in] = djangodb.get_or_update_weibo_auth_info(3041970403)
weibo = weiboAPI.weiboAPI(access_token = access_token, expires_in = expires_in, u_id = 3041970403)

if _DEBUG:
    print 'Sina Weibo 登录信息:\t' , weibo.getUserInfo()['name']

def remindUserTopicUpdates(topicTitle):
    try:
        topic = djangodb.Topic.objects.get(title = topicTitle)
        ## 不知道这样的效率如何，应该还好吧
        topic_news = topic.news_set.all()[0]
    except djangodb.Topic.DoesNotExist:
        print 'Topic:\t' + topicTitle + ' not exist!!!'
        return False
    except:
        print 'No news update for topic:\t' + topicTitle + '!!!'
        return False
    topicWatchers = topic.watcher.all()
    topciWatcherWeibo = topic.watcher_weibo.all()
    ## TODO: 网站上线，把链接改成自己的
    postMsg = '#'+topicTitle+'# 有新进展：'+topic_news.title + '(' + weibo.getShortUrl(topic_news.link) + ')'

    if _DEBUG:
        print 'topicWatchers ', topicWatchers
        print 'topciWatcherWeibo ', topciWatcherWeibo

    _user_reminded = []
    for watcherWeibo in topciWatcherWeibo:
        targetStatusId = watcherWeibo.weibo_id
        ## 如果微博不存在，则将该微博记录从topic的链接中删除,否则添加到已经提醒的用户列表中
        if len(postMsg) > 139:
            postMsg = postMsg[:139]
        if _DEBUG:
            print 'postMsg: ', postMsg
        if not weibo.postComment(weibo_id = targetStatusId, content = postMsg):
            topic.watcher_weibo.remove(watcherWeibo)
            if _DEBUG:
                print 'post comment failed! '
                print 'weibo_id: ', targetStatusId
                print 'postMsg: ', postMsg
        else:
            _user_reminded.append(watcherWeibo.user.weiboId)

    ## 有些用户没有发微博关注该事件(将原有微博删除了)，但也要提醒，首先要剔除已经提醒的_user_commented
    for watcher in topicWatchers:
        weiboId = watcher.weiboId
        if weiboId != 0 and weiboId not in _user_reminded:
            ## 如果用户绑定了微博帐号，且没有发微博订阅该话题
            ## 目前做法：主帐号有一条专门提醒用户话题更新的公用微博，每当用户有要更新的话题时，评论该微博，并＠用户和新闻更新信息
            postMsg = '@' + watcher.weiboName + ' 您关注的事件' + postMsg
            if len(postMsg) > 139:
                postMsg = postMsg[:139]
            if _DEBUG:
                print 'postMsg: ', postMsg
            if not weibo.postComment(weiboAPI.REMIND_WEIBO_ID, postMsg):
                print 'post comment failed! '
                print 'weiboAPI.REMIND_WEIBO_ID: ', weiboAPI.REMIND_WEIBO_ID
                print 'postMsg: ', postMsg

def create_or_update_news_timeline(topicTitle):
    '''
     生成指定话题的timeline，并保存到文件中
     文件放在newstrack的static目录下，以后可以放到media目录中
     文件的保存名称为: topicTitle.jsonp
    '''
    try:
        topic = djangodb.Topic.objects.get(title = topicTitle)
        topic_news = topic.news_set.all()
        ## TODO: 改进筛选news的方法
        if len(topic_news) > 20:
            topic_news = topic_news[:20]
        news_list = []
        for news in topic_news:
            ##TODO: text提取新闻概要信息
            jnews = {"startDate":news.pubDate.strftime('%Y,%m,%d,%H,%M'),
                    "endDate":(news.pubDate.date() + datetime.timedelta(1)).strftime('%Y,%m,%d,%H,%M'),
                    "headline":news.title,
                    "text":'news.summary[12:-22]',
                    "tag":"",
                    "asset": {
                        "media":'',
                        "thumbnail":"",
                        "credit":"",
                        "caption":"",
                        }
                     }
            news_list.append(jnews)

        timeline = {}
        timeline['headline'] = topic.title
        timeline['type'] = 'default'
        timeline['text'] = 'topic'
        timeline['date'] = news_list
#        timeline['era'] = [{"startDate":"2012,1,10",
#                "endDate":"2012,1,11",
#                "headline":news.title,
#                "tag":"This is Optional"}]

        ## Save to file
        f = open(str(os.getcwd()) + '/../newstracker/newstrack/static/news.timeline/' + topicTitle + '.jsonp', 'w+')
        f.write('storyjs_jsonp_data = ')
        f = open(str(os.getcwd()) + '/../newstracker/newstrack/static/news.timeline/' + topicTitle + '.jsonp', 'a')
        json.dump({"timeline": timeline}, f, encoding='utf-8')
        print 'Generate news timeline: ' + str(os.getcwd()) + '/../newstracker/newstrack/static/news.timeline/' + topicTitle + '.jsonp'
    except djangodb.Topic.DoesNotExist:
        print 'Topic:\t' + topicTitle + ' not exist!!!'
        return False
    except:
        print 'error in create_or_update_news_timeline ', topicTitle

def update_all_news_timeline():
    topic_list = djangodb.Topic.objects.all()
    for topic in topic_list:
        print 'create or update news timeline for: ', topic.title
        create_or_update_news_timeline(topic.title)
    print 'all finished'
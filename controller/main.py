#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 10, 2012

@author: plex
'''

from libgreader import GoogleReader
from libgnews import googlenews
from djangodb import djangodb
from djangodb import utils
from libweibo import weiboAPI

from datetime import datetime
import re

_DEBUG = True

## Init google reader
reader = GoogleReader()
if _DEBUG:
    print 'Google Reader 登录信息:\t' , reader.getUserInfo()['userName']

## Init weibo
weibo = weiboAPI.weiboAPI()
if _DEBUG:
    print 'Sina Weibo 登录信息:\t' , weibo.getUserInfo()['id']
    

def fetchHotTopic():
    '''
    获取微博上*每周*的热门话题,之后更新订阅
    '''
    ## 获取,解析和存储话题
    weekHotTopics = weibo.getHotTopics()
    topic_dict = {}
    for topictime in weekHotTopics.keys():
        for topic in weekHotTopics.get(topictime):
            topictitle = topic['query']
            if _DEBUG:
                print topictime, topictitle
            try:
                djangodb.Topic.objects.get(title = topictitle)
            except djangodb.Topic.DoesNotExist:
                topicrss = googlenews.GoogleNews(topictitle).getRss()
                djangodb.Topic.objects.create(title = topictitle,
                                              rss = topicrss,
                                              time = topictime)
                topic_dict[topictitle] = topicrss
    ## 订阅话题 
    for topic_tile in topic_dict.keys():
        topic_rss = topic_dict.get(topic_tile)
        ## 订阅的时候即便是加了title,最后谷歌还是会在后面加上' - Google 新闻'
        status = reader.subscribe(topic_rss, topic_tile)
        if not status:
            print '\nFail to subscribed ',topic_rss
        elif _DEBUG:
            print 'Subscribed ',topic_rss
    
def fetchRssUpdates():
    '''
    检查更新rss订阅源,并存储更新的新闻,之后标记rss为已读
    debug模式下,如果数据库中找不到订阅的rss,则会创建之
    '''
    unreadFeedsDict = reader.getUnreadFeeds()
    
    for feed in unreadFeedsDict.keys():
        if(feed.startswith('feed')):
            excludeRead = True
            continuation = None
            over = False
            while not over:
                feedContent = reader.fetchFeedItems(feed, excludeRead, continuation)
                try:
                    continuation = feedContent['continuation']
                    if len(continuation) < 1:
                        raise KeyError
                except KeyError:
                    over = True
                
                itemSet = feedContent['items']
                ## title的形式:"镜头里的萝莉 - Google 新闻"  要截断后面的
                feedTopic = feedContent['title'][0:feedContent['title'].find(' - Google ')]

                if _DEBUG:
                    print 'feed content:\n', feedContent
                    print 'continuation:\t', continuation
                    print 'item set size:\t', len(itemSet)
                    print 'feed topic:\t', feedTopic
                    
                topic = None
                try:
                    topic = djangodb.Topic.objects.get(title = feedTopic)
                except djangodb.Topic.DoesNotExist:
                    if _DEBUG:
                        topicrss = googlenews.GoogleNews(feedTopic).getRss()
                        topic = djangodb.Topic.objects.create(title = feedTopic,
                                                              rss = topicrss,
                                                              time = datetime.now())
                        print 'WARNING: 话题 ' + feedTopic + ' 不存在, 重建后保存数据库'
                    else:
                        print 'Error!!!无法找到对应话题,跳过该feed:',feedTopic
                        break

                for item in itemSet:
                    ## extract information from item
                    title = item['title']
                    pubDate = datetime.fromtimestamp(float(item['published']))
                    summary = item['summary']
                    ## TODO: 可能会抛出Null pointer Excepiton
                    link = item['alternate'][0]['href']
                    if link.find('&url=http') > 0 :
                        link = link[link.find('&url=http')+5:]
                        
                    ##Store into database TODO: change to get_or_create()
                    try:
                        djangodb.News.objects.get(title = title)
                    except djangodb.News.DoesNotExist:
                        nnew = djangodb.News.objects.create(title = title,
                                                     link = link,
                                                     pubDate = pubDate,
                                                     summary = summary)
                        nnew.topic.add(topic)
                        nnew.save()
                        if _DEBUG:
                            print nnew
            ## 标记该feed为全部已读
            if not reader.markFeedAsRead(feed):
                print 'Error in mark ' + feed + ' as read!!!'
            elif _DEBUG:
                print 'Succeed mark ' + feed + ' as read'
                
            ## 提醒订阅该话题（feed）的用户 TODO:uncomment
            remindUserTopicUpdates(feedTopic)
            pass
            
def remindUserTopicUpdates(topicTitle):
    try:
        topic = djangodb.Topic.objects.get(title = topicTitle)
        ## TODO： limit数量
        topic_news = djangodb.News.objects.filter(topic = topic)[0]
    except djangodb.Topic.DoesNotExist:
        print 'Topic:\t' + topicTitle + ' not exist!!!'
        return False
    except:
        print 'No news update for topic:\t' + topicTitle + '!!!'
        return False
    topicWatchers = topic.watcher.all()
    topciWatcherWeibo = topic.watcher_weibo.all()
    postMsg = '#'+topicTitle+'# 最近进展：'
    _user_commented = []
    
    if _DEBUG:
        print topicWatchers
        print topciWatcherWeibo
        print postMsg
    
    for watcherWeibo in topciWatcherWeibo:
        postMsg = postMsg + topic_news.title + ':' + weibo.getShortUrl(topic_news.link)
        ## TODO: 中文和英文的计算长度有问题
        if len(postMsg) > 140:
            pass
        targetStatusId = watcherWeibo.weibo_id
        ## 如果微博不存在，则将该微博记录从topic的链接中删除,否则添加到已经提醒的用户列表中
        if not weibo.postComment(weibo_id = targetStatusId, content = postMsg):
            topic.watcher_weibo.remove(watcherWeibo)
        else:
            ## watcherWeibo.user是空。。。。
            _user_commented.append(watcherWeibo.user.weiboId)
            pass
    ## 有些用户没有发微博关注该事件(将原有微博删除了)，但也要提醒，首先要剔除已经提醒的_user_commented
    for watcher in topicWatchers:
        weiboId = watcher.weiboId
        if weiboId != 0 and weiboId not in _user_commented:
            ##TODO: 考虑主帐号发话题微博，之后@用户
            pass
                
def getUserPostTopic():
    '''
    获取微博上用户的订阅话题,之后更新订阅
    用户订阅话题的方式可以发布包含:@新闻追踪007 *订阅或取消订阅* #话题内容#的微博
    '''
    ## 获取,解析和存储话题
    mentions = weibo.getMentions()
    mention_list = mentions['statuses']
    if _DEBUG:
        print mention_list
    topic_user_dict = {}
    
    ## 提取用户@的消息并进行解读,保存话题
    for mention in mention_list:
        ## step 1: 提取并构造微博对象
        mweibo = utils.get_or_create_weibo(mention)

        ## step 2: 提取并构造用户对象
        muser = utils.get_or_create_account_from_weibo(mention['user'])
        
        ## step 3: 提取话题相关的信息
        topic_res = re.search('#([^#]+)#',mweibo.text)
        action_res = re.search('\*([^\*]+)\*',mweibo.text)
        if topic_res is not None:
            mtopictitle = topic_res.group(1)
        else:
            ## 没有话题,结束并返回False
            print '本条@微博不含有话题--！\t' + mweibo.text
            return False
        ## TODO: 判断用户是要订阅还是取消订阅，暂时不处理，统一认为是订阅话题
        if action_res is not None:
            moperation = action_res.group(1)
        else:
            moperation = '订阅'
        
        ## step 4: 构建话题
        if mtopictitle is not None:
            mtopic, created = djangodb.Topic.objects.get_or_create(title = mtopictitle)
            if created:
                topic_user_dict['is_new_topic'] = True
                mtopic.rss = googlenews.GoogleNews(mtopic.title).getRss()
                mtopic.time = mweibo.created_at
            else:
                topic_user_dict['is_new_topic'] = False
                
            mtopic.watcher.add(muser)
            mtopic.watcher_weibo.add(mweibo)
            mtopic.save()
            topic_user_dict['topic_title'] = mtopic.title
            topic_user_dict['topic_rss'] = mtopic.rss
            topic_user_dict['user'] = muser
            
        ##订阅 TODO: 直接取值更能抛异常，提前判断字典是否含有key
        if True or topic_user_dict['is_new_topic']:
            success = reader.subscribe(topic_user_dict['topic_rss'],
                                      topic_user_dict['topic_title'])
            if not success:
                print '\nFail to subscribed ', topic_user_dict['topic_rss']
            elif _DEBUG:
                print 'Subscribed ', topic_user_dict['topic_rss']
          
if __name__ == '__main__':
#    fetchHotTopic()
    getUserPostTopic()
    fetchRssUpdates()
#    remindUserTopicUpdates('中渔民被韩海警射杀')
#    remindUserTopicUpdates('军舰驶向钓鱼岛')
    
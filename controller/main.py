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
import re
import os

_DEBUG = True

# Init google reader
reader = GoogleReader()
if _DEBUG:
    print 'Google Reader 登录信息:\t' , reader.getUserInfo()['userName']

# Init weibo
[access_token, expires_in] = djangodb.get_or_update_weibo_auth_info(3041970403)
## test
print access_token
print 'expires_in ', expires_in
weibo = weiboAPI.weiboAPI(access_token = access_token, expires_in = expires_in, u_id = 3041970403)

if _DEBUG:
    print 'Sina Weibo 登录信息:\t' , weibo.getUserInfo()['name']

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
            ## TODO: change to True
            excludeRead = False
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
                    print 'feed topic:\t', feedTopic
                    print 'item set size:\t', len(itemSet)
                    print 'continuation:\t', continuation

                topic = None
                try:
                    topic = djangodb.Topic.objects.get(title = feedTopic)
                except djangodb.Topic.DoesNotExist:
                    if _DEBUG:
                        topicrss = googlenews.GoogleNews(feedTopic).getRss()
                        topic = djangodb.Topic.objects.create(title = feedTopic,
                                                              rss = topicrss,
                                                              time = datetime.datetime.now())
                        pass
                        #print 'WARNING: #' + feedTopic + '# 不存在, 重建后保存数据库'
                    else:
                        print 'Error!!!无法找到对应话题,跳过该feed:',feedTopic
                        break

                for item in itemSet:
                    ## extract information from item
                    title = item['title']
                    pubDate = datetime.datetime.fromtimestamp(float(item['published']))
                    summary = item['summary']
                    try:
                        link = item['alternate'][0]['href']
                    except:
                        print 'fail to extract link from alternate attr\n', str(item)
                        link = 'http://www.fakeurl.com'
                    if link.find('&url=http') > 0 :
                        link = link[link.find('&url=http')+5:]
                    nnews, created = djangodb.News.objects.get_or_create(title = title)
                    if created:
                        nnews.link = link
                        nnews.pubDate = pubDate
                        nnews.summary = summary
                    nnews.topic.add(topic)
                    nnews.save()


            ## 标记该feed为全部已读
            if not reader.markFeedAsRead(feed):
                print 'Error in mark ' + feedTopic + ' as read!!!'
            elif _DEBUG:
                print 'Succeed mark ' + feedTopic + ' as read'

            ##　更新话题的news timeline
            create_or_update_news_timeline(feedTopic)

            ## 提醒订阅该话题（feed）的用户
            ##remindUserTopicUpdates(feedTopic)
            pass

def getUserPostTopic():
    '''
    获取微博上用户的订阅话题,之后更新订阅
    用户订阅话题的方式可以发布包含:@新闻追踪007 *订阅或取消订阅* #话题内容#的微博；或者转发上述微博

    TODO:
    1. mentions只获取了前５０条，接下来要设法获取全部。。
    '''
    ## 获取,解析和存储话题
    lastMentionId = djangodb.get_last_mention_id()
    mentions = weibo.getMentions(since_id = lastMentionId)
    mention_list = mentions['statuses']
    if _DEBUG:
        print mention_list
    topic_user_dict = {}

    ## 提取用户@的消息并进行解读,保存话题
    for mention in mention_list:
        ## step 1: 提取并构造微博对象
        mweibo = djangodb.get_or_create_weibo(mention)
        if 'retweeted_status' in mention:
            # 是不是存在retweeted_status就一定是转发的微博
            is_retweeted = True
            mweibo_retweeted = djangodb.get_or_create_weibo(mention['retweeted_status'])
        else:
            is_retweeted = False

        ## step 2: 提取并构造用户对象
        muser = djangodb.get_or_create_account_from_weibo(mention['user'])

        ## step 3: 提取话题相关的信息
        topic_res = re.search('#([^#]+)#',mweibo.text)
        action_res = re.search('\*([^\*]+)\*',mweibo.text)
        if topic_res is not None:
            mtopictitle = topic_res.group(1)
        elif is_retweeted:
            topic_res = re.search('#([^#]+)#', mweibo_retweeted.text)
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

        ##订阅
        if 'is_new_topic' in topic_user_dict and topic_user_dict['is_new_topic']:
            success = reader.subscribe(topic_user_dict['topic_rss'],
                                      topic_user_dict['topic_title'])
            if not success:
                print '\nFail to subscribed ', topic_user_dict['topic_rss']
            elif _DEBUG:
                print 'Subscribed ', topic_user_dict['topic_rss']

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


if __name__ == '__main__':
#    fetchHotTopic()
#    getUserPostTopic()
    update_all_news_timeline()
    #fetchRssUpdates()
#    remindUserTopicUpdates('中渔民被韩海警射杀')
#    remindUserTopicUpdates('军舰驶向钓鱼岛')
#    create_or_update_news_timeline('中渔民被韩海警射杀')
    pass

#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Oct 29, 2012

@author: plex
'''
from djangodb import djangodb
import datetime
import json
import os

def create_or_update_news_timeline(topicTitle):
    '''
     生成指定话题的timeline，并保存到文件中
     文件放在newstrack的static目录下，以后可以放到media目录中
     文件的保存名称为: topicTitle.jsonp
    '''
    try:
        topic = djangodb.Topic.objects.get(title = topicTitle)
        topic_news = _filter_news(list(topic.news_set.all()))

        news_list = []
        for news in topic_news:
            ##TODO: text提取新闻概要信息
            jnews = {"startDate":news.pubDate.strftime('%Y,%m,%d,%H,%M'),
                    "endDate":(news.pubDate.date() + datetime.timedelta(1)).strftime('%Y,%m,%d,%H,%M'),
                    "headline":news.title,
                    "text":news.summary[15:-24].decode('unicode-escape'),
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
        raise

def update_all_news_timeline():
    topic_list = djangodb.Topic.objects.all()
    for topic in topic_list:
        print 'create or update news timeline for: ', topic.title
        create_or_update_news_timeline(topic.title)
    print 'all finished'

def _filter_news(topic_news, min_delta_time=20*60, limit=20):
    total = len(topic_news)
    if total > limit * 2:
        limit = total * 0.618
    if limit > 61:
        limit = 61
    _last_timestamp = datetime.datetime.now()
    dist = {}
    for news in reversed(topic_news):
        _delta_time = (news.pubDate - _last_timestamp).seconds
        dist[_delta_time] = news
        _last_timestamp = news.pubDate
    keys = dist.keys()
    keys.sort(reverse = True)
    del topic_news[:]
    for key in keys:
        if key < min_delta_time or limit < 0:
            break
        topic_news.append(dist[key])
        limit -= 1
    print 'filter news result: ', len(topic_news), ' / ', total
    return topic_news
    
if __name__ == '__main__':
#    create_or_update_news_timeline("杭州烟花爆炸事故")
    update_all_news_timeline()
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
import re

def create_or_update_news_timeline(topicTitle):
    '''
     生成指定话题的timeline，并保存到文件中
     文件放在newstrack的static目录下，以后可以放到media目录中
     文件的保存名称为: topicTitle.jsonp
    '''
    try:
        topic = djangodb.Topic.objects.get(title = topicTitle)
        topic_news = _filter_news(list(topic.news_set.all()))
        summary_template = '<div><div style=\" height:100px; padding:10px; display:inline-block;\">%s</div><div style=\"width:500px; padding:0 10px 0 10px; display:inline-block; letter-spacing:1px; line-height:20px;\">%s</div></div>'
        headline_template = '<a href=\"%s\" >%s</a>'
        news_list = []
        for news in topic_news:
            _summary = news.summary[15:-24].decode('unicode-escape')
            _res = re.findall('<td[^>]*>(.*?)</td>', _summary)
            if len(_res) == 2:
                _summary_pic = _res[0]
                _summary_content = _res[1]
                _summary_content = re.sub('<[/]?font[^>]*>', '', _summary_content)
                _summary_content = re.sub('<[/]?div[^>]*>', '', _summary_content)
                news_link = re.search('href="([^"]*)"', _summary_content).group(1)
                _summary_content = re.sub('<a[^>]*>.*?</a>', '', _summary_content)
                _summary_content = re.sub('[.]{3}.*', '...', _summary_content)
            else:
                _summary_content = _summary
                _summary_pic = ''
                news_link = ''
                print '_summary is not well structured in create_or_update_news_timeline()'
            _summary = summary_template%(_summary_pic, _summary_content)
            _headline = headline_template%(news_link, news.title)
            jnews = {"startDate":news.pubDate.strftime('%Y,%m,%d,%H,%M'),
                    "endDate":(news.pubDate.date() + datetime.timedelta(1)).strftime('%Y,%m,%d,%H,%M'),
                    "headline":_headline,
                    "text":_summary,
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
    print 'update_all_news_timeline start'
    topic_list = djangodb.Topic.objects.all()
    for topic in topic_list:
        print 'create or update news timeline for: ', topic.title
        create_or_update_news_timeline(topic.title)
    print 'update_all_news_timeline finished'

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
    create_or_update_news_timeline("杭州烟花爆炸事故")
#    update_all_news_timeline()
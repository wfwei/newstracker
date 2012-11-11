#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Oct 29, 2012

@author: plex
'''
from djangodb import djangodb
import datetime
import time
import json
import os
import re

import __builtin__
_DEBUG = __builtin__._DEBUG
logger = __builtin__.fulllogger

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
                if '&url=http' in news_link:
                    news_link[news_link.find('&url=http')+5:]
                _summary_content = re.sub('<a[^>]*>.*?</a>', '', _summary_content)
                _summary_content = re.sub('[.]{3}.*', '...', _summary_content)
            else:
                _summary_content = _summary
                _summary_pic = ''
                news_link = ''
                logger.error('_summary is not well structured in create_or_update_news_timeline()')
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
        logger.info('Generate news timeline: ' + str(os.getcwd()) + \
                    '/../newstracker/newstrack/static/news.timeline/' + \
                    topicTitle + '.jsonp \n')
    except djangodb.Topic.DoesNotExist:
        logger.error('Topic:\t' + topicTitle + ' not exist!!!')
        return False
    except:
        logger.error('error in create_or_update_news_timeline:' + topicTitle)
        raise

def update_all_news_timeline():
    logger.info('update_all_news_timeline start')
    topic_list = djangodb.Topic.objects.all()
    for topic in topic_list:
        create_or_update_news_timeline(topic.title)
    logger.info('update_all_news_timeline finished')

## TODO: 可能会过滤掉最新消息！！！

def _filter_news(topic_news, limit=22):
    total = len(topic_news)
    ## set limit
    if total > limit * 2:
        limit = total * 0.618
    if limit > 61:
        limit = 61
    ##去掉与前后时间距离最近的新闻
    while True:
        if len(topic_news) <= limit:
            break
        min_dist = 100000000
        min_news = None
        for pre,cur,post in zip(topic_news[-1:]+topic_news[2:], topic_news, topic_news[1:]+topic_news[:1]):
            pre_ts = long(time.mktime(pre.pubDate.timetuple()))
            cur_ts = long(time.mktime(cur.pubDate.timetuple()))
            post_ts = long(time.mktime(post.pubDate.timetuple()))
            _len = (abs(pre_ts - cur_ts) * 0.35 + abs(cur_ts - post_ts) * 0.15) % 100000000
            if _len < min_dist:
                min_dist = _len
                min_news = cur
            
        if min_news is not None:
            topic_news.remove(min_news)
        else:
            logger.error('WARNING: Unreachable Code')
            break

    logger.info('filter news result: ' + str(len(topic_news)) + ' / ' + str(total))
    return topic_news
    
if __name__ == '__main__':
#    create_or_update_news_timeline("中渔民被韩海警射杀")
    update_all_news_timeline()
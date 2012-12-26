# !/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Oct 29, 2012

@author: plex
'''
from djangodb import djangodb
import time
import json
import os
import re


import logging
# setup logging
logger = logging.getLogger(u'dbop-logger')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(u'../logs/dbop.log')
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


def create_or_update_news_timeline(topicTitle):
    '''
     生成指定话题的timeline，并保存到文件中
     文件放在newstrack的static目录下，以后可以放到media目录中
     文件的保存名称为: topicTitle.jsonp
    '''
    try:
        topic = djangodb.Topic.objects.get(title=topicTitle)
        topic_news = _filter_news(list(topic.news_set.all()))
        summary_template = u'<div><div style=\" height:100px; padding:10px; display:inline-block;\">%s</div><div style=\"width:500px; padding:0 10px 0 10px; display:inline-block; letter-spacing:1px; line-height:20px;\">%s</div></div>'
        headline_template = u'<a href=\"%s\" target="_blank">%s</a>'
        news_list = []
        for news in topic_news:
            _summary = news.summary[15:-24].decode(u'unicode-escape')
            _res = re.findall(u'<td[^>]*>(.*?)</td>', _summary)
            if len(_res) == 2:
                _summary_pic = _res[0]
                _summary_content = _res[1]
                _summary_content = re.sub(u'<[/]?font[^>]*>', '', _summary_content)
                _summary_content = re.sub(u'<[/]?div[^>]*>', '', _summary_content)
                news_link = re.search(u'href="([^"]*)"', _summary_content).group(1)
                if 'url=http' in news_link:
                    news_link = news_link[news_link.find(u'url=http') + 4:]
                _summary_content = re.sub(u'<a[^>]*>.*?</a>', '', _summary_content)
                _summary_content = re.sub(u'<b>[.]{3}</b>.*', '...', _summary_content)
            else:
                _summary_content = u'<br /><br />获取摘要失败啦～～～<br /><hr /><br />我们会尽快解决这个问题的！'
                _summary_pic = u''
                news_link = u''
                logger.error(u'_summary is not well structured in create_or_update_news_timeline()')
                logger.error(u'_summary:' + _summary)
            _summary = summary_template % (_summary_pic, _summary_content)
            news_title = news.title
            if u' - ' in news_title :
                news_title = news_title[:news_title.rfind(u' - ')]
            _headline = headline_template % (news_link, news_title)
            jnews = {u'startDate':news.pubDate.strftime(u'%Y,%m,%d,%H,%M'),
                    u'endDate':news.pubDate.strftime(u'%Y,%m,%d,%H,%M'),
                    u'headline':_headline,
                    u'text':_summary,
                    u'tag':u'',
                    u'asset': {
                        u'media':u'',
                        u'thumbnail':u'',
                        u'credit':u'',
                        u'caption':u'',
                        }
                     }
            news_list.append(jnews)

        timeline = {}
        timeline[u'headline'] = topic.title
        timeline[u'type'] = u'default'
        timeline[u'text'] = u'我们记录并跟踪了该事件的%d条新闻，希望可以帮您更好的了解该事件的来龙去脉～' % len(news_list)
        timeline[u'date'] = news_list

        # Save to file
        f = open(str(os.getcwd()) + u'/../newstracker/newstrack/static/news.timeline/' + topicTitle + u'.jsonp', u'w+')
        f.write(u'storyjs_jsonp_data = u')
        f = open(str(os.getcwd()) + u'/../newstracker/newstrack/static/news.timeline/' + topicTitle + u'.jsonp', u'a')
        json.dump({u'timeline': timeline}, f, encoding=u'utf-8')
        logger.info(u'Generate news timeline: ' + str(os.getcwd()) + \
                    u'/../newstracker/newstrack/static/news.timeline/' + \
                    topicTitle + u'.jsonp \n')
    except djangodb.Topic.DoesNotExist:
        logger.error(u'Topic:\t' + topicTitle + u' not exist!!!')
        return False
    except:
        logger.error(u'error in create_or_update_news_timeline:' + topicTitle)
        raise

def update_all_news_timeline():
    logger.info(u'update_all_news_timeline start')
    topic_list = djangodb.Topic.objects.all()
    for topic in topic_list:
        create_or_update_news_timeline(topic.title)
    logger.info(u'update_all_news_timeline finished')


def _filter_news(topic_news, limit=22):
    '''
    可能会过滤掉最新消息！！！
    '''
    total = len(topic_news)
    # set limit
    if total > limit * 2:
        limit = total * 0.618
    if limit > 45:
        limit = 45
    # 去掉与前后时间距离最近的新闻
    while True:
        if len(topic_news) <= limit:
            break
        min_dist = 100000000
        min_news = None
        for pre, cur, post in zip(topic_news[-1:] + topic_news[2:], topic_news, topic_news[1:] + topic_news[:1]):
            pre_ts = long(time.mktime(pre.pubDate.timetuple()))
            cur_ts = long(time.mktime(cur.pubDate.timetuple()))
            post_ts = long(time.mktime(post.pubDate.timetuple()))
            _len = (abs(pre_ts - cur_ts) * 0.0618 + abs(cur_ts - post_ts) * 0.0382) % 100000000
            if _len < min_dist:
                min_dist = _len
                min_news = cur

        if min_news is not None:
            topic_news.remove(min_news)
        else:
            logger.error(u'WARNING: Unreachable Code')
            break

    logger.info(u'filter news result: ' + str(len(topic_news)) + u' / ' + str(total))
    return topic_news

if __name__ == u'__main__':
#    create_or_update_news_timeline(u'中渔民被韩海警射杀')
    update_all_news_timeline()

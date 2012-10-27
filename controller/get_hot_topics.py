'''
Created on Oct 27, 2012

@author: plex
'''
from controller.common import *

_DEBUG = True

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


if __name__ == '__main__':
    pass
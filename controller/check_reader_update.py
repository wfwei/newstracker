'''
Created on Oct 27, 2012

@author: plex
'''
from controller.common import *

_DEBUG = True

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
            remindUserTopicUpdates(feedTopic)
            pass

if __name__ == '__main__':
    while True:
        fetchRssUpdates()
        time.sleep(2*60*60)
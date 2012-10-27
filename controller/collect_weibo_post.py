'''
Created on Oct 27, 2012

@author: plex
'''
from controller.common import *

_DEBUG = True

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

        ## step 4: 构建话题
        if mtopictitle is not None:
            mtopic, created = djangodb.Topic.objects.get_or_create(title = mtopictitle)
            if created:
                topic_user_dict['is_new_topic'] = True
                mtopic.rss = googlenews.GoogleNews(mtopic.title).getRss()
                mtopic.time = mweibo.created_at
                _reminder = "您已成功订阅#" + mtopictitle + "#，由于此前无人订阅该话题，我们需要一定时间整理材料，之后会通过再次评论该微博提醒您，请谅解～"
            else:
                topic_user_dict['is_new_topic'] = False
                _reminder = "您已成功订阅#" + mtopictitle + "#，可以登录" + weibo.getShortUrl('http://localhost:8000/home/') + "查看该话题的进展情况，非常感谢使用该服务～"
            
            mtopic.watcher.add(muser)
            mtopic.watcher_weibo.add(mweibo)
            mtopic.save()
            topic_user_dict['topic_title'] = mtopic.title
            topic_user_dict['topic_rss'] = mtopic.rss
            topic_user_dict['user'] = muser

            ## step 5:提醒用户订阅话题成功 TODO:test
            weibo.postComment(mweibo.weibo_id, _reminder)
            
        ##step 6:订阅
        if 'is_new_topic' in topic_user_dict and topic_user_dict['is_new_topic']:
            success = reader.subscribe(topic_user_dict['topic_rss'],
                                      topic_user_dict['topic_title'])
            if not success:
                print '\nFail to subscribed ', topic_user_dict['topic_rss']
            elif _DEBUG:
                print 'Subscribed ', topic_user_dict['topic_rss']

if __name__ == '__main__':
    while True:
        getUserPostTopic();
        time.sleep(30*60)
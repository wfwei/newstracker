#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 10, 2012

@author: plex
'''

from djangodb import djangodb


import logging
logger = logging.getLogger('main')
hdlr = logging.FileHandler('../logs/main.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

## 为什么要加上下面两行才不会出错？否则
## File "main.py", line 241, in remindUserTopicUpdates
##    postMsg = '#' + str(topicTitle) + '# 有新进展：' + str(topic_news.title) + '(' + str(weibo.getShortUrl(topic_news.link)) + ')'
## UnicodeEncodeError: 'ascii' codec can't encode characters in position 0-4: ordinal not in range(128)
## 参考资料http://www.oschina.net/question/119303_21679
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import __builtin__

__builtin__._DEBUG= True

from multiprocessing import Process, Lock
__builtin__.weibo_lock = Lock()
__builtin__.reader_lock = Lock()

# Init weibo
from libweibo import weiboAPI
[access_token, expires_in] = djangodb.get_or_update_weibo_auth_info(3041970403)
weibo = weiboAPI.weiboAPI(access_token = access_token, expires_in = expires_in, u_id = 3041970403)
logger.info('Sina Weibo 登录信息:\t' + weibo.getUserInfo()['name'])
__builtin__.weibo = weibo

# Init google reader
from libgreader import GoogleReader
reader = GoogleReader()
logger.info('Google Reader 登录信息:\t' + reader.getUserInfo()['userName'])
__builtin__.reader = reader

from checkweibo import t_checkweibo
from newstimeline import update_all_news_timeline
from checkreader import t_checkreader
from exetask import t_exetask

if __name__ == '__main__':
    logger.info('Start update_all_news_timeline')
    update_all_news_timeline()

    logger.info('Start multiprocessing.Process(target=t_checkweibo).start()')
    Process(target=t_checkweibo, args=()).start()
    logger.info('Start multiprocessing.Process(target=t_checkreader).start()')
    Process(target=t_checkreader, args=()).start()
    logger.info('Start multiprocessing.Process(target=t_exetask).start()')
    Process(target=t_exetask, args=()).start()
    logger.info('All process started')


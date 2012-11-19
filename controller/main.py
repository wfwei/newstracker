# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 10, 2012

@author: plex
'''

# # 为什么要加上下面两行才不会出错？否则
# # File "main.py", line 241, in remindUserTopicUpdates
# #    postMsg = '#' + str(topicTitle) + '# 有新进展：' + str(topic_news.title) + '(' + str(weibo.getShortUrl(topic_news.link)) + ')'
# # UnicodeEncodeError: 'ascii' codec can't encode characters in position 0-4: ordinal not in range(128)
# # 参考资料http://www.oschina.net/question/119303_21679
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import __builtin__
__builtin__._DEBUG = True
import logging

fulllogger = logging.getLogger('fulllogger')
hdlr = logging.FileHandler('../logs/full.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
fulllogger.addHandler(hdlr)
fulllogger.setLevel(logging.DEBUG)

splogger = logging.getLogger('splogger')
hdlr = logging.FileHandler('../logs/sp.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
splogger.addHandler(hdlr)
splogger.setLevel(logging.DEBUG)

weibologger = logging.getLogger('weibologger')
hdlr = logging.FileHandler('../logs/weibo.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
weibologger.addHandler(hdlr)
hdlr2 = logging.FileHandler('../logs/full.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr2.setFormatter(formatter)
weibologger.addHandler(hdlr2)
weibologger.setLevel(logging.DEBUG)

readerlogger = logging.getLogger('readerlogger')
hdlr = logging.FileHandler('../logs/reader.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
readerlogger.addHandler(hdlr)
hdlr2 = logging.FileHandler('../logs/full.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr2.setFormatter(formatter)
readerlogger.addHandler(hdlr2)
readerlogger.setLevel(logging.DEBUG)

tasklogger = logging.getLogger('tasklogger')
hdlr = logging.FileHandler('../logs/task.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
tasklogger.addHandler(hdlr)
hdlr2 = logging.FileHandler('../logs/full.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr2.setFormatter(formatter)
tasklogger.addHandler(hdlr2)
tasklogger.setLevel(logging.DEBUG)

__builtin__.fulllogger = fulllogger
__builtin__.splogger = splogger
__builtin__.weibologger = weibologger
__builtin__.readerlogger = readerlogger
__builtin__.tasklogger = tasklogger

from multiprocessing import Process
import time

# Init weibo
from libweibo import weiboAPI
from djangodb import djangodb
[access_token, expires_in] = djangodb.get_or_update_weibo_auth_info(3041970403)
if time.time() > expires_in:
    raise Exception("授权过期了!")
weibo = weiboAPI.weiboAPI(access_token=access_token, expires_in=expires_in, u_id=3041970403)
fulllogger.info('Sina Weibo 登录信息:\t' + weibo.getUserInfo()['name'])
__builtin__.weibo = weibo

# Init google reader
from libgreader import readerAPI
reader = readerAPI()
fulllogger.info('Google Reader 登录信息:\t' + reader.getUserInfo()['userName'])
__builtin__.reader = reader

from checkweibo import t_checkweibo
from newstimeline import update_all_news_timeline
from checkreader import t_checkreader
from exetask import t_exetask

if __name__ == '__main__':
    fulllogger.info('Start update_all_news_timeline')
    update_all_news_timeline()

    fulllogger.info('Start multiprocessing.Process(target=t_checkweibo).start()')
    Process(target=t_checkweibo, args=()).start()
    fulllogger.info('Start multiprocessing.Process(target=t_checkreader).start()')
    Process(target=t_checkreader, args=()).start()
    fulllogger.info('Start multiprocessing.Process(target=t_exetask).start()')
    Process(target=t_exetask, args=()).start()
    fulllogger.info('All process started')


#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 13, 2012

@author: plex
'''
from weibo import APIClient
import time
import threading

####网页应用的配置
APP_KEY = '4057638893'
APP_SECRET = '29a39034c98cbd0c9703192707653f10'
CALLBACK_URL = 'http://110.76.40.188:81/weibo_callback/'

import __builtin__
try:
    logger = __builtin__.splogger
except:
    import logging
    logger = logging.getLogger('nonlogger')

class weiboAPI(object):
    '''
    该类是线程安全的，特别是需要使用weibo链接网络的方法一定要加锁，还有就是判断访问频次的方法也要加锁
    如果要用户授权，要保证授权未过期！！
    TODO:
    1. 添加自动登录功能
    '''

    def __init__(self, access_token=None, expires_in=None, u_id = None):
        self.client = APIClient(app_key=APP_KEY,
                                app_secret=APP_SECRET,
                                redirect_uri=CALLBACK_URL,
                                )
        self.u_id = u_id
        self.REMIND_WEIBO_ID = 3504267275499498
        self.lock = threading.Lock() ##多线程同步
        self.acc_count = {}
        self.acc_limit = {}
        self._initAccessCount()
        self._initAccessLimit()
        if access_token is not None and expires_in is not None:
            self.client.set_access_token(access_token, expires_in)
            self.refreshAccessToken()
            logger.info('current user:' + str(u_id) + \
                        '\naccess_token:' + str(access_token) + \
                        '\nexpires_in' + str(expires_in))
        else:
            logger.info('just weibo client, no user authorized')

    def _initAccessCount(self):
        '''
        该方法没有加锁，要求调用的方法必须是线程安全的
        '''
        self.acc_count['hour'] = time.localtime().tm_hour
        self.acc_count['ip_all'] = 0 #单小时限制:10000
        self.acc_count['user_all'] = 0 #单小时限制:1000
        self.acc_count['user_status'] = 0 #单小时限制:30
        self.acc_count['user_comment'] = 0 #单小时限制:60
        self.acc_count['user_follow'] = 0 #单小时限制:60;这个还有每天的限制，没有考虑
        
        logger.info('_initAccessCount:\t' + str(self.acc_count))

    def _initAccessLimit(self):
        '''
        该方法没有加锁，要求调用的方法必须是线程安全的
        '''
        self.acc_limit['time_unit'] = 'hour'
        self.acc_limit['ip_all'] = 10000 - 100 ##减去这些值是为了考虑到有漏掉的访问
        self.acc_limit['user_all'] = 1000 - 20
        self.acc_limit['user_status'] = 30 - 5
        self.acc_limit['user_comment'] = 60 - 10
        self.acc_limit['user_follow'] = 60 - 10 #这个还有每天的限制，没有考虑

        logger.info('_initAccessLimit:\t' + str(self.acc_limit))

    def _checkAccessLimit(self, type='ip_all'):
        '''
        线程安全
        '''
        with self.lock:
            logger.info('_checkAccessLimit, type:' + str(type))
            logger.info('old acc_count:\t' + str(self.acc_count))
    
            ##MARK: 两小时刷新一次记录会不会过分了
            if self.acc_count['hour'] < time.localtime().tm_hour or \
                self.acc_count['hour'] > time.localtime().tm_hour + 1:
                self._initAccessCount()
            else:
                self.acc_count[type] += 1
                if type != 'ip_all':
                    self.acc_count['ip_all'] += 1
                self.acc_count['user_all'] += 1
    
            logger.info('new acc_count:\t' + str(self.acc_count))
    
            if self.acc_count[type] > self.acc_limit[type] or \
             self.acc_count['ip_all'] > self.acc_limit['ip_all'] or \
             self.acc_count['user_all'] > self.acc_limit['user_all']:
                sleeptime = (60 - time.localtime().tm_min + 65) * 60 ##MARK目前多睡１小时。。。
                logger.info('access limit reached, sleep for ' + str(sleeptime / 60) + ' minutes')
                time.sleep(sleeptime)
        
    def refreshAccessToken(self):
        '''
        这个方法实现自动授权？
        '''
        logger.info('refreshAccessToken')
        if self.client.is_expires():
            logger.error('refreshAccessToken: access_token is expired')
            self._setAccessTokenManually()
            
    def _setAccessTokenManually(self):
        url = self.client.get_authorize_url()
        print 'weibo.refreshAccessToken 访问url获取认证code\n',url
        # TODO:能否impl自动认证
        code = raw_input()
        r = self.client.request_access_token(code)
        access_token = r.access_token  # 新浪返回的token，类似abc123xyz456
        expires_in = r.expires_in  # token过期的UNIX时间：http://zh.wikipedia.org/wiki/UNIX%E6%97%B6%E9%97%B4
        self.client.set_access_token(access_token, expires_in)

    def getAuthorizeUrl(self):
        '''该方法没有访问服务器，只是静态的字符串拼接，不需要加锁'''
        return self.client.get_authorize_url()

    def getHotTopics(self):
        '''得到一周的热门话题'''
        self._checkAccessLimit()
        with self.lock:
            return self.client.get.trends__weekly()['trends']

    def getUID(self):
        '''得到当前授权用户的ID
        TODO: 添加判断授权的机制
        '''
        self._checkAccessLimit()
        with self.lock:
            return self.client.get.account__get_uid()['uid']

    def getUserInfo(self, uid=None):
        ''' 获取用户信息
         如果uid非空，请求uid的用户信息
       　如果uid是空，则请求当前授权用户的用户信息
        '''
        self._checkAccessLimit()
        with self.lock:
            if uid is not  None:
                _uid = uid
            elif self.u_id is None:
                _uid = self.getUID()
                time.sleep(2) ##间隔两次请求
            else:
                _uid = self.u_id
            return self.client.get.users__show(uid=_uid)
        

    def getMentions(self, count = 50, page = 1, since_id = 0, trim_user = 0):
        '''得到当前授权用户的mention信息'''
        self._checkAccessLimit()
        with self.lock:
            return self.client.get.statuses__mentions(count = count, \
                                                 page = page, \
                                                 since_id = since_id, \
                                                 trim_user = trim_user)

    def postComment(self, weibo_id, content):
        ''' 发布评论　'''
        self._checkAccessLimit('user_comment')
        with self.lock:
            try:
                self.client.post.comments__create(comment=content, id=weibo_id)
                return True
            except:
                logger.warn('target weibo does not exist!\t' + str(weibo_id))
            return False

    def getShortUrl(self, url_long):
        ''' 获得短鏈　'''
        self._checkAccessLimit()
        with self.lock:
            return self.client.get.short_url__shorten(url_long=url_long)['urls'][0]['url_short']

    def getLongUrl(self, url_short):
        ''' 获得长鏈　'''
        self._checkAccessLimit()
        with self.lock:
            return self.client.get.short_url__expand(url_short=url_short)['urls'][0]['url_long']

    def setAccessToken(self, access_token, expires_in):
        '''  '''
        with self.lock:
            self.client.set_access_token(access_token, expires_in)


if __name__ == '__main__':
    pass




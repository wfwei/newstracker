# !/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 13, 2012

@author: plex
'''
from weibo import APIClient

import time
import threading

# 网页应用的配置
APP_KEY = '3233912973'
APP_SECRET = '289ae4ee3da84d8c4c359312dc2ca17d'
CALLBACK_URL = 'http://110.76.40.188/weibo_callback/'

import logging
logger = logging.getLogger('closed')

class weiboAPI(object):
    '''
    该类是线程安全的，特别是需要使用weibo链接网络的方法一定要加锁，还有就是判断访问频次的方法也要加锁
    如果要用户授权，要保证授权未过期！！
    
    '''

    def __init__(self, access_token=None, expires_in=None, u_id=None):
        self.client = APIClient(app_key=APP_KEY,
                                app_secret=APP_SECRET,
                                redirect_uri=CALLBACK_URL,
                                )
        self.u_id = u_id
        self.REMIND_WEIBO_ID = 3504267275499498
        self.lock = threading.Lock()  # #多线程同步
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
        self.acc_count['ip_all'] = 0  # 单小时限制:10000
        self.acc_count['user_all'] = 0  # 单小时限制:1000
        self.acc_count['user_status'] = 0  # 单小时限制:30
        self.acc_count['user_comment'] = 0  # 单小时限制:60
        self.acc_count['user_follow'] = 0  # 单小时限制:60;这个还有每天的限制，没有考虑

        logger.info('_initAccessCount:\t' + str(self.acc_count))

    def _initAccessLimit(self):
        '''
        该方法没有加锁，要求调用的方法必须是线程安全的
        '''
        self.acc_limit['time_unit'] = 'hour'
        self.acc_limit['ip_all'] = 10000 - 100  # #减去这些值是为了考虑到有漏掉的访问
        self.acc_limit['user_all'] = 1000 - 20
        self.acc_limit['user_status'] = 30 - 5
        self.acc_limit['user_comment'] = 60 - 10
        self.acc_limit['user_follow'] = 60 - 10  # 这个还有每天的限制，没有考虑

        logger.info('_initAccessLimit:\t' + str(self.acc_limit))

    def _checkAccessLimit(self, type='ip_all'):
        '''
        线程安全
        '''
        with self.lock:
            logger.info('_checkAccessLimit, type:' + str(type))
            logger.info('old acc_count:\t' + str(self.acc_count))

            # #MARK: 两小时刷新一次记录会不会过分了
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
                sleeptime = (60 - time.localtime().tm_min + 65) * 60  # #MARK目前多睡１小时。。。
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
        print 'weibo.refreshAccessToken 访问url获取认证code\n', url
        # TODO:能否impl自动认证
        code = raw_input()
        r = self.client.request_access_token(code)
        access_token = r.access_token  # 新浪返回的token，类似abc123xyz456
        expires_in = r.expires_in  # token过期的UNIX时间：http://zh.wikipedia.org/wiki/UNIX%E6%97%B6%E9%97%B4
        self.client.set_access_token(access_token, expires_in)

    def getAuthorizeUrl(self):
        '''该方法没有访问服务器，只是静态的字符串拼接，不需要加锁'''
        return self.client.get_authorize_url()

    def getWeeklyHotTopics(self):
        '''得到一周的热门话题'''
        self._checkAccessLimit()
        with self.lock:
            return self.client.get.trends__weekly()['trends']

    def getDailyHotTopics(self):
        '''得到一周的热门话题'''
        self._checkAccessLimit()
        with self.lock:
            return self.client.get.trends__daily()['trends']

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
            else:
                _uid = self.u_id
            return self.client.get.users__show(uid=_uid)


    def getMentions(self, count=50, page=1, since_id=0, trim_user=0):
        ''' 得到当前授权用户的mention信息 '''
        self._checkAccessLimit()
        with self.lock:
            return self.client.get.statuses__mentions(count=count, \
                                                      page=page, \
                                                      since_id=since_id, \
                                                      trim_user=trim_user)

    def postComment(self, weibo_id, content):
        ''' 发布评论　'''
        self._checkAccessLimit('user_comment')
        with self.lock:
            if len(content) > 139:
                content = content[:139]
            return self.client.post.comments__create(comment=content, id=weibo_id)

    def repostStatus(self, weibo_id, content, is_comment=3):
        '''　转发微博
        
            一些参数：
            参数    必选    类型及范围    说明
            id    true    int64    要转发的微博ID。
            status    false    string    添加的转发文本，必须做URLencode，内容不超过140个汉字，不填则默认为“转发微博”。
            is_comment    false    int    是否在转发的同时发表评论，0：否、1：评论给当前微博、2：评论给原微博、3：都评论，默认为0 
        '''
        self._checkAccessLimit('user_status')
        with self.lock:
            if len(content) > 139:
                content = content[:139]
            return self.client.post.statuses__repost(id=weibo_id, \
                                                     status=content, \
                                                     is_comment=is_comment)

    def updateStatus(self, content, visible=0):
        '''　发布新微博
        
            一些参数：
            参数    必选    类型及范围    说明
            status    true    string    要发布的微博文本内容，必须做URLencode，内容不超过140个汉字。
            visible    false    int    微博的可见性，0：所有人能看，1：仅自己可见，2：密友可见，3：指定分组可见，默认为0。
            list_id    false    string    微博的保护投递指定分组ID，只有当visible参数为3时生效且必选。
            lat    false    float    纬度，有效范围：-90.0到+90.0，+表示北纬，默认为0.0。
            long    false    float    经度，有效范围：-180.0到+180.0，+表示东经，默认为0.0。
            annotations    false    string    元数据，主要是为了方便第三方应用记录一些适合于自己使用的信息，每条微博可以包含一个或者多个元数据，必须以json字串的形式提交，字串长度不超过512个字符，具体内容可以自定。
        '''
        self._checkAccessLimit('user_status')
        with self.lock:
            if len(content) > 139:
                content = content[:139]
            return self.client.post.statuses__update(status=content, visible=visible)

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

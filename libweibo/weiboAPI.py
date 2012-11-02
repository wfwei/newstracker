#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 13, 2012

@author: plex
'''
from weibo import APIClient
import time

####网页应用的配置
APP_KEY = '4057638893'
APP_SECRET = '20771c2157efe0659eead33718e4feae'
CALLBACK_URL = 'http://110.76.40.188:81/weibo_callback/'

class weiboAPI(object):         
    '''
    TODO: 
    1. 添加自动登录功能
    2. 每个方法检查授权是否过期
    3. test 计数请求次数
    '''
    
    def __init__(self, access_token=None, expires_in=None, u_id = None):
        '''
        Constructor
        '''
        self.client = APIClient(app_key=APP_KEY,
                                app_secret=APP_SECRET,
                                redirect_uri=CALLBACK_URL,
                                )
        self.u_id = u_id
        self.REMIND_WEIBO_ID = 3504267275499498
        self.acc_count = {}
        self.acc_limit = {}
        self._initAccessCount()
        self._initAccessLimit()
        if access_token is not None and access_token is not None:
            self.client.set_access_token(access_token, expires_in)
            self.refreshAccessToken()
        else:
            print u_id, ' not set access token yet'

    def _initAccessCount(self):
        self.acc_count['hour'] = time.localtime().tm_hour
        self.acc_count['ip_all'] = 0 #单小时限制:1000
        self.acc_count['user_all'] = 0 #单小时限制:150
        self.acc_count['user_status'] = 0 #单小时限制:30
        self.acc_count['user_comment'] = 0 #单小时限制:60
        self.acc_count['user_follow'] = 0 #单小时限制:60;这个还有每天的限制，没有考虑
        
    def _initAccessLimit(self):
        self.acc_limit['time_unit'] = 'hour'
        self.acc_limit['ip_all'] = 1000 - 100 ##减去这些值是为了考虑到有漏掉的访问
        self.acc_limit['user_all'] = 150 - 20
        self.acc_limit['user_status'] = 30 - 5
        self.acc_limit['user_comment'] = 60 - 10
        self.acc_limit['user_follow'] = 60 - 10 #这个还有每天的限制，没有考虑
    
    def _checkAccessLimit(self, type='ip_all'):
        if self.acc_count['hour'] != time.localtime().tm_hour:
            self._initAccessCount()
        else:
            self.acc_count[type] += 1
            if type != 'ip_all':
                self.acc_count['ip_all'] += 1
            self.acc_count['user_all'] += 1
            
            if self.acc_count[type] > self.acc_limit[type] or \
             self.acc_count['ip_all'] > self.acc_limit['ip_all'] or \
             self.acc_count['user_all'] > self.acc_limit['user_all']:
                sleeptime = (60 - time.localtime().tm_min + 10) * 60 ##多休息10分钟，考虑系统刷新延迟等因素
                print 'access limit reached, sleep for ' + str(sleeptime / 60) + ' minutes'
                time.sleep(sleeptime)
                
            
    
    def refreshAccessToken(self):
        if self.client.is_expires():
            url = self.client.get_authorize_url()
            print 'weibo.refreshAccessToken 访问url获取认证code\n',url
            # 获取URL参数code: TODO:impl自动认证
            code = raw_input()
            u_id = raw_input()##TODO: how to get this information
            r = self.client.request_access_token(code)
            access_token = r.access_token  # 新浪返回的token，类似abc123xyz456
            expires_in = r.expires_in  # token过期的UNIX时间：http://zh.wikipedia.org/wiki/UNIX%E6%97%B6%E9%97%B4
            ## 考虑不要存数据库了，这个refreshAccessToken的功能貌似只有主帐号可以用，其他用户也用不到
#            djangodb.get_or_update_weibo_auth_info(u_id, access_token, expires_in)
            self.client.set_access_token(access_token, expires_in)
        print 'Weibo refresh Access Token Ok!!!'
    
    def getAuthorizeUrl(self):
        return self.client.get_authorize_url()
    
    def getHotTopics(self):
        self._checkAccessLimit()
        weekHotTopics = self.client.get.trends__weekly()['trends']
        return weekHotTopics
    
    def getUID(self):
        '''
        得到当前授权用户的ID，前提是要授权！！！
        TODO: 添加判断授权的机制
        '''
        self._checkAccessLimit()
        return self.client.get.account__get_uid()['uid']
    
    def getUserInfo(self, uid=None):
        '''
       　必须配置uid参数，如果没有会报错 
        '''
        if uid is not  None:
            self._checkAccessLimit()
            return self.client.get.users__show(uid=uid)
        if self.u_id is None:
            self.u_id = self.getUID()
        self._checkAccessLimit()
        return self.client.get.users__show(uid=self.u_id)
        
    def getMentions(self, count = 50, page = 1, since_id = 0, trim_user = 0):    
        self._checkAccessLimit()
        return self.client.get.statuses__mentions(count = count, page = page, since_id = since_id, trim_user = trim_user)
        
    def postComment(self, weibo_id, content):
        try:
            self._checkAccessLimit('user_comment')
            self.client.post.comments__create(comment=content, id=weibo_id)
            return True
        except:
            print 'target weibo does not exist!\t'+weibo_id
        return False
    
    def getShortUrl(self, url_long):
        self._checkAccessLimit()
        return self.client.get.short_url__shorten(url_long=url_long)['urls'][0]['url_short']
    
    def getLongUrl(self, url_short):
        self._checkAccessLimit()
        return self.client.get.short_url__expand(url_short=url_short)['urls'][0]['url_long']
    
    def setAccessToken(self, access_token, expires_in):
        self.client.set_access_token(access_token, expires_in)
        

if __name__ == '__main__':
    pass
    
        
    

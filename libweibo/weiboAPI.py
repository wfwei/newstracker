#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 13, 2012

@author: plex
'''
from weibo import APIClient

#站内应用的配置
#APP_KEY = '639210256'
#APP_SECRET = '2f6ab2ac68a561f7e63403e372a61f82'
#CALLBACK_URL = 'http://apps.weibo.com/newstracker'

####网页应用的配置
APP_KEY = '4057638893'
APP_SECRET = '20771c2157efe0659eead33718e4feae'
CALLBACK_URL = 'http://110.76.40.188:81/weibo_callback/'

REMIND_WEIBO_ID = 3504267275499498

class weiboAPI(object):         
    '''
    classdocs
    '''
    
    def __init__(self, access_token=None, expires_in=None, u_id = None):
        '''
        Constructor
        '''
        self.client = APIClient(app_key=APP_KEY,
                                app_secret=APP_SECRET,
                                redirect_uri=CALLBACK_URL,
                                )
        ## 刚加的，有些引用要改
        self.u_id = u_id
        if access_token is not None and access_token is not None:
            self.client.set_access_token(access_token, expires_in)
            self.refreshAccessToken()
        else:
            print u_id, ' not set access token yet'

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
        weekHotTopics = self.client.get.trends__weekly()['trends']
        return weekHotTopics
    
    def getUID(self):
        '''
        得到当前授权用户的ID，前提是要授权！！！
        TODO: 添加判断授权的机制
        '''
        return self.client.get.account__get_uid()['uid']
    
    def getUserInfo(self, uid=None):
        '''
       　必须配置uid参数，如果没有会报错 
        '''
        if uid is not  None:
            return self.client.get.users__show(uid=uid)
        if self.u_id is None:
            self.u_id = self.getUID() 
        return self.client.get.users__show(uid=self.u_id)
        
    def getMentions(self, count = 50, page = 1, since_id = 0, trim_user = 0):    
        return self.client.get.statuses__mentions(count = count, page = page, since_id = since_id, trim_user = trim_user)
        
    def postComment(self, weibo_id, content):
        try:
            self.client.post.comments__create(comment=content, id=weibo_id)
            return True
        except:
            print 'target weibo does not exist!\t'+weibo_id
        return False
    
    def getShortUrl(self, url_long):
        return self.client.get.short_url__shorten(url_long=url_long)['urls'][0]['url_short']
    
    def getLongUrl(self, url_short):
        return self.client.get.short_url__expand(url_short=url_short)['urls'][0]['url_long']
    
    def setAccessToken(self, access_token, expires_in):
        self.client.set_access_token(access_token, expires_in)
        

if __name__ == '__main__':
    pass
#    测试站内应用
    [access_token, expires_in] = ['2.00l9nr_D0qmDQhc1ef1ea942R3rHrB', 1351052312]
    weibo = weiboAPI(access_token = access_token, expires_in = expires_in, u_id = 3041970403)
    
        
    

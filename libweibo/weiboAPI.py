#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 13, 2012

@author: plex
'''
from weibo import APIClient
from djangodb import djangodb

APP_KEY = '639210256'  # kvpair key
APP_SECRET = '2f6ab2ac68a561f7e63403e372a61f82'  # kvpair secret
#CALLBACK_URL = 'https://api.weibo.com/oauth2/default.html'  # callback url
#CALLBACK_URL = 'http://localhost:8000/weiboLogin/'
CALLBACK_URL = 'http://apps.weibo.com/newstracker'

class weiboAPI(object):         
    '''
    classdocs
    '''
    def refreshAccessToken(self):
        if self.client.is_expires():
            url = self.client.get_authorize_url()
            print '访问url获取认证code\n',url
            # 获取URL参数code: TODO:impl自动认证
            code = raw_input()
            u_id = raw_input()##TODO: how to get this information
            r = self.client.request_access_token(code)
            access_token = r.access_token  # 新浪返回的token，类似abc123xyz456
            expires_in = r.expires_in  # token过期的UNIX时间：http://zh.wikipedia.org/wiki/UNIX%E6%97%B6%E9%97%B4
            ## 保存到配置文件中
            djangodb.get_or_update_weibo_auth_info(u_id, access_token, expires_in)
#            self.weibo_config.updateKeyVal('access_token', access_token)
#            self.weibo_config.updateKeyVal('expires_in', expires_in)
            self.client.set_access_token(access_token, expires_in)
        print 'Weibo refresh Access Token Ok!!!'
    
    def getAuthorizeUrl(self):
        return self.client.get_authorize_url()
    
    def getHotTopics(self):
        weekHotTopics = self.client.get.trends__weekly()['trends']
        return weekHotTopics
    
    def getUserInfo(self, uid=None):
        if uid is None:
            uid = self.weibo_config.u_id
        return self.client.get.users__show(uid=uid)
        
    def getMentions(self, count = 50, page = 1, since_id = 0, trim_user = 0):    
        return self.client.get.statuses__mentions()
        
    def postComment(self, weibo_id, content):
        try:
            self.client.post.comments__create(comment=content, id=weibo_id)
            return True
        except:
            print 'target weibo does not exist!\t'+weibo_id
        return False
    
    def getShortUrl(self, url_long):
        ## TODO: 容错措施
        return self.client.get.short_url__shorten(url_long=url_long)['urls'][0]['url_short']
    
    def getLongUrl(self, url_short):
        ## TODO: 容错措施
        return self.client.get.short_url__expand(url_short=url_short)['urls'][0]['url_long']
    
    def __init__(self, access_token=None, expires_in=None):
        '''
        Constructor
        '''
        self.client = APIClient(app_key=APP_KEY,
                                app_secret=APP_SECRET,
                                redirect_uri=CALLBACK_URL,
                                )
        if(access_token is not None and expires_in is not None):
            self.client.set_access_token(access_token, expires_in)
            self.refreshAccessToken()
        else:
            print 'not set access token'
        

if __name__ == '__main__':
    weibo = weiboAPI()
    weibo.refreshAccessToken()
    
#    weibo.getHotTopics()

#    surl = weibo.getShortUrl("http://www.wrfrwrrr.com/")
#    lurl = weibo.getLongUrl(surl['urls'][0]['url_short'])
#    print surl
#    print lurl

    mentions = weibo.getMentions()
    print mentions
    
        
    
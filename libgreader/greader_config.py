#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on Oct 13, 2012

@author: plex
'''
from djangodb import djangodb
from auth import OAuth2Method

_DEBUG = False

class GReaderConfig(object):
    '''
    Google Reader 的配置
    '''
    def __init__(self):
        self.username = self._getVal('username')
        self.password = self._getVal('password')
        self.client_id     = self._getVal('client_id')
        self.client_secret = self._getVal('client_secret')
        self.redirect_url  = self._getVal('redirect_url')
        
        # 只保存refresh_token(长期有效)
        # access_token的有效期只有一个小时,所以不保存        
        self.refresh_token = self._getVal('refresh_token')
        # 登录,获取auth
        self.auth = self._oauth2_login(self.client_id,
                                      self.client_secret,
                                      self.refresh_token,
                                      self.redirect_url)
        
    def updateKeyVal(self, _key, _val):
        try:
            kvpair = djangodb.GReaderConfig.objects.get(key=_key)
            kvpair.value=_val
            kvpair.save()
        except djangodb.GReaderConfig.DoesNotExist:
            djangodb.GReaderConfig.objects.create(key=_key,value=_val)
        if _DEBUG:
            print 'create or updated:\t', _key,_val 
    
    def _getVal(self,_key):
        val = None
        try:
            val = djangodb.GReaderConfig.objects.get(key=_key).value
        except djangodb.GReaderConfig.DoesNotExist:
            print 'non-exist key:', _key
        
        if _DEBUG:
            print 'get kvpair from db ', _key, val
        return val
    
    '''
    access_token有效期是一个小时,refresh_token长久有效,直到用户剥夺应用的权限
    
    同一个用户同一个应用可以生成多个refresh_token,且都能用
    
    refresh_token放到数据库中
    '''
    def _oauth2_login(self, client_id, client_secret, refresh_token, redirect_url):
        auth = OAuth2Method(client_id, client_secret, refresh_token)
        auth.setRedirectUri(redirect_url)
        if(len(refresh_token)<1):
            url = auth.buildAuthUrl()
            print '访问该地址授权',url
            auth.code = raw_input()
            auth.setAccessToken()
        else:
            auth.refreshAccessToken()
        auth.setActionToken()
        print 'Google Reader login OK!'
        return auth

if __name__ == '__main__':
    gConfig = GReaderConfig()
    ##开始的时候初始化GReaderConfig
#    gConfig.updateKeyVal('username', 'newstrackerpro@gmail.com')
#    gConfig.updateKeyVal('password', 'wangfengwei')
#    gConfig.updateKeyVal('client_id', '6030332710.apps.googleusercontent.com')
#    gConfig.updateKeyVal('client_secret', 'TZv3m1Zbodu_rqwg4XDa9CZC')
#    gConfig.updateKeyVal('redirect_url', 'urn:ietf:wg:oauth:2.0:oob')
#    gConfig.updateKeyVal('refresh_token', '1/Jh_gCO2V3EAtMU0_MbKOHt5Fq0fivY602aN56nikjmk')


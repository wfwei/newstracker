#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on Oct 13, 2012

@author: plex
'''
from djangodb import djangodb

#APP_KEY = '639210256'  # kvpair key
#APP_SECRET = '2f6ab2ac68a561f7e63403e372a61f82'  # kvpair secret
#CALLBACK_URL = 'https://api.weibo.com/oauth2/default.html'  # callback url
#access_token = '2.00KDQyqB0qmDQhb557b8a0c006xwBv'
#expires_in = 1350241200
#u_id = 1698863684

_DEBUG = False  

class WeiboConfig(object):

    def __init__(self):
        self.APP_KEY = self._getVal('APP_KEY')
        self.APP_SECRET = self._getVal('APP_SECRET')
        self.CALLBACK_URL = self._getVal('CALLBACK_URL')
        self.access_token = self._getVal('access_token')
        self.expires_in = self._getVal('expires_in')
        self.u_id = self._getVal('u_id')
        
    def updateKeyVal(self, _key, _val):
        try:
            kvpair = djangodb.WeiboConfig.objects.get(key=_key)
            kvpair.value=_val
            kvpair.save()
        except djangodb.WeiboConfig.DoesNotExist:
            djangodb.WeiboConfig.objects.create(key=_key,value=_val)
            
        if _DEBUG:
            print 'create or updated:\t', _key,_val 
    
    def _getVal(self,_key):
        val = None
        try:
            val = djangodb.WeiboConfig.objects.get(key=_key).value
        except djangodb.WeiboConfig.DoesNotExist:
            print 'non-exist key:', _key
        if _DEBUG:
            print 'get kvpair from db ', _key, val
        return val
    
if __name__ == '__main__':
    wcon = WeiboConfig()
#    wcon.updateKeyVal('APP_KEY',APP_KEY)
#    wcon.updateKeyVal('APP_SECRET',APP_SECRET)
#    wcon.updateKeyVal('CALLBACK_URL',CALLBACK_URL)
#    wcon.updateKeyVal('access_token',access_token)
#    wcon.updateKeyVal('expires_in',expires_in)
#    wcon.updateKeyVal('u_id',u_id)
        
    
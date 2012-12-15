# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 28, 2012

@author: plex
'''

# # Init google reader
# from libgreader import GoogleReader
# reader = GoogleReader()
# print 'Google Reader 登录信息:\t' + reader.getUserInfo()['userName']

from libweibo import weiboAPI

[access_token, expires_in] = ['2.00l9nr_DbO8b7Eff8cd4a1b9_wJOEB', 2510466805]

weibo = weiboAPI.weiboAPI(access_token=access_token, expires_in=expires_in, u_id=3041970403)
# print ('Sina Weibo 登录信息:\t' + weibo.getUserInfo()['name'])

# wbs = weibo.client.search__topics(q='曼联', count=50, page=1)
wbs2 = weibo.client.search__suggestions__statuses(q=u'曼联')
users = weibo.client.suggestions__users__by_status(content=u'曼联')
print wbs2


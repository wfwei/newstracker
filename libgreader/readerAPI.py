#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Nov 13, 2012

@author: plex
'''

import time
import threading

try:
    import json
except:
    import simplejson as json

from url import ReaderUrl
from items import Item, Category, Feed
from auth import OAuth2Method

USERNAME = 'newstrackerpro@gmail.com'
PASSWORD = 'wangfengwei'
CLIENT_ID = '6030332710.apps.googleusercontent.com'
CLIENT_SECRET = 'TZv3m1Zbodu_rqwg4XDa9CZC'
REDIRECT_URL = 'urn:ietf:wg:oauth:2.0:oob'
REFRESH_TOKEN = '1/Jh_gCO2V3EAtMU0_MbKOHt5Fq0fivY602aN56nikjmk'

_DEBUG = True

class readerAPI(object):
    """
    线程安全的API
    """
    def __repr__(self):
        return "<Google Reader object: %s>" % self.auth.username

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return "<Google Reader object: %s>" % self.auth.username

    def __init__(self):
        self.auth           = self._getOAuth2(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, REDIRECT_URL)
        self.userId         = None
        self.lock           = threading.Lock()
        
    def _getOAuth2(self, client_id, client_secret, refresh_token, redirect_url):
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
        return auth

    def getUnreadFeeds(self):
        '''
        得到含有unread条目的Feed,并以列表的形式返回
        例子:
         {u'user/11942290202134524999/state/com.google/reading-list': 22, u'feed/http://news.google.
 com.hk/news?hl=zh-CN&gl=cn&q=Obama&um=1&ie=UTF-8&output=rss': 6, u'feed/...': 4, u'feed/...: 12}
        '''
        with self.lock:
            unreadFeedsDict = {}
            if not self.userId:
                self.setUserId()
            unreadJson = self.httpGet(ReaderUrl.UNREAD_COUNT_URL, { 'output': 'json', })
            unreadCounts = json.loads(unreadJson, strict=False)['unreadcounts']
            for unread in unreadCounts:
                unreadFeedsDict[unread['id']] = unread['count']
            return unreadFeedsDict
    
    def fetchFeedItems(self, rss, excludeRead=False, continuation=None):
        """
        Return itemSet for a particular feed
        每次最多返回20个item,如果还有更多,则提供continuation字段
        """
        with self.lock:
            feed = Feed(self, 'title', rss)
            return self._getFeedContent(feed.fetchUrl, excludeRead, continuation)
        
    def markFeedAsRead(self, feedId):
        '''
        feedId就是feed的url地址
        '''
        with self.lock:
            return self.httpPost(ReaderUrl.MARK_ALL_READ_URL, {'s': feedId, })

    def subscribe(self, feedUrl, title = None):
        """
        Adds a feed to the top-level subscription list

        Ubscribing seems idempotent, you can subscribe multiple times
        without error

        returns True or throws urllib2 HTTPError
        """
        with self.lock:
            parameters = {'ac':'subscribe', 's': feedUrl}
            if title is not None:
                parameters['t'] = title
            response = self.httpPost(
                ReaderUrl.SUBSCRIPTION_EDIT_URL,
                {'ac':'subscribe', 's': feedUrl})
            # FIXME - need better return API
            if response and 'OK' in response:
                return True
            else:
                return False

    def unsubscribe(self, feedUrl):
        """
        Removes a feed url from the top-level subscription list

        Unsubscribing seems idempotent, you can unsubscribe multiple times
        without error

        returns True or throws urllib2 HTTPError
        """
        with self.lock:
            response = self.httpPost(
                ReaderUrl.SUBSCRIPTION_EDIT_URL,
                {'ac':'unsubscribe', 's': feedUrl})
            # FIXME - need better return API
            if response and 'OK' in response:
                return True
            else:
                return False

    def getUserInfo(self):
        """
        Returns a dictionary of user info that google stores.
        """
        with self.lock:
            userJson = self.httpGet(ReaderUrl.USER_INFO_URL)
            userInfo = json.loads(userJson, strict=False)
            self.userId = userInfo['userId']
            return userInfo
    
    def setUserId(self, userId=None):
        """
        set user id
        """
        with self.lock:
            if userId:
                self.userId = userId
            elif self.userId is None:
                userJson = self.httpGet(ReaderUrl.USER_INFO_URL)
                self.userId = json.loads(userJson, strict=False)['userId']
        
    def _getFeedContent(self, url, excludeRead=False, continuation=None):
        """
        A list of itemSet (from a feed, a category or from URLs made with SPECIAL_ITEMS_URL)

        Returns a dict with
         :param id: (str, feed's id)
         :param continuation: (str, to be used to fetch more itemSet)
         :param itemSet:  array of dits with :
            - update (update timestamp)
            - author (str, username)
            - title (str, page title)
            - id (str)
            - content (dict with content and direction)
            - categories (list of categories including states or ones provided by the feed owner)
        """
        parameters = {}
        if excludeRead:
            parameters['xt'] = 'user/-/state/com.google/read'
        if continuation:
            parameters['c'] = continuation
        contentJson = self.httpGet(url, parameters)
        try:
            return json.loads(contentJson, strict=False)
        except:
            print 'contentJson:', contentJson
            raise
        
    def httpGet(self, url, parameters=None):
        """
        Wrapper around AuthenticationMethod get()
        """
        return self.auth.get(url, parameters)

    def httpPost(self, url, post_parameters=None):
        """
        Wrapper around AuthenticationMethod post()
        """
        return self.auth.post(url, post_parameters)

if __name__ == '__main__':
    reader = readerAPI()
    print 'Google Reader 登录信息:\t' + reader.getUserInfo()['userName']
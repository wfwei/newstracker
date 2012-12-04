# !/usr/bin/env python
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
from djangodb import djangodb


CLIENT_ID = '6030332710.apps.googleusercontent.com'
CLIENT_SECRET = 'TZv3m1Zbodu_rqwg4XDa9CZC'
REDIRECT_URL = 'urn:ietf:wg:oauth:2.0:oob'


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

    def __init__(self, u_id, access_token, refresh_token, expires_access):
        self.auth = self._getOAuth2(u_id=u_id, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, \
                                    access_token=access_token, refresh_token=refresh_token, \
                                    expires_access=expires_access, redirect_url=REDIRECT_URL)
        self.lock = threading.Lock()

    def _getOAuth2(self, u_id, client_id, client_secret, access_token, refresh_token, expires_access, redirect_url):
        auth = OAuth2Method(u_id=u_id, client_id=client_id, client_secret=client_secret, \
                           access_token=access_token, refresh_token=refresh_token, \
                           expires_access=expires_access, redirect_url=redirect_url)
        if not refresh_token:
            url = auth.buildAuthUrl()
            print '访问该地址授权', url
            auth.code = raw_input()
            auth.setAccessToken()
        elif auth.is_access_token_expires():
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

    def subscribe(self, feedUrl, title=None):
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

        TODO: does not work!!!!!!!!

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
            return userInfo

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
    # u_id=1对应的用户是
    # USERNAME = 'newstrackerpro@gmail.com'
    # PASSWORD = 'wangfengwei'
    # REFRESH_TOKEN = '1/Jh_gCO2V3EAtMU0_MbKOHt5Fq0fivY602aN56nikjmk'
    u_id = 1
    [access_token, refresh_token, access_expires] = djangodb.get_google_auth_info(u_id=u_id)

    reader = readerAPI(u_id=u_id, access_token=access_token, \
                       refresh_token=refresh_token, expires_access=access_expires)
    time.sleep(31)
    print reader.subscribe('feed/http://news.google.com.hk/news?hl=zh-CN&gl=cn&q=吸血鬼日记&um=1&ie=UTF-8&output=rss')
    time.sleep(31)
    reader2 = readerAPI(u_id=u_id, access_token=access_token, \
                       refresh_token=refresh_token, expires_access=access_expires)
    time.sleep(31)
    print reader2.subscribe('feed/http://news.google.com.hk/news?hl=zh-CN&gl=cn&q=实习医生格雷&um=1&ie=UTF-8&output=rss')
    time.sleep(31)

    print reader.subscribe('feed/http://news.google.com.hk/news?hl=zh-CN&gl=cn&q=行尸走肉&um=1&ie=UTF-8&output=rss')


    print 'Google Reader 登录信息:\t' + reader.getUserInfo()['userName']

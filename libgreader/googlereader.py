# # -*- coding: utf-8 -*-
# 
# import time
# 
# try:
#    import json
# except:
#    import simplejson as json
# 
# from url import ReaderUrl
# from items import Item, Category, Feed
# from auth import OAuth2Method
# 
# USERNAME = 'newstrackerpro@gmail.com'
# PASSWORD = 'wangfengwei'
# CLIENT_ID = '6030332710.apps.googleusercontent.com'
# CLIENT_SECRET = 'TZv3m1Zbodu_rqwg4XDa9CZC'
# REDIRECT_URL = 'urn:ietf:wg:oauth:2.0:oob'
# REFRESH_TOKEN = '1/Jh_gCO2V3EAtMU0_MbKOHt5Fq0fivY602aN56nikjmk'
# 
# _DEBUG = True
# 
# class GoogleReader(object):
#    """
#    Class for using the unofficial Google Reader API and working with
#    the data it returns.
# 
#    Requires valid google username and password.
#    """
#    def __repr__(self):
#        return "<Google Reader object: %s>" % self.auth.username
# 
#    def __str__(self):
#        return unicode(self).encode('utf-8')
# 
#    def __unicode__(self):
#        return "<Google Reader object: %s>" % self.auth.username
# 
#    def __init__(self):
#        self.auth           = self._getOAuth2(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, REDIRECT_URL)
#        self.feeds          = []
#        self.categories     = []
#        self.feedsById      = {}
#        self.categoriesById = {}
#        self.specialFeeds   = {}
#        self.orphanFeeds    = []
#        self.userId         = None
# 
#    def _getOAuth2(self, client_id, client_secret, refresh_token, redirect_url):
#        auth = OAuth2Method(client_id, client_secret, refresh_token)
#        auth.setRedirectUri(redirect_url)
#        if(len(refresh_token)<1):
#            url = auth.buildAuthUrl()
#            print '访问该地址授权',url
#            auth.code = raw_input()
#            auth.setAccessToken()
#        else:
#            auth.refreshAccessToken()
#        auth.setActionToken()
#        return auth
# 
#    def getUnreadFeeds(self):
#        '''
#        得到含有unread条目的Feed,并以列表的形式返回
#        例子:
#         {u'user/11942290202134524999/state/com.google/reading-list': 22, u'feed/http://news.google.
# com.hk/news?hl=zh-CN&gl=cn&q=Obama&um=1&ie=UTF-8&output=rss': 6, u'feed/...': 4, u'feed/...: 12}
#        '''
#        unreadFeedsDict = {}
#        if not self.userId:
#            self.getUserInfo()
#        unreadJson = self.httpGet(ReaderUrl.UNREAD_COUNT_URL, { 'output': 'json', })
#        unreadCounts = json.loads(unreadJson, strict=False)['unreadcounts']
#        for unread in unreadCounts:
#            unreadFeedsDict[unread['id']] = unread['count']
#        return unreadFeedsDict
# 
#    def fetchFeedItems(self, rss, excludeRead=False, continuation=None):
#        """
#        Return itemSet for a particular feed
#        每次最多返回20个item,如果还有更多,则提供continuation字段
#        """
#        feed = Feed(self,
#                    'title',
#                    rss)
#        return self._getFeedContent(feed.fetchUrl, excludeRead, continuation)
# 
#    def buildSubscriptionList(self):
#        """
#        Hits Google Reader for a users's alphabetically ordered list of feeds.
# 
#        Returns true if succesful.
#        """
#        self._clearLists()
#        unreadById = {}
# 
#        if not self.userId:
#            self.getUserInfo()
# 
#        unreadJson = self.httpGet(ReaderUrl.UNREAD_COUNT_URL, { 'output': 'json', })
#        unreadCounts = json.loads(unreadJson, strict=False)['unreadcounts']
#        for unread in unreadCounts:
#            unreadById[unread['id']] = unread['count']
# 
#        feedsJson = self.httpGet(ReaderUrl.SUBSCRIPTION_LIST_URL, { 'output': 'json', })
#        subscriptions = json.loads(feedsJson, strict=False)['subscriptions']
# 
#        for sub in subscriptions:
#            categories = []
#            if 'categories' in sub:
#                for hCategory in sub['categories']:
#                    cId = hCategory['id']
#                    if not cId in self.categoriesById:
#                        category = Category(self, hCategory['label'], cId)
#                        self._addCategory(category)
#                    categories.append(self.categoriesById[cId])
# 
#            try:
#                feed = self.getFeed(sub['id'])
#                if not feed:
#                    raise
#                if not feed.title:
#                    feed.title = sub['title']
#                for category in categories:
#                    feed.addCategory(category)
#                feed.unread = unreadById.get(sub['id'], 0)
#            except:
#                feed = Feed(self,
#                            sub['title'],
#                            sub['id'],
#                            sub.get('htmlUrl', None),
#                            unreadById.get(sub['id'], 0),
#                            categories)
#            if not categories:
#                self.orphanFeeds.append(feed)
#            self._addFeed(feed)
# 
#        specialUnreads = [id for id in unreadById
#                            if id.find('user/%s/state/com.google/' % self.userId) != -1]
#        for type in self.specialFeeds:
#            feed = self.specialFeeds[type]
#            feed.unread = 0
#            for id in specialUnreads:
#                if id.endswith('/%s' % type):
#                    feed.unread = unreadById.get(id, 0)
#                    break
# 
#        return True
# 
#    def _getFeedContent(self, url, excludeRead=False, continuation=None):
#        """
#        A list of itemSet (from a feed, a category or from URLs made with SPECIAL_ITEMS_URL)
# 
#        Returns a dict with
#         :param id: (str, feed's id)
#         :param continuation: (str, to be used to fetch more itemSet)
#         :param itemSet:  array of dits with :
#            - update (update timestamp)
#            - author (str, username)
#            - title (str, page title)
#            - id (str)
#            - content (dict with content and direction)
#            - categories (list of categories including states or ones provided by the feed owner)
#        """
#        parameters = {}
#        if excludeRead:
#            parameters['xt'] = 'user/-/state/com.google/read'
#        if continuation:
#            parameters['c'] = continuation
#        contentJson = self.httpGet(url, parameters)
#        try:
#            return json.loads(contentJson, strict=False)
#        except:
#            print 'contentJson:', contentJson
#            raise
# 
#    def itemsToObjects(self, parent, itemSet):
#        objects = []
#        for item in itemSet:
#            objects.append(Item(self, item, parent))
#        return objects
# 
#    def getFeedContent(self, feed, excludeRead=False, continuation=None):
#        """
#        Return itemSet for a particular feed
#        """
#        return self._getFeedContent(feed.fetchUrl, excludeRead, continuation)
# 
#    def getCategoryContent(self, category, excludeRead=False, continuation=None):
#        """
#        Return itemSet for a particular category
#        """
#        return self._getFeedContent(category.fetchUrl, excludeRead, continuation)
# 
#    def removeItemTag(self, item, tag):
#        return self.httpPost(ReaderUrl.EDIT_TAG_URL,
#                             {'i': item.id, 'r': tag, 'ac': 'edit-tags', })
# 
#    def addItemTag(self, item, tag):
#        return self.httpPost(
#            ReaderUrl.EDIT_TAG_URL,
#            {'i': item.id, 'a': tag, 'ac': 'edit-tags', })
# 
#    ## TODO: this is stupid
#    def markFeedAsRead(self, feed):
#        if isinstance(feed, Feed):
#            feedId = feed.id
#        else:
#            feedId = feed
#        return self.httpPost(
#            ReaderUrl.MARK_ALL_READ_URL,
#            {'s': feedId, })
# 
#    def subscribe(self, feedUrl, title = None):
#        """
#        Adds a feed to the top-level subscription list
# 
#        Ubscribing seems idempotent, you can subscribe multiple times
#        without error
# 
#        returns True or throws urllib2 HTTPError
#        """
#        parameters = {'ac':'subscribe', 's': feedUrl}
#        if title is not None:
#            parameters['t'] = title
#        response = self.httpPost(
#            ReaderUrl.SUBSCRIPTION_EDIT_URL,
#            {'ac':'subscribe', 's': feedUrl})
#        # FIXME - need better return API
#        if response and 'OK' in response:
#            return True
#        else:
#            return False
# 
#    def unsubscribe(self, feedUrl):
#        """
#        Removes a feed url from the top-level subscription list
# 
#        Unsubscribing seems idempotent, you can unsubscribe multiple times
#        without error
# 
#        returns True or throws urllib2 HTTPError
#        """
#        response = self.httpPost(
#            ReaderUrl.SUBSCRIPTION_EDIT_URL,
#            {'ac':'unsubscribe', 's': feedUrl})
#        # FIXME - need better return API
#        if response and 'OK' in response:
#            return True
#        else:
#            return False
# 
#    def getUserInfo(self):
#        """
#        Returns a dictionary of user info that google stores.
#        """
#        userJson = self.httpGet(ReaderUrl.USER_INFO_URL)
#        result = json.loads(userJson, strict=False)
#        self.userId = result['userId']
#        return result
# 
#    def getUserSignupDate(self):
#        """
#        Returns the human readable date of when the user signed up for google reader.
#        """
#        userinfo = self.getUserInfo()
#        timestamp = int(float(userinfo["signupTimeSec"]))
#        return time.strftime("%m/%d/%Y %H:%M", time.gmtime(timestamp))
# 
#    def httpGet(self, url, parameters=None):
#        """
#        Wrapper around AuthenticationMethod get()
#        """
#        return self.auth.get(url, parameters)
# 
#    def httpPost(self, url, post_parameters=None):
#        """
#        Wrapper around AuthenticationMethod post()
#        """
#        return self.auth.post(url, post_parameters)
# 
#    def _clearLists(self):
#        """
#        Clear all list before sync : feeds and categories
#        """
#        self.feedsById      = {}
#        self.feeds          = []
#        self.categoriesById = {}
#        self.categories     = []
#        self.orphanFeeds    = []

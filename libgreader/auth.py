# -*- coding: utf-8 -*-

import urllib
import urllib2
import urlparse
import time

try:
    import json
except:
    # Python 2.6 support
    import simplejson as json

try:
    import oauth2 as oauth
    has_oauth = True
except:
    has_oauth = False

try:
    import httplib2
    has_httplib2 = True
except:
    has_httplib2 = False

from url import ReaderUrl

def toUnicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

class AuthenticationMethod(object):
    """
    Defines an interface for authentication methods, must have a get method
    make this abstract?
    1. auth on setup
    2. need to have GET method
    """
    def __init__(self):
        self.client = "libgreader" #@todo: is this needed?

    def getParameters(self, extraargs=None):
        #ck is a timecode to help google with caching
        parameters = {'ck':time.time(), 'client':self.client}
        if extraargs:
            parameters.update(extraargs)
        return urllib.urlencode(parameters)

    def postParameters(self, post=None):
        if post is not None:
            post_string = urllib.urlencode(post)
        else:
            post_string = None
        return post_string

class ClientAuthMethod(AuthenticationMethod):
    """
    Auth type which requires a valid Google Reader USERNAME and PASSWORD
    """
    CLIENT_URL = 'https://www.google.com/accounts/ClientLogin'

    def __init__(self, USERNAME, PASSWORD):
        super(ClientAuthMethod, self).__init__()
        self.username   = USERNAME
        self.password   = PASSWORD
        self.auth_token = self._getAuth()
        self.token      = self._getToken()

    def postParameters(self, post=None):
        post.update({'T': self.token})
        return super(ClientAuthMethod, self).postParameters(post)

    def get(self, url, parameters=None):
        """
        Convenience method for requesting to google with proper cookies/params.
        """
        getString = self.getParameters(parameters)
        req = urllib2.Request(url + "?" + getString)
        req.add_header('Authorization','GoogleLogin auth=%s' % self.auth_token)
        r = urllib2.urlopen(req)
        data = r.read()
        r.close()
        return toUnicode(data)

    def post(self, url, postParameters=None, urlParameters=None):
        """
        Convenience method for requesting to google with proper cookies/params.
        """
        if urlParameters:
            url = url + "?" + self.getParameters(urlParameters)
        req = urllib2.Request(url)
        req.add_header('Authorization','GoogleLogin auth=%s' % self.auth_token)
        postString = self.postParameters(postParameters)
        r = urllib2.urlopen(req, data=postString)
        data = r.read()
        r.close()
        return toUnicode(data)

    def _getAuth(self):
        """
        Main step in authorizing with Reader.
        Sends request to Google ClientAuthMethod URL which returns an Auth token.

        Returns Auth token or raises IOError on error.
        """
        parameters = urllib.urlencode({
            'service'     : 'reader',
            'Email'       : self.username,
            'Passwd'      : self.password,
            'accountType' : 'GOOGLE'})
        try:
            conn = urllib2.urlopen(ClientAuthMethod.CLIENT_URL,parameters)
            data = conn.read()
            conn.close()
        except urllib2.HTTPError:
            raise IOError("Error getting the Auth token, have you entered a"
                    "correct USERNAME and PASSWORD?")
        #Strip newline and non token text.
        token_dict = dict(x.split('=') for x in data.split('\n') if x)
        return token_dict["Auth"]

    def _getToken(self):
        """
        Second step in authorizing with Reader.
        Sends authorized request to Reader token URL and returns a token value.

        Returns token or raises IOError on error.
        """
        req = urllib2.Request(ReaderUrl.API_URL + 'token')
        req.add_header('Authorization','GoogleLogin auth=%s' % self.auth_token)
        try:
            conn = urllib2.urlopen(req)
            token = conn.read()
            conn.close()
        except urllib2.HTTPError:
            raise IOError("Error getting the Reader token.")
        return token

class OAuthMethod(AuthenticationMethod):
    """
    Loose wrapper around OAuth2 lib. Kinda awkward.
    """
    GOOGLE_URL        = 'https://www.google.com/accounts/'
    REQUEST_TOKEN_URL = (GOOGLE_URL + 'OAuthGetRequestToken?scope=%s' %
                         ReaderUrl.READER_BASE_URL)
    AUTHORIZE_URL     = GOOGLE_URL + 'OAuthAuthorizeToken'
    ACCESS_TOKEN_URL  = GOOGLE_URL + 'OAuthGetAccessToken'

    def __init__(self, consumer_key, consumer_secret):
        if not has_oauth:
            raise ImportError("No module named oauth2")
        super(OAuthMethod, self).__init__()
        self.oauth_key         = consumer_key
        self.oauth_secret      = consumer_secret
        self.consumer          = oauth.Consumer(self.oauth_key, self.oauth_secret)
        self.authorized_client = None
        self.token_key         = None
        self.token_secret      = None
        self.callback          = None
        self.username          = "OAuth"

    def setCallback(self, callback_url):
        self.callback = '&oauth_callback=%s' % callback_url

    def setRequestToken(self):
        # Step 1: Get a request token. This is a temporary token that is used for
        # having the user authorize an access token and to sign the request to obtain
        # said access token.
        client = oauth.Client(self.consumer)
        if not self.callback:
            resp, content = client.request(OAuthMethod.REQUEST_TOKEN_URL)
        else:
            resp, content = client.request(OAuthMethod.REQUEST_TOKEN_URL + self.callback)
        if int(resp['status']) != 200:
            raise IOError("Error setting Request Token")
        token_dict = dict(urlparse.parse_qsl(content))
        self.token_key = token_dict['oauth_token']
        self.token_secret = token_dict['oauth_token_secret']

    def setAndGetRequestToken(self):
        self.setRequestToken()
        return (self.token_key, self.token_secret)

    def buildAuthUrl(self, token_key=None):
        if not token_key:
            token_key = self.token_key
        #return auth url for user to click or redirect to
        return "%s?oauth_token=%s" % (OAuthMethod.AUTHORIZE_URL, token_key)

    def setAccessToken(self):
        self.setAccessTokenFromCallback(self.token_key, self.token_secret, None)

    def setAccessTokenFromCallback(self, token_key, token_secret, verifier):
        token = oauth.Token(token_key, token_secret)
        #step 2 depends on callback
        if verifier:
            token.set_verifier(verifier)
        client = oauth.Client(self.consumer, token)

        resp, content = client.request(OAuthMethod.ACCESS_TOKEN_URL, "POST")
        if int(resp['status']) != 200:
            raise IOError("Error setting Access Token")
        access_token = dict(urlparse.parse_qsl(content))

        #created Authorized client using access tokens
        self.authFromAccessToken(access_token['oauth_token'],
                                 access_token['oauth_token_secret'])

    def authFromAccessToken(self, oauth_token, oauth_token_secret):
        self.token_key         = oauth_token
        self.token_key_secret  = oauth_token_secret
        token                  = oauth.Token(oauth_token,oauth_token_secret)
        self.authorized_client = oauth.Client(self.consumer, token)

    def getAccessToken(self):
        return (self.token_key, self.token_secret)

    def get(self, url, parameters=None):
        if self.authorized_client:
            getString = self.getParameters(parameters)
            #can't pass in urllib2 Request object here?
            resp, content = self.authorized_client.request(url + "?" + getString)
            return toUnicode(content)
        else:
            raise IOError("No authorized client available.")

    def post(self, url, postParameters=None, urlParameters=None):
        """
        Convenience method for requesting to google with proper cookies/params.
        """
        if self.authorized_client:
            if urlParameters:
                getString = self.getParameters(urlParameters)
                req = urllib2.Request(url + "?" + getString)
            else:
                req = urllib2.Request(url)
            postString = self.postParameters(postParameters)
            resp,content = self.authorized_client.request(req, method="POST", body=postString)
            return toUnicode(content)
        else:
            raise IOError("No authorized client available.")

class OAuth2Method(AuthenticationMethod):
    '''
    Google OAuth2 base method.
    '''
    GOOGLE_URL = 'https://accounts.google.com'
    AUTHORIZATION_URL = GOOGLE_URL + '/o/oauth2/auth'
    ACCESS_TOKEN_URL = GOOGLE_URL + '/o/oauth2/token'
    SCOPE = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.google.com/reader/api/',
    ]

    def __init__(self, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN):
        super(OAuth2Method, self).__init__()
        self.client_id         = CLIENT_ID
        self.client_secret     = CLIENT_SECRET
        self.authorized_client = None
        self.code              = None
        self.access_token      = None ## need in all request
        self.action_token      = None ## need in post @note: http://code.google.com/p/google-reader-api/wiki/ActionToken
        self.redirect_uri      = None
        self.refresh_token     = REFRESH_TOKEN
        self.username          = "OAuth2"
        self.expires_access    = None ## access_token的失效日期时间（长度为60min）
        self.expires_action    = None ## action_token的失效日期时间（长度为30min）

    def setRedirectUri(self, redirect_uri):
        self.redirect_uri = redirect_uri

    def buildAuthUrl(self):
        args = {
            'CLIENT_ID': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.SCOPE),
            'response_type': 'code',
        }
        return self.AUTHORIZATION_URL + '?' + urllib.urlencode(args)

    def setActionToken(self):
        '''
        Get action to prevent XSRF attacks
        http://code.google.com/p/google-reader-api/wiki/ActionToken

        ## ActionToken, The token is valid for 30 minutes.
        '''
        self.action_token = self.get(ReaderUrl.ACTION_TOKEN_URL)
        current = int(time.time())
        self.expires_action = current + 30*60

    def setAccessToken(self):
        params = {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.code,                   # server response code
            'CLIENT_ID': self.client_id,
            'CLIENT_SECRET': self.client_secret,
            'redirect_uri': self.redirect_uri
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        request = urllib2.Request(
            self.ACCESS_TOKEN_URL,
            data=urllib.urlencode(params),
            headers=headers
            )

        try:
            response = json.loads(urllib2.urlopen(request).read())
        except urllib2.HTTPError, e:
            raise IOError('Error getting Access Token')

        if 'access_token' not in response:
            raise IOError('Error getting Access Token')
        else:
            self.authFromAccessToken(response['access_token'],response['REFRESH_TOKEN'])
        
    '''
    @author: plex
    '''
    def refreshAccessToken(self):
        params = {
            'grant_type': 'refresh_token',  # request REFRESH_TOKEN
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        request = urllib2.Request(
            self.ACCESS_TOKEN_URL,
            data=urllib.urlencode(params),
            headers=headers
            )

        try:
            response = json.loads(urllib2.urlopen(request).read())
        except :
            print 'WARN:'
            print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) +\
             '\t获取授权失败，可能是网络timeout，休息十分钟后再次请求'
            time.sleep(600)
            self.refreshAccessToken()
            return 
        
        if 'access_token' not in response:
            raise IOError('Error getting Access Token')
        else:
            self.authFromAccessToken(response['access_token'])

    def is_access_token_expires(self):
        if not self.access_token:
            print 'ERROR in is_access_token_expires, there is no access_token: ', self.access_token
        return not self.access_token or time.time() >= self.expires_access
    
    def is_action_token_expires(self):
        return not self.action_token or time.time() >= self.expires_action
    
    def authFromAccessToken(self, access_token, refresh_token=None, expires_in=60*60):
        self.access_token = access_token
        if(refresh_token is not None):
            self.refresh_token = refresh_token
        current = int(time.time())
        self.expires_access = current + expires_in

    def get(self, url, parameters=None):
        """
        Convenience method for requesting to google with proper cookies/params.
        """
        if self.is_access_token_expires():
            self.refreshAccessToken()
        
        if not self.access_token:
            raise IOError("No authorized client available.")
        if parameters is None:
            parameters = {}
        parameters.update({'access_token': self.access_token, 'alt': 'json'})
        request = urllib2.Request(url + '?' + self.getParameters(parameters))
        try:
            response = urllib2.urlopen(request).read()
            return toUnicode(response)
        except (ValueError, KeyError, IOError) as e:
            return None

    def post(self, url, postParameters=None, urlParameters=None):
        if self.is_access_token_expires():
            self.refreshAccessToken()
        if self.is_action_token_expires():
            ## action token only needed in post request
            self.setActionToken()
        """
        Convenience method for requesting to google with proper cookies/params.
        """
        if not self.access_token:
            raise IOError("No authorized client available.")
        if not self.action_token:
            raise IOError("Need to generate action token.")
        if urlParameters is None:
            urlParameters = {}
        headers = {'Authorization': 'Bearer ' + self.access_token}
        postParameters.update({'T':self.action_token})
        postString = self.postParameters(postParameters)
        request = urllib2.Request(url + '?' + self.getParameters(urlParameters), data=postString, headers=headers)
        try:
            response = urllib2.urlopen(request)
            return toUnicode(response.read())
        except (ValueError, KeyError, IOError) as e:
            return None

class GAPDecoratorAuthMethod(AuthenticationMethod):
    """
    An adapter to work with Google API for Python OAuth2 wrapper.
    Especially useful when deploying to Google AppEngine.
    """
    def __init__(self, credentials):
        """
        Initialize auth method with existing credentials.
        Args:
            credentials: OAuth2 credentials obtained via GAP OAuth2 library.
        """
        if not has_httplib2:
            raise ImportError("No module named httplib2")
        super(GAPDecoratorAuthMethod, self).__init__()
        self._http = None
        self._credentials = credentials

    def _setupHttp(self):
        """
        Setup an HTTP session authorized by OAuth2.
        """
        if self._http == None:
            http = httplib2.Http()
            self._http = self._credentials.authorize(http)

    def get(self, url, parameters=None):
        """
        Implement libgreader's interface for authenticated GET request
        """
        if self._http == None:
            self._setupHttp()
        uri = url + "?" + self.getParameters(parameters)
        response, content = self._http.request(uri, "GET")
        return content
    def post(self, url, postParameters=None, urlParameters=None):
        """
        Implement libgreader's interface for authenticated POST request
        """
        if self._http == None:
            self._setupHttp()
        uri = url + "?" + self.getParameters(urlParameters)
        body = self.postParameters(postParameters)
        response, content = self._http.request(uri, "POST", body=body)

#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 12, 2012

@author: plex
'''
## 为什么去掉这个配置，调试正确，但是运行就报错？？？
## 但是，留着这个配置，运行ｄｊａｎｇｏ就会报错。。。
#from django.conf import settings
#settings.configure(
#    DATABASE_ENGINE = 'django.db.backends.mysql',
#    DATABASE_NAME = 'newstracker',
#    DATABASE_USER = 'root',
#    DATABASE_PASSWORD = 'wangfengwei',
#    DATABASE_HOST = 'localhost',
#    TIME_ZONE = 'America/New_York',
#)

from django.contrib.auth.models import User

#import sys
#sys.path.append('/home/plex/wksp/django/newstracker')
# 动态绑定,使用了固定地址,后面可以直接from newstracker.newstrack import models
from newstracker.newstrack import models
from newstracker.account import models as account_models

Account = account_models.Account
Useroauth2 = account_models.Useroauth2

Weibo = models.Weibo
Topic = models.Topic
News = models.News
WeiboConfig = models.WeiboConfig
GReaderConfig = models.GReaderConfig

from datetime import datetime

_DEBUG = True

def get_or_create_weibo(weiboJson):
    '''
    通过微博（status）的json形式构建weibo对象，并保存到数据库
    '''
    if _DEBUG:
        print weiboJson
    nweibo, created = Weibo.objects.get_or_create(weibo_id = weiboJson['id'])
    if created:
        nweibo.created_at = datetime.strptime(weiboJson['created_at'], "%a %b %d %H:%M:%S +0800 %Y")
        nweibo.text = weiboJson['text']
        if weiboJson['in_reply_to_status_id'] != '':
            nweibo.in_reply_to_status_id = weiboJson['in_reply_to_status_id']
        if weiboJson['in_reply_to_user_id'] != '':
            nweibo.in_reply_to_user_id = weiboJson['in_reply_to_user_id']
        if weiboJson['in_reply_to_screen_name'] != '':
            nweibo.in_reply_to_screen_name = weiboJson['in_reply_to_screen_name']
        if weiboJson['reposts_count'] != '':
            nweibo.reposts_count = weiboJson['reposts_count']
        if weiboJson['comments_count'] != '':
            nweibo.comments_count = weiboJson['comments_count']
        ## TODO: test
        if weiboJson['user'] != '':
            nweibo.user = get_or_create_account_from_weibo(weiboJson['user'])
                
        nweibo.save()
        
    return nweibo

def get_or_create_account_from_weibo(weiboUserJson):
    '''
    通过微博用户（user）的json形式构建weibo用户对象，并保存到数据库
    如果要构建微博用户，用户名使用微博昵称，密码是用户微博id，邮箱是默认的邮箱
    '''
    
    try:
        account = Account.objects.get(weiboId = weiboUserJson['id'])
    except Account.DoesNotExist:
        try:
            user = User.objects.get(username = weiboUserJson['name'])
        except:
            user = User.objects.create_user(username = weiboUserJson['name'],
                                            email = weiboUserJson['name'] + '-' + str(weiboUserJson['id']) + '@fakeemail.com',
                                            password = weiboUserJson['id'])
        account, created = Account.objects.get_or_create(user = user)
        if created:
            account.weiboId = weiboUserJson['id']
            if weiboUserJson['city'] != '':
                account.weiboCity = weiboUserJson['city']
            if weiboUserJson['gender'] != '':
                account.weiboGender = weiboUserJson['gender']
            if weiboUserJson['followers_count'] != '':
                account.weiboFollowersCount = weiboUserJson['followers_count']
            if weiboUserJson['friends_count'] != '':
                account.weiboFriendsCount = weiboUserJson['friends_count']
            if weiboUserJson['statuses_count'] != '':
                account.weiboStatusesCount = weiboUserJson['statuses_count']
            if weiboUserJson['following'] != '':
                account.weiboFollowing = weiboUserJson['following']
            if weiboUserJson['follow_me'] != '':
                account.weiboFollowMe = weiboUserJson['follow_me']
            if weiboUserJson['verified'] != '':
                account.verified = weiboUserJson['verified']
            
            account.save()
    return account

def get_or_update_weibo_auth_info(u_id, access_token = None, expires_in = None):
    '''得到或保存更新access_token和expires_in信息
    如果access_token和expire_in都不是None，则保存更新　返回[None, None]
    否则从数据库中取u_id对应的access_token和expire_in，并返回[access_token, expire_in]
    '''
    if access_token is None or expires_in is None:
        try:
            _oauth2info = Useroauth2.objects.get(server='weibo', u_id=u_id)
            access_token = _oauth2info.access_token
            expires_in = _oauth2info.expires_in
        except:
            print 'access information for weibo user:'+str(u_id)+' not found'
    return [access_token, expires_in]

if __name__ == '__main__':
    #test
#    topic = Topic.objects.create(title = 't', rss = 'r')
    topics = Topic.objects.all()
    print topics
        
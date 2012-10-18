#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 16, 2012

@author: plex
'''

from newstracker.account.models import Account
from django.contrib.auth.models import User

import djangodb


from datetime import datetime

_DEBUG = True

def get_or_create_weibo(weiboJson):
    '''
    通过微博（status）的json形式构建weibo对象，并保存到数据库
    '''
    if _DEBUG:
        print weiboJson
    nweibo, created = djangodb.Weibo.objects.get_or_create(weibo_id = weiboJson['id'])
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

if __name__ == '__main__':
    pass
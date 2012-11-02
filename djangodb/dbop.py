#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on Oct 24, 2012

@author: plex
'''

from django.contrib.auth.models import User

from newstracker.newstrack.models import Weibo, Topic, News, Task
from newstracker.account.models import Account, Useroauth2

from datetime import datetime

_DEBUG = True

def get_or_create_weibo(weiboJson):
    '''
    通过微博（status）的json形式构建weibo对象，并保存到数据库
    '''
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
            ## TODO: bug 没有考虑用户该微博昵称的情况，并认为user和account是一一对应的
            user = User.objects.get(username = weiboUserJson['name'])
        except:
            user = User.objects.create_user(username = weiboUserJson['name'],
                                            email = str(weiboUserJson['id']) + '@fakeemail.com',
                                            password = str(weiboUserJson['id']))
        account, created = Account.objects.get_or_create(user = user)
        if created:
            account.weiboId = weiboUserJson['id']
            if weiboUserJson['name'] != '':
                account.weiboName = weiboUserJson['name']
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
    '''
    _oauth2info, created = Useroauth2.objects.get_or_create(server='weibo', u_id = u_id)

    if access_token is None or expires_in is None:
        ## 认为是获取信息
        access_token = _oauth2info.access_token
        expires_in = _oauth2info.expires_in
    else:
        ##　认为是更新信息
        _oauth2info.access_token = access_token
        _oauth2info.expires_in = expires_in
        _oauth2info.save()
    return [access_token, expires_in]

def get_last_mention_id():
    '''
    得到最近获取的一条＠微博，由于Weibo模型中已经定义了顺序，所以。。。
    '''
    try:
        return Weibo.objects.all()[0].weibo_id
    except:
        return 0

def add_remind_user_task(topic):
    task, created = Task.objects.get_or_create(type = 'remind', topic = topic)
    if not created:
        task.status += 1
        task.save()

def add_subscribe_topic_task(topic):
    task, created = Task.objects.get_or_create(type = 'subscribe', topic = topic)
    if not created:
        task.status += 1
        task.save()

def get_tasks(type, count=1):
    tasks = Task.objects.filter(type=type)[:count]
    return list(tasks)
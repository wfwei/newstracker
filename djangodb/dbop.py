# !/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on Oct 24, 2012

@author: plex
'''

from django.contrib.auth.models import User
from newstracker.newstrack.models import *  # in other module, it is used!!!
from newstracker.account.models import Account, Useroauth2
from datetime import datetime


import logging
# setup logging
try:
    logger = logging.getLogger(u'dbop-logger')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(u'../logs/dbop.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with warn log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    # create logger output formater
    formatter = logging.Formatter(u'%(asctime)s %(name)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
except:
    logger = logging.getLogger()

def get_or_create_weibo(weiboJson):
    '''
    通过微博（status）的json形式构建weibo对象，并保存到数据库
    '''
    logger.info(u'in get_or_create_weibo(weiboJson)\nweiboJson:%s' % weiboJson)
    nweibo, created = Weibo.objects.get_or_create(weibo_id=weiboJson[u'id'])
    logger.info(u'created:%s' % created)
    if created:
        nweibo.created_at = datetime.strptime(weiboJson[u'created_at'], "%a %b %d %H:%M:%S +0800 %Y")
        nweibo.text = weiboJson[u'text']
        if weiboJson[u'in_reply_to_status_id'] != u'':
            nweibo.in_reply_to_status_id = weiboJson[u'in_reply_to_status_id']
        if weiboJson[u'in_reply_to_user_id'] != u'':
            nweibo.in_reply_to_user_id = weiboJson[u'in_reply_to_user_id']
        if weiboJson[u'in_reply_to_screen_name'] != u'':
            nweibo.in_reply_to_screen_name = weiboJson[u'in_reply_to_screen_name']
        if weiboJson[u'reposts_count'] != u'':
            nweibo.reposts_count = weiboJson[u'reposts_count']
        if weiboJson[u'comments_count'] != u'':
            nweibo.comments_count = weiboJson[u'comments_count']
        if weiboJson[u'user'] != u'':
            nweibo.user = get_or_create_account_from_weibo(weiboJson[u'user'])

        nweibo.save()
    return nweibo

def get_or_create_account_from_weibo(weiboUserJson):
    '''
    通过微博用户（user）的json形式构建weibo用户对象，并保存到数据库
    如果要构建微博用户，用户名使用微博昵称，密码是用户微博id，邮箱是默认的邮箱
    '''
    logger.info(u'in get_or_create_account_from_weibo(weiboUserJson)\weiboUserJson:%s' % weiboUserJson)
    try:
        account = Account.objects.get(weiboId=weiboUserJson[u'id'])
        logger.info(u'account already exists:%s' % account)
    except Account.DoesNotExist:
        try:
            # TODO: bug 没有考虑用户该微博昵称的情况，并认为user和account是一一对应的
            user = User.objects.get(username=weiboUserJson[u'name'])
        except:
            user = User.objects.create_user(username=weiboUserJson[u'name'],
                                            email=str(weiboUserJson[u'id']) + u'@fakeemail.com',
                                            password=weiboUserJson[u'id'])
        account, created = Account.objects.get_or_create(user=user)
        logger.info(u'created:%s' % created)
        if created:
            account.weiboId = weiboUserJson[u'id']
            if weiboUserJson[u'name'] != u'':
                account.weiboName = weiboUserJson[u'name']
            if weiboUserJson[u'city'] != u'':
                account.weiboCity = weiboUserJson[u'city']
            if weiboUserJson[u'gender'] != u'':
                account.weiboGender = weiboUserJson[u'gender']
            if weiboUserJson[u'followers_count'] != u'':
                account.weiboFollowersCount = weiboUserJson[u'followers_count']
            if weiboUserJson[u'friends_count'] != u'':
                account.weiboFriendsCount = weiboUserJson[u'friends_count']
            if weiboUserJson[u'statuses_count'] != u'':
                account.weiboStatusesCount = weiboUserJson[u'statuses_count']
            if weiboUserJson[u'following'] != u'':
                account.weiboFollowing = weiboUserJson[u'following']
            if weiboUserJson[u'follow_me'] != u'':
                account.weiboFollowMe = weiboUserJson[u'follow_me']
            if weiboUserJson[u'verified'] != u'':
                account.verified = weiboUserJson[u'verified']

            account.save()
    return account


def get_weibo_auth_info(u_id):
    '''
    得到access_token和expires_in信息
    成功返回对应的oauth，否则返回None
    '''
    _oauth = Useroauth2.objects.filter(server=u'weibo', u_id=u_id)
    if _oauth:
        return [_oauth[0].access_token, _oauth[0].expires_in]
    else:
        return None

def create_or_update_weibo_auth(u_id, access_token, expires_in):
    '''
    更新u_id对应oauth的access_token和expires_in信息
    更新成功，返回auth，否则，返回None
    '''

    if u_id and access_token and expires_in:
        _oauth2info, created = Useroauth2.objects.get_or_create(server=u'weibo', u_id=u_id)
        _oauth2info.access_token = access_token
        _oauth2info.expires_in = expires_in
        _oauth2info.save()
        logger.info(u'create or update weibo auth:%s' % _oauth2info)
        return _oauth2info
    else:
        logger.warn(u'not enough parameters：[u_id:%d, access_token:%s, expires_in:%s]' % \
                    (u_id, access_token, expires_in))
        return None

def get_google_auth_info(u_id):
    '''
    得到access_token，refresh_token和expires_in(access_expires)信息
    成功返回对应的oauth，否则返回None
    '''
    _oauth = Useroauth2.objects.filter(server=u'google', u_id=u_id)
    if _oauth:
        return [_oauth[0].access_token, _oauth[0].refresh_token, _oauth[0].expires_in]
    else:
        return None

def create_or_update_google_auth(u_id, access_token, refresh_token, expires_in):
    '''
    更新u_id对应oauth的access_token, refresh_token和expires_in信息
    更新成功，返回auth，否则，返回None
    '''

    if u_id and access_token and refresh_token and expires_in:
        _oauth2info, created = Useroauth2.objects.get_or_create(server=u'google', u_id=u_id)
        _oauth2info.access_token = access_token
        _oauth2info.expires_in = expires_in
        _oauth2info.save()
        logger.info(u'create or update google auth:%s' % _oauth2info)
        return _oauth2info
    else:
        logger.warn(u'缺少参数：[u_id:%d, access_token:%d, refresh_token:%s expires_in:%s]' % \
                    (u_id, access_token, refresh_token, str(expires_in)))
        return None

def rm_weibo_auth(u_id):
    '''得到或保存更新access_token和expires_in信息
    TODO:test
    '''
    _oauth2info = Useroauth2.objects.filter(u_id=u_id)

    if _oauth2info:
        _oauth2info.delete()
        logger.info(u'succeed to delete auth:%s' % str(u_id))
    else:
        logger.warn(u'failed to delete auth:%s' % str(u_id))


def get_last_mention_id():
    '''
    得到最近获取的一条＠微博，由于Weibo模型中已经定义了顺序，所以。。。
    '''
    _lastMentionId = 0
    try:
        _lastMentionId = Weibo.objects.all()[0].weibo_id
        logger.info(u'get_last_mention_id:%d' % _lastMentionId)
    except:
        logger.error(u'error in get_last_mention_id()')

    return _lastMentionId

def add_task(topic, type):
    task, created = Task.objects.get_or_create(type=type, topic=topic)

    if not created:
        task.status += 1
        task.save()
        logger.info(u'update task:%s' % task)
    else:
        logger.info(u'create task:%s' % task)

def get_tasks(type, count=1, excludeDead=True):
    tasks = Task.objects.exclude(status=0).filter(type=type)[:count]
    logger.info(u'get_tasks:%s' % tasks)
    return tasks

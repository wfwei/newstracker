# !/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth import models as auth_models

import time
import datetime

"""attribute in User
username(*), first_name, last_name, email, password, is_staff, is_active,
is_superuser, last_login, date_joined
"""

class Account(models.Model):

    user = models.ForeignKey(auth_models.User, unique=True)
    weiboId = models.BigIntegerField(default=0)
    weiboName = models.CharField(max_length=100)
    weiboCity = models.IntegerField(default=0)
    weiboGender = models.CharField(max_length=10)
    weiboFollowersCount = models.IntegerField(default=0)
    weiboFriendsCount = models.IntegerField(default=0)
    weiboStatusesCount = models.IntegerField(default=0)
    weiboFollowing = models.BooleanField(default=False)
    weiboFollowMe = models.BooleanField(default=False)
    weiboVerified = models.BooleanField(default=False)

    oauth = models.ForeignKey("Useroauth2", blank=True)
    # TODO: change database

    # 　是否允许使用其帐号提醒他人
    allow_remind_others = models.BooleanField(default=True)

    # 　每天的提醒上限
    remind_daily_limit = models.IntegerField(default=1)

    # 　提醒的历史记录，格式是"date1 date2 date3"，但制保留当天的记录
    remind_history = models.TextField(default='')

    # 是否允许转发微博来提醒自己
    repost_remind = models.BooleanField(default=True)

    # 是否允许评论微博来提醒自己
    comment_remind = models.BooleanField(default=True)

    # 是否允许＠微博来提醒自己
    at_remind = models.BooleanField(default=True)

    def __unicode__(self):
        if self.weiboName is None or self.weiboId == 0:
            wname = '未绑定微博帐号'
        else:
            wname = self.weiboName
        return '[account:' + self.user.username + ', weibo:' + wname + ']'

    def to_remind(self):
        '''
        今天要不要提醒该用户
        '''
        new_remind_history = ''
        count = 0
        for dt in self.remind_history.split(' '):
            if dt == datetime.date.today().strftime('%Y-%m-%d'):
                count += 1
                new_remind_history += dt + ' '
        # 更新提醒历史，只包含今天
        self.remind_history = new_remind_history
        self.save()
        # 返回今天是否还要提醒用户
        return self.remind_daily_limit < count

    def add_remind(self):
        self.remind_history += datetime.date.today().strftime('%Y-%m-%d') + ' '
        self.save()

    def has_oauth(self):
        '''
        用户已经授权且授权没有过期，返回True
        否则，返回False
        '''
        if self.oauth:
            return self.oauth.is_expired()
        else:
            return False

    @staticmethod
    def get_account(user):
        return Account.objects.get(user=user)

class Useroauth2(models.Model):
    '''
    APP_KEY,    APP_SECRET,    CALLBACK_URL 这些都直接在程序肿配置
    这里只是保存用户授权
    '''
    # weibo or google
    server = models.CharField(max_length=100, db_index=True)
    u_id = models.BigIntegerField(db_index=True)
    access_token = models.CharField(max_length=100)
    access_secret = models.CharField(max_length=100)
    refresh_token = models.CharField(max_length=100)
    expires_in = models.CharField(max_length=100)

    def is_expired(self):
        return float(self.expires_in) < time.time()

    def __unicode__(self):
        _str = self.u_id + '@' + self.server + ':' + str(self.access_token)
        if self.is_expired():
            _str += ' Expired!'
        return _str


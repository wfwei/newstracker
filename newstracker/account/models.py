# !/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth import models as auth_models

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
    
    def __unicode__(self):
        if self.weiboName is None or self.weiboId == 0:
            wname = '未绑定微博帐号'
        else:
            wname = self.weiboName
        return '[account:' + self.user.username + ', weibo:' + wname + ']'

    @staticmethod
    def get_account(user):
        return Account.objects.get(user=user)

class Useroauth2(models.Model):
    '''
    APP_KEY,    APP_SECRET,    CALLBACK_URL 这些都直接在程序肿配置
    这里只是保存用户授权
    
    not in use
    目前还没有用这个，感觉保存两个小时的用户授权没有价值，目前只是将用户微博帐号和本地帐号关联起来
    '''
    # # weibo or google
    server = models.CharField(max_length=100, db_index=True)
    u_id = models.BigIntegerField(db_index=True)
    access_token = models.CharField(max_length=100)
    access_secret = models.CharField(max_length=100)
    refresh_token = models.CharField(max_length=100)
    expires_in = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.u_id + '@' + self.server + ':' + str(self.access_token)
    

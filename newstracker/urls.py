#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'newstracker.newstrack.views.topic_list', name='topic_list'),
     ## remove below
     url(r'^topic_list/(?P<account_id>\d+)$', 'newstracker.newstrack.views.topic_list', name='topic_list'),
     url(r'^topic_list/$', 'newstracker.newstrack.views.topic_list', name='topic_list'),
     url(r'^topic_view/(?P<topic_id>\d+)$', 'newstracker.newstrack.views.topic_view', name='topic_view'),
     url(r'^news_timeline/(?P<topic_id>\d+)$', 'newstracker.newstrack.views.news_timeline', name='news_timeline'),
     
     ## （取消）关注话题
     url(r'^follow_topic/$', 'newstracker.newstrack.views.follow_topic', name='follow_topic'),
     url(r'^unfollow_topic/$', 'newstracker.newstrack.views.unfollow_topic', name='unfollow_topic'),
     
     ## 註冊和登錄部分
     url(r'login/$', 'newstracker.account.views.login', name='login'),
     url(r'weiboLogin/$', 'newstracker.account.views.weiboLogin', name='weibologin'),
     url(r'logout/$', 'newstracker.account.views.logout', name='logout'),
     url(r'userinfo/$', 'newstracker.account.views.userinfo', name='userinfo'),
     url(r'register/$', 'newstracker.account.views.register', name='register'),
     
     url(r'weibo_callback/$', 'newstracker.account.views.weibo_callback', name='weibo_callback'),
     url(r'weibo_callback_rm/$', 'newstracker.account.views.weibo_callback_rm', name='weibo_callback_rm'),
     
#     url(r'^newstracker/', include('newstracker.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
#     url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
     url(r'^admin/', include(admin.site.urls)),
)

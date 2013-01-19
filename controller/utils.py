# !/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Dec 26, 2012

@author: plex
'''
import time


def reqInterval(interval=20):
    time.sleep(interval)

class Conf():
    # 网站地址
    site_url = u'http://track.youlil.com'

    # 时间线url，需要参数
    timeline_url = u'http://track.youlil.com/news_timeline/%d'

    # 狗狗追踪应用的key和secret
    weibo_app_key = '3233912973'
    weibo_app_secret = '289ae4ee3da84d8c4c359312dc2ca17d'
    # 微薄授权回调地址
    callback_url = u'http://track.youlil.com/weibo_callback/'
    # 取消微薄授权回调地址
    callback_rm_url = u'http://track.youlil.com/weibo_callback_rm/'

    @classmethod
    def get_timeline_url(cls, topicId):
        return cls.timeline_url % topicId


if __name__ == '__main__':
    print Conf.callback_rm_url
    print Conf.callback_url
    print Conf.site_url
    print Conf.get_timeline_url(2)

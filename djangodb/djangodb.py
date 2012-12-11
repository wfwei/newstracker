# !/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 12, 2012

@author: plex
'''

from django.conf import settings
settings.configure(
    DATABASE_ENGINE='django.db.backends.mysql',
    DATABASE_NAME='newstracker',
    DATABASE_USER='wangfengwei',
    DATABASE_PASSWORD='wangfengwei',
    DATABASE_HOST='localhost',
)
from dbop import *


if __name__ == '__main__':
    from newstracker.newstrack.models import Weibo, Topic, News, Task
    nnews, created = News.objects.get_or_create(title='街拍合肥三里庵官亭路美女穿搭欧美风御姐PK日系小萝莉 - 万家热线')
    print nnews
    print created
    try:
        nnews.save()
    except:
        raise
    print 'ok'











    weiboJson = {'allow_all_act_msg': False,
 'allow_all_comment': True,
 'avatar_large': u'http://tp3.sinaimg.cn/2638714490/180/5620042495/0',
 'bi_followers_count': 35,
 'city': u'1',
 'created_at': u'Wed Dec 28 14:04:13 +0800 2011',
 'description': u'\u6211\u559c\u6b22\u7b11\uff0c\u559c\u6b22\u548c\u4eba\u5206\u4eab\u5feb\u4e50~\u6211\u76f8\u4fe1\u5947\u8ff9\uff0c\u76f8\u4fe1\u6211\u4eec\u4f1a\u4e2d\u5956~\u6211\u5c31\u662f\u5e78\u8fd0\u5973\u795e\uff0c\u5e78\u8fd0\u5973\u795e\u5c31\u662f\u6211~\u5982\u679c\u4f60\u613f\u610f\uff0c\u5173\u6ce8\u6211\u5427\uff0c\u76f8\u4fe1\u5e78\u8fd0\u4f1a\u968f\u4e4b\u800c\u6765^ ^',
 'domain': u'',
 'favourites_count': 0,
 'follow_me': True,
 'followers_count': 4328,
 'following': True,
 'friends_count': 250,
 'gender': u'f',
 'geo_enabled': True,
 'id': 2638714490,
 'idstr': u'2638714490',
 'lang': u'zh-cn',
 'location': u'\u6d59\u6c5f \u676d\u5dde',
 'name': u'\u5e78\u8fd0\u5973\u795e\u5c31\u662f\u6211',
 'online_status': 1,
 'profile_image_url': u'http://tp3.sinaimg.cn/2638714490/50/5620042495/0',
 'profile_url': u'u/2638714490',
 'province': u'33',
 'remark': u'',
 'screen_name': u'\u5e78\u8fd0\u5973\u795e\u5c31\u662f\u6211',
 'star': 0,
 'status': {'attitudes_count': 0,
            'comments_count': 0,
            'created_at': u'Wed Mar 07 15:26:49 +0800 2012',
            'favorited': False,
            'geo': None,
            'id': 3420965553614099,
            'idstr': u'3420965553614099',
            'in_reply_to_screen_name': u'',
            'in_reply_to_status_id': u'',
            'in_reply_to_user_id': u'',
            'mid': u'3420965553614099',
            'mlevel': 0,
            'reposts_count': 0,
            'retweeted_status': {'annotations': [{'source': {'appid': u'38',
                                                             'id': u'372349',
                                                             'name': u'\u3010\u660e\u73e0\u4fa0\u3011\u706b\u7206\u516c\u6d4b\uff01\u6625\u5149\u4e09\u6708\u6709\u5956\u8f6c\u53d1\uff01\u5c0a\u7684\u6728\u6709iPhone 4\uff01',
                                                             'title': u'\u3010\u660e\u73e0\u4fa0\u3011\u706b\u7206\u516c\u6d4b...',
                                                             'url': u'http://event.weibo.com/372349'}}],
                                 'attitudes_count': 0,
                                 'bmiddle_pic': u'http://ww4.sinaimg.cn/bmiddle/918f33b7jw1dqr1cluhnnj.jpg',
                                 'comments_count': 0,
                                 'created_at': u'Wed Mar 07 10:46:59 +0800 2012',
                                 'favorited': False,
                                 'geo': None,
                                 'id': 3420895131885233,
                                 'idstr': u'3420895131885233',
                                 'in_reply_to_screen_name': u'',
                                 'in_reply_to_status_id': u'',
                                 'in_reply_to_user_id': u'',
                                 'mid': u'3420895131885233',
                                 'mlevel': 0,
                                 'original_pic': u'http://ww4.sinaimg.cn/large/918f33b7jw1dqr1cluhnnj.jpg',
                                 'reposts_count': 0,
                                 'source': u'<a href="" rel="nofollow"></a>',
                                 'text': u'\u638c\u4e0a\u660e\u73e0\u9996\u6b3e\u5199\u5b9e\u98ce\u683c\u6b66\u4fa0\u5de8\u4f5c#\u660e\u73e0\u4fa0\u516c\u6d4b#\u5566!\u878d\u5408\u591a\u79cd\u7eaf\u6b63\u6b66\u4fa0\u5143\u7d20,\u5e26\u4f60\u91cd\u56de\u4e5d\u5927\u95e8\u6d3e\u9519\u7efc\u7ea0\u845b\u7684\u6069\u6028\u5e74\u4ee3,\u52a0\u5165\u4fa0\u7684\u4e16\u754c,\u6f14\u7ece\u4e00\u51fa\u6069\u6028\u4ea4\u7ec7\u7684\u6c5f\u6e56\u60c5\u7f18,\u8ffd\u9010\u4e00\u6bb5\u5200\u5149\u5251\u5f71\u7684\u6b66\u4fa0\u8ff7\u68a6!\u53ea\u8981\u6210\u4e3a@\u660e\u73e0\u4fa0 \u7c89\u4e1d+\u6210\u529f\u8f6c\u53d1\u5fae\u535a+@ 3\u4f4d\u597d\u53cb\u5373\u53ef\u53c2\u4e0e\u62bd\u5956!\u5c0a\u7684\u6728\u6709iPhone 4! http://t.cn/zOccSqw',
                                 'thumbnail_pic': u'http://ww4.sinaimg.cn/thumbnail/918f33b7jw1dqr1cluhnnj.jpg',
                                 'truncated': False,
                                 'user': {'allow_all_act_msg': False,
                                          'allow_all_comment': True,
                                          'avatar_large': u'http://tp4.sinaimg.cn/2442081207/180/5638858207/1',
                                          'bi_followers_count': 10,
                                          'city': u'5',
                                          'created_at': u'Thu Nov 03 10:48:58 +0800 2011',
                                          'description': u'\u5168\u65b0\u7384\u5e7b\u6b66\u4fa0\u624b\u673a\u7f51\u6e38,\u552f\u7f8e\u98ce\u666f,\u767e\u53d8\u65f6\u88c5,\u534e\u4e3d\u5149\u6548,\u8d85\u5927\u5730\u56fe,\u95e8\u6d3e\u65e0\u8d23\u8f6c\u6362,\u9669\u6076\u6c5f\u6e56\u4efb\u900d\u9065.wap\u5b98\u7f51:mzx.pipgame.cn,web\u5b98\u7f51:www.pipgame.com/mzx/',
                                          'domain': u'pipmzx',
                                          'favourites_count': 0,
                                          'follow_me': False,
                                          'followers_count': 1404,
                                          'following': False,
                                          'friends_count': 25,
                                          'gender': u'm',
                                          'geo_enabled': True,
                                          'id': 2442081207,
                                          'idstr': u'2442081207',
                                          'lang': u'zh-cn',
                                          'location': u'\u5317\u4eac \u671d\u9633\u533a',
                                          'name': u'\u660e\u73e0\u4fa0',
                                          'online_status': 0,
                                          'profile_image_url': u'http://tp4.sinaimg.cn/2442081207/50/5638858207/1',
                                          'profile_url': u'pipmzx',
                                          'province': u'11',
                                          'screen_name': u'\u660e\u73e0\u4fa0',
                                          'star': 0,
                                          'statuses_count': 309,
                                          'url': u'http://www.pipgame.com/mzx/',
                                          'verified': True,
                                          'verified_reason': u'\u300a\u660e\u73e0\u4fa0\u300b\u5b98\u65b9\u5fae\u535a',
                                          'verified_type': 2,
                                          'weihao': u''},
                                 'visible': {'list_id': 0, 'type': 0}},
            'source': u'<a href="" rel="nofollow">\u672a\u901a\u8fc7\u5ba1\u6838\u5e94\u7528</a>',
            'text': u'\u6bcf\u65e5\u4e00\u8f6c\uff0c\u795d\u81ea\u5df1\u548c\u4f60\u4eec\u597d\u8fd0\u5427 ^ ^  @\u54c8\u5c14\u6ee8\u963f\u8428\u5e1d18\u516c\u9986--\u6cd5\u76db @Rich3 @Jerry_cyj',
            'truncated': False,
            'visible': {'list_id': 0, 'type': 0}},
 'statuses_count': 1833,
 'url': u'',
 'verified': False,
 'verified_reason': u'',
 'verified_type': 200,
 'weihao': u''}
#    get_or_create_account_from_weibo(weiboJson)

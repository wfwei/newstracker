#coding=utf-8
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import simplejson

from newstracker.newstrack.models import Topic, News
from newstracker.account.models import Account

from libweibo.weiboAPI import weiboAPI

import itertools
import re

_DEBUG = True
_mimetype =  'application/javascript, charset=utf8'

'''
TODO:
1. 直接传输topic对象太大了，后面要什么传什么
3. 模板改用bootstrap
'''
def home(request):
    template_var = {}
    my_topics = []
    exclude_set = []
    if request.user.is_authenticated():
        current_account = User.objects.get(username = request.user.username).account_set.all()[0]
        my_topics = current_account.topic_set.all()
        template_var['current_account'] = current_account
        template_var['my_topics'] = my_topics
        exclude_set.append(current_account)
    else:
        ## 用户weibo登录的认证链接
        template_var['authorize_url'] = weiboAPI().getAuthorizeUrl()

    ## 得到数据库其他的比较热门的10个话题
    other_topics = Topic.objects.exclude(watcher__in=exclude_set).annotate(watcher_count=Count('watcher')).order_by( '-watcher_count' )[:10]
    template_var['other_topics'] = other_topics

    for topic in itertools.chain(my_topics, other_topics):
        if topic.news_set.count() > 0:
            _news = topic.news_set.all()[0]
            topic.recent_news_title = _news.title
            topic.recent_news_link = _news.link
            topic.timeline_ready = True
        else:
            topic.recent_news_title= '还没来得及更新＝＝!'
            topic.recent_news_link = ''
            topic.timeline_ready = False

    if False and _DEBUG:
        for key in template_var:
            print key, template_var[key]

    return render_to_response("home.html",
                              template_var,
                              context_instance=RequestContext(request))

def topic_view(request,topic_id):

    topic = Topic.objects.get(pk=topic_id)
    news_list = News.objects.filter(topic = topic)

    if _DEBUG:
        print 'in topic_view: topic_id: ', topic_id,'\t news count: ',len(news_list)

    return render_to_response("topic_view.html",
                              {"topic": topic,
                               "news_list": news_list},
                              context_instance=RequestContext(request))

def news_timeline(request,topic_id):
    _ua = request.META['HTTP_USER_AGENT']
    _res = re.search('MSIE\s[1-7]\.[^;]*', _ua)
    if _res:
        print 'unsurpported browser:\t', _res.group()
        return HttpResponse('''<p style="text-align:center;">
        我们的Timeline插件不支持您当前使用的浏览器(%s)，建议您安装Chrome, Firefox或者升级IE到8.0以上的版本。<br>
        <a href='/'>返回</a></p>
        ''' % (_res.group()))

    topic = Topic.objects.get(id = topic_id)
    news_timeline_file = topic.title + ".jsonp"
    if _DEBUG:
        print 'in news_timeline: topic_id: ', topic_id

    return render_to_response("news_timeline.html",
                              {"news_timeline_file": news_timeline_file},
                              context_instance=RequestContext(request))

def follow_topic(request):
    if not request.is_ajax():
        return HttpResponse('ERROR:NOT AJAX REQUEST')
    post_data = simplejson.loads(request.raw_post_data)
    if _DEBUG:
        print post_data
    try:
        t = Topic.objects.get(pk=post_data['t_id'])
        current_account = Account.objects.get(pk=post_data['u_id'])
        t.watcher.add(current_account)
        t.save()
    except:
        print 'post_data error...'
        return HttpResponse(simplejson.dumps(False), _mimetype)
    return HttpResponse(simplejson.dumps(True), _mimetype)

def unfollow_topic(request):
    if not request.is_ajax():
        return HttpResponse('ERROR:NOT AJAX REQUEST')
    post_data = simplejson.loads(request.raw_post_data)
    if _DEBUG:
        print post_data
    try:
        t = Topic.objects.get(pk=post_data['t_id'])
        current_account = Account.objects.get(pk=post_data['u_id'])
        t.watcher.remove(current_account)
        t.save()
    except:
        print 'post_data error...'
        return HttpResponse(simplejson.dumps(False), _mimetype)
    return HttpResponse(simplejson.dumps(True), _mimetype)

def show_more_topics(request):
    '''
    对已有的topics按照关注人数排序，返回从start_idx开始的count个topic
    exclude_user：是否除去当前用户关注的话题
    TODO: exclude用法，简化代码
    '''
    if not request.is_ajax():
        return HttpResponse('ERROR:NOT AJAX REQUEST')

    post_data = simplejson.loads(request.raw_post_data)
    if _DEBUG:
        print post_data
    start_idx = post_data['start_idx']
    count = post_data['count']
    exclude_user = post_data['exclude_user']
    exclude_set = []

    if request.user.is_authenticated() and exclude_user:
        current_account = User.objects.get(username = request.user.username).account_set.all()[0]
        exclude_set.append(current_account)

    _available_count = Topic.objects.exclude(watcher__in=exclude_set).count()

    if _available_count < start_idx:
        count = 0
    elif _available_count < start_idx + count:
        count = _available_count - start_idx

    if count > 0:
        more_topics = Topic.objects.exclude(watcher__in=exclude_set).annotate(watcher_count=Count('watcher')).order_by( '-watcher_count' )[start_idx: start_idx + count]
    else:
        more_topics = []

    for topic in more_topics:
        if topic.news_set.count() > 0:
            _news = topic.news_set.all()[0]
            topic.recent_news_title = _news.title
            topic.recent_news_link = _news.link
            topic.timeline_ready = True
        else:
            topic.recent_news_title= '还没来得及更新＝＝!'
            topic.recent_news_link = ''
            topic.timeline_ready = False

    rendered = render_to_string('other_topic_item_set.html', {'topics': more_topics})

    return HttpResponse(simplejson.dumps(rendered), content_type='application/json')

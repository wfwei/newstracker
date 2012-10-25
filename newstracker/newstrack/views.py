#coding=utf-8

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.models import User

from django.utils import simplejson

from newstracker.newstrack.models import Topic, News
from newstracker.account.models import Account

_DEBUG = True
_mimetype =  'application/javascript, charset=utf8'

'''
TODO: 
1. 直接传输topic对象太大了，后面要什么传什么
3. 
'''
def topic_list(request, account_id=None):
    if not request.user.is_authenticated():
        print 'in topic_list user not logged in ', request.user
    else:
        print 'in topic_list user logged in ', request.user.username
    if account_id is not None:
        current_account = Account.objects.get(pk = account_id)
    else:
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login')
        _user = User.objects.get(username = request.user.username)
        current_account = _user.account_set.all()[0]

    topic_list = Topic.objects.all()
    my_topics = []
    other_topics = []
    for topic in topic_list:
        if current_account in topic.watcher.all():
            my_topics.append(topic)
        else:
            other_topics.append(topic)
    if False and _DEBUG:
        print 'DEBUG mode in topic_list:'
        print 'current_account: ', current_account
        print 'my_topics: ', my_topics
        print 'other_topics: ', other_topics

    return render_to_response("topic_list.html",
                              {"my_topics": my_topics,
                               "other_topics": other_topics,
                               "current_account": current_account},
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

    topic = Topic.objects.get(pk=topic_id)
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
    
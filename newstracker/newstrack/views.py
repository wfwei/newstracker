#coding=utf-8

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext

from newstracker.newstrack.models import Topic, News

import collections;
import datetime
import calendar

_DEBUG = True

def topic_list(request):

    topic_list = Topic.objects.all()

    if _DEBUG:
        print topic_list

    return render_to_response("topic_list.html",
                              {"topic_list": topic_list},
                              context_instance=RequestContext(request))
    
def topic_view(request,topic_id):

    topic = Topic.objects.get(pk=topic_id)
    news_list = News.objects.filter(topic = topic)
    
    if _DEBUG:
        print topic_id,'\n',len(news_list)

    return render_to_response("topic_view.html",
                              {"topic": topic,
                               "news_list": news_list},
                              context_instance=RequestContext(request))
# coding=utf-8
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count
from django.utils import simplejson

from newstracker.newstrack.models import Topic, News
from newstracker.account.models import Account
from newstracker.account.forms import SettingForm

from libweibo.weiboAPI import weiboAPI

import datetime
import itertools
import re

_DEBUG = True
_mimetype = 'application/javascript, charset=utf8'

def _get_account_from_req(request):
    cur_acc = None
    try:
        cur_acc = User.objects.get(username=request.user.username).account_set.all()[0]
    except:
        print 'invalid user:' + request.user.username
    return cur_acc

'''
TODO:
1. 直接传输topic对象太大了，后面要什么传什么
'''
def home(request):
    template_var = {}
    my_topics = []
    exclude_set = []
    if request.user.is_authenticated():
        current_account = _get_account_from_req(request)
        if not current_account:
            return HttpResponse('''当前用户没有Account帐号''')
        my_topics = current_account.topic_set.all()
        template_var['current_account'] = current_account
        template_var['my_topics'] = my_topics
        exclude_set.append(current_account)
    else:
        current_account = None
        # 用户weibo登录的认证链接
        template_var['authorize_url'] = weiboAPI().getAuthorizeUrl()

    # 得到数据库其他的比较热门的5个话题
    other_topics = Topic.alive_objects.exclude(watcher__in=exclude_set).\
    annotate(watcher_count=Count('watcher')).order_by('-watcher_count')[:5]
    template_var['other_topics'] = other_topics

    # 得到数据库中最新的5个话题(原本就是按照时间排列的)
    new_topics = Topic.alive_objects.exclude(watcher__in=exclude_set)[:5]
    template_var['new_topics'] = new_topics

    for topic in itertools.chain(my_topics, other_topics, new_topics):
        _news_count = topic.news_set.count()
        if _news_count > 0:

            if _news_count > 6:
                _lmt = 6
            else:
                _lmt = _news_count
            _news_list = topic.news_set.all()[:_lmt]
            topic.recent_news[topic.title] = []
            topic.recent_news[topic.title].append({'title':_news_list[0].title, \
                                                   'link':_news_list[0].link, \
                                                   'time_passed':_get_time_passed(_news_list[0].pubDate)})
            topic.recent_news[topic.title].append({'title':_news_list[_lmt / 2].title, \
                                                   'link':_news_list[_lmt / 2].link, \
                                                   'time_passed':_get_time_passed(_news_list[_lmt / 2].pubDate)})
            topic.recent_news[topic.title].append({'title':_news_list[_lmt - 1].title, \
                                                   'link':_news_list[_lmt - 1].link, \
                                                   'time_passed':_get_time_passed(_news_list[_lmt - 1].pubDate)})
            topic.timeline_ready = True
        else:
            topic.recent_news[topic.title] = []
            topic.recent_news[topic.title].append({'title':'还木有更新呢＝＝！', \
                                                   'link':'javascript:void(0)', \
                                                   'time_passed':_get_time_passed(datetime.datetime.now())})
            topic.timeline_ready = False

    if _DEBUG:
        for key in template_var:
            print key, template_var[key]

    template_var["setting_form"] = _get_setting_form(current_account)

    return render_to_response("home.html",
                              template_var,
                              context_instance=RequestContext(request))

def _get_setting_form(account=None):
    if account:
        return SettingForm(initial={'username': account.weiboName, \
                                'email': account.user.email, \
                                'cross_remind': account.allow_remind_others, \
                                'comment_remind': account.comment_remind, \
                                'repost_remind' : account.repost_remind, \
                                'at_remind':account.at_remind, \
                                'daily_remind_limit':account.remind_daily_limit})
    else:
        return SettingForm()

def topic_view(request, topic_id):

    topic = Topic.objects.get(pk=topic_id)
    news_list = News.objects.filter(topic=topic)

    if _DEBUG:
        print 'in topic_view: topic_id: ', topic_id, '\t news count: ', len(news_list)

    return render_to_response("topic_view.html",
                              {"topic": topic,
                               "news_list": news_list},
                              context_instance=RequestContext(request))

def news_timeline(request, topic_id):
    _ua = request.META['HTTP_USER_AGENT']
    _res = re.search('MSIE\s[1-7]\.[^;]*', _ua)
    if _res:
        print 'unsurpported browser:\t', _res.group()
        return HttpResponse('''<p style="text-align:center;">
        我们的Timeline插件不支持您当前使用的浏览器(%s)，建议您安装Chrome, Firefox或者升级IE到8.0以上的版本。<br>
        <a href='/'>返回</a></p>
        ''' % (_res.group()))

    topic = Topic.objects.get(id=topic_id)
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

def user_setting(request):
    '''
    保存用户配置
    '''
    template_var = {}
    form = SettingForm()
    if request.method == "POST" and request.is_ajax() and request.user.is_authenticated():
        '''
        <QueryDict: {
        u'username': [u'WeBless'], 
        u'daily_remind_limit': [u'1'], 
        u'at_remind': [u'on'], 
        u'cross_remind': [u'on'], 
        u'repost_remind': [u'on'], #如果关掉则不会有该条记录
        u'email': [u'1698863684@fakeemail.com'], 
        u'comment_remind': [u'on']}>
        '''
        cur_acc = _get_account_from_req(request)
        if cur_acc:
            form = SettingForm(request.POST.copy())
            # TODO: get to know is_valid and remove True
            if True or form.is_valid():
                form_data = request.POST.copy()
                cur_acc.user.username = form_data["username"]
                cur_acc.user.email = form_data["email"]
                cur_acc.remind_daily_limit = int(form_data["daily_remind_limit"])
                cur_acc.at_remind = 'at_remind' in form_data
                cur_acc.allow_remind_others = "cross_remind" in form_data
                cur_acc.repost_remind = "repost_remind" in form_data
                cur_acc.comment_remind = "comment_remind" in form_data
                cur_acc.save()
                form = _get_setting_form(cur_acc)
            else:
                messages.add_message(request, messages.ERROR, '请检查输入')
        else:
            messages.add_message(request, messages.ERROR, '请先登录')

    template_var["setting_form"] = form
    template_var["messages"] = messages

    rendered = render_to_string("settings.html", template_var)
    return HttpResponse(simplejson.dumps(rendered), content_type='application/json')


def show_more_topics(request):
    '''
    对已有的topics按照关注人数排序，返回从start_idx开始的count个topic
    exclude_user：是否除去当前用户关注的话题
    TODO: exclude用法，简化代码
    '''
    template_var = {}

    if not request.is_ajax():
        return HttpResponse('ERROR:NOT AJAX REQUEST')

    if request.user.is_authenticated():
        try:
            current_account = User.objects.get(username=request.user.username).account_set.all()[0]
            template_var['current_account'] = current_account
        except:
            pass

    post_data = simplejson.loads(request.raw_post_data)
    if _DEBUG:
        print post_data
    type = post_data['type']
    start_idx = post_data['start_idx']
    count = post_data['count']
    exclude_user = post_data['exclude_user']
    exclude_set = []

    if request.user.is_authenticated() and exclude_user:
        current_account = User.objects.get(username=request.user.username).account_set.all()[0]
        exclude_set.append(current_account)

    _available_count = Topic.alive_objects.exclude(watcher__in=exclude_set).count()

    if _available_count < start_idx:
        count = 0
    elif _available_count < start_idx + count:
        count = _available_count - start_idx

    if count > 0:
        if type == 'new':
            more_topics = Topic.alive_objects.exclude(watcher__in=exclude_set)[start_idx: start_idx + count]
        else:
            more_topics = Topic.alive_objects.exclude(watcher__in=exclude_set).\
            annotate(watcher_count=Count('watcher')).order_by('-watcher_count')[start_idx: start_idx + count]
    else:
        more_topics = []

    for topic in more_topics:
        _news_count = topic.news_set.count()
        if _news_count > 0:

            if _news_count > 6:
                _lmt = 6
            else:
                _lmt = _news_count
            _news_list = topic.news_set.all()[:_lmt]
            topic.recent_news[topic.title] = []
            topic.recent_news[topic.title].append({'title':_news_list[0].title, \
                                                   'link':_news_list[0].link, \
                                                   'time_passed':_get_time_passed(_news_list[0].pubDate)})
            topic.recent_news[topic.title].append({'title':_news_list[_lmt / 2].title, \
                                                   'link':_news_list[_lmt / 2].link, \
                                                   'time_passed':_get_time_passed(_news_list[_lmt / 2].pubDate)})
            topic.recent_news[topic.title].append({'title':_news_list[_lmt - 1].title, \
                                                   'link':_news_list[_lmt - 1].link, \
                                                   'time_passed':_get_time_passed(_news_list[_lmt - 1].pubDate)})
            topic.timeline_ready = True
        else:
            topic.recent_news[topic.title] = []
            topic.recent_news[topic.title].append({'title':'还木有更新呢＝＝！', \
                                                   'link':'javascript:void(0)', \
                                                   'time_passed':_get_time_passed(datetime.datetime.now())})
            topic.timeline_ready = False

    template_var['topics'] = more_topics
    rendered = render_to_string('other_topic_item_set.html', template_var)
    return HttpResponse(simplejson.dumps(rendered), content_type='application/json')

def _get_time_passed(from_dt, to_dt=datetime.datetime.now()):
    if from_dt > to_dt:
        return '未来式～'

    tdelta = to_dt - from_dt
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    if d['days'] > 0:
        res = str(d['days']) + '天'
    elif d["hours"] > 0:
        res = str(d["hours"]) + '小时'
    else:
        res = str(d['minutes']) + '分钟'
    return res + '前'





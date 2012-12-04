# !/usr/bin/python
# -*- coding: utf-8 -*-
from newstracker.newstrack.models import Topic, News, Weibo, Task
from newstracker.account.models import Account, Useroauth2
from django.contrib import admin
import datetime
import time
admin.site.register(News)

def activate_topic(modeladmin, request, queryset):
    queryset.update(state=1)
activate_topic.short_description = "Set state as alive(1)"

def mute_topic(modeladmin, request, queryset):
    queryset.update(state=0)
mute_topic.short_description = "Set state as dead(0)"

def delete_topic_news(modeladmin, request, queryset):
    for topic in queryset:
        topic.news_set.all().delete()
delete_topic_news.short_description = "Permanently remove news"

def unsubscribe_topic(modeladmin, request, queryset):
    for topic in queryset:
        Task.objects.get_or_create(type='unsubscribe', topic=topic)
unsubscribe_topic.short_description = "Add unsubscribe task"


class TopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'count_weibo', 'count_news', 'state']
    ordering = ['-state']
    actions = [activate_topic, mute_topic, delete_topic_news, unsubscribe_topic]

    def queryset(self, request):
        """
        no customization
        """
        return super(TopicAdmin, self).queryset(request)

    def count_weibo(self, obj):
        return '(%d/%d)' % (obj.watcher_weibo.count(), obj.watcher.count())
    count_weibo.short_description = 'watcher(weibo/people)'

    def count_news(self, obj):
        return str(obj.news_set.count())
    count_news.short_description = 'news'

admin.site.register(Topic, TopicAdmin)


def activate_task(modeladmin, request, queryset):
    queryset.update(status=1)
activate_task.short_description = "Activate task"

def mute_task(modeladmin, request, queryset):
    queryset.update(status=0)
mute_task.short_description = "Mute task"

def change_to_subscribe_task(modeladmin, request, queryset):
    queryset.update(type='subscribe', status=1)
change_to_subscribe_task.short_description = "Change to subscribe task"

class TaskAdmin(admin.ModelAdmin):
    list_display = ['topic', 'type', 'status', 'time']
    ordering = ['-status', 'type', '-time']
    actions = [activate_task, mute_task, change_to_subscribe_task]
admin.site.register(Task, TaskAdmin)

class WeiboAdmin(admin.ModelAdmin):
    list_display = ['weibo_id', 'text', 'calc_active', 'user', 'created_at' ]
    ordering = ['-reposts_count', '-comments_count']

    def calc_active(self, obj):
        return '(%d,%d)' % (obj.reposts_count, obj.comments_count)
    calc_active.short_description = '(repost, comment)'

admin.site.register(Weibo, WeiboAdmin)


class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'weiboId', 'weiboName', 'comb' \
                    , 'weiboStatusesCount', 'weiboVerified', 'weiboFollowMe']
    def comb(self, obj):
        return '%d(%d,%d)' % (obj.weiboFriendsCount / obj.weiboFollowersCount, obj.weiboFriendsCount, obj.weiboFollowersCount)
    comb.short_description = '关注比(关注, 粉丝)'
admin.site.register(Account, AccountAdmin)

class Useroauth2Admin(admin.ModelAdmin):
    list_display = ['server', 'u_id', 'access_token' \
                    , 'format_time', 'is_expired']
    def is_expired(self, obj):
        return float(obj.expires_in) < time.time()

    def format_time(self, obj):
        return datetime.datetime.fromtimestamp(long(obj.expires_in)).strftime('%Y-%m-%d %H:%M:%S')
    format_time.short_description = 'expires_in'

admin.site.register(Useroauth2, Useroauth2Admin)

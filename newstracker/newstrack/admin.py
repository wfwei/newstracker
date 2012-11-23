# !/usr/bin/python
# -*- coding: utf-8 -*-
from newstracker.newstrack.models import Topic, News, Weibo, Task
from newstracker.account.models import Account, Useroauth2
from django.contrib import admin
import datetime
admin.site.register(News)

def reset_state(modeladmin, request, queryset):
    queryset.update(state=1)
reset_state.short_description = "reset state"

def delete_selected(modeladmin, request, queryset):
    queryset.update(state=0)
delete_selected.short_description = "delete topic(mark as dead state)"

def delete_topic_news(modeladmin, request, queryset):
    for topic in queryset:
        topic.news_set.all().delete()
delete_topic_news.short_description = "permanently remove news"

def add_unsubscribe_task(modeladmin, request, queryset):
    for topic in queryset:
        Task.objects.get_or_create(type='unsubscribe', topic=topic)
add_unsubscribe_task.short_description = "add unsubscribe task"


class TopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'count_weibo', 'count_news', 'state']
    ordering = ['-state']
    actions = [reset_state, delete_selected, delete_topic_news, add_unsubscribe_task]

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


class TaskAdmin(admin.ModelAdmin):
    list_display = ['topic', 'type', 'status', 'time']
    ordering = ['-status']

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
        return datetime.datetime.fromtimestamp(long(obj.expires_in)) > datetime.datetime.now()

    def format_time(self, obj):
        return datetime.datetime.fromtimestamp(long(obj.expires_in)).strftime('%Y-%m-%d %H:%M:%S')
    format_time.short_description = 'expires_in'

admin.site.register(Useroauth2, Useroauth2Admin)

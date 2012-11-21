from newstracker.newstrack.models import Topic, News, Weibo, Task
from django.contrib import admin

admin.site.register(News)
admin.site.register(Weibo)
admin.site.register(Task)

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
delete_selected.short_description = "add unsubscribe task"


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

from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'posts.views.index', name="index"),
    url(r'^f/(?P<cono>\w+)/$', 'posts.views.index'),
    url(r'^new$', 'posts.views.new_post'),
    url(r'^generate$', 'posts.views.generate_datagraph'),
    url(r'^search$', 'posts.views.search'),
    url(r'^comments$', 'posts.views.comments'),
)

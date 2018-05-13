from django.conf.urls import patterns, include, url

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'feelday.views.home', name='home'),
                       # url(r'^blog/', include('blog.urls')),

                       # It seems that reverse() needs a namespace if you define
                       # a namespace inside an include()
                       url(r'^admin/', include(admin.site.urls)),
                       # url(r'^$', include('posts.urls', namespace='posts'))
                       url(r'^$', 'posts.views.index'),
                       url(r'^submitted/$', 'posts.views.redirect'),
                       url(r'^replies/(\d+)/$', 'posts.views.replies'),
                       url(r'^topfeels$', 'posts.views.most_replied'),
                       url(r'^reply$', 'posts.views.quick_reply'),
                       url(r'^banned$', 'posts.views.banned'),
                       url(r'^mod$', 'posts.views.mod'),
                       url(r'^moderation$', 'posts.views.moderation'),
                       url(r'^generate$', 'posts.views.generate_datagraph'),
                       url(r'^stats$', 'posts.views.stats'),
                       url(r'^top_meme$', 'posts.views.top_memes'),
                       url(r'^rules$', 'posts.views.rules'),
                       url(r'^memes_mod$', 'posts.views.memes_mod'),
                       url(r'api/fph.json$', 'posts.views.stats_json'),
                       url(r'api/latest.json$', 'posts.views.latest_json'),
                       url(r'^upload/oakycoffee/$', 'posts.views.upload_image'),
                       url(r'^book/$', 'posts.views.book'),
                       url(r'^limits/$', 'posts.views.get_limits'),
                       url(r'^search/$', 'posts.views.search_view'),
                       url(r'^comments/$', 'posts.views.comments'),
                       url(r'^pages/$', 'posts.views.pages'),
                       )

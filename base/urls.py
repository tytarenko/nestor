from django.conf.urls import url, include
from django.conf import settings


from base import views



urlpatterns = [
    url(r'^$', views.main, name='main'),
    url(r'^publications/$', views.main, name='publications'),
    url(r'^publications/(?P<pk>[0-9]+)/$', views.publication, name='publication'),
    url(r'^categories/(?P<slug>\w+)?$', views.categories, name='categories'),
    url(r'^users/$', views.users, name='users'),
    url(r'^users/(?P<username>\w+)/$', views.user_profile, name='user_profile'),
    url(r'^users/(?P<username>\w+)/publications/$', views.user_publications, name='user_publications'),
    url(r'^users/(?P<username>\w+)/comments/$', views.user_comments, name='user_comments'),
    url(r'^users/(?P<username>\w+)/bookmarks/publications$', views.user_publications_bookmarks, name='user_publications_bookmarks'),
    url(r'^users/(?P<username>\w+)/bookmarks/comments', views.user_comments_bookmarks, name='user_comments_bookmarks'),
    url(r'^users/(?P<username>\w+)/user_follows/$', views.user_follows, name='user_follows'),
    url(r'^users/(?P<username>\w+)/user_followers/$', views.user_followers, name='user_followers'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

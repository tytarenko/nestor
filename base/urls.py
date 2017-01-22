from django.conf.urls import url, include
from django.conf import settings

from base import views


urlpatterns = [
    url(r'^$', views.main, name='main'),

    url(r'^publications/', include([
        url(r'^$', views.main, name='publications'),
        url(r'^(?P<publication_id>[0-9]+)/', views.publication, name='publication'),
        url(r'^(?P<publication_id>[0-9]+)/voicing/(?P<voice>like|unlike)/$', views.publication_voicing, name='publication_voicing'),
        # url(r'^(?P<publication_id>[0-9]+)/comments/(?P<comment_id>[0-9]+)/', include([
        #     url(r'^voicing/(?P<voice>like|unlike)/$', views.comment_voicing, name='comment_voicing'),
        # ]))
    ])),

    url(r'^categories/(?P<slug>\w+)?$', views.categories, name='categories'),

    url(r'^comments/(?P<comment_id>[0-9]+)/voicing/(?P<voice>like|unlike)/$', views.comment_voicing, name='comment_voicing'),

    url(r'^auth/register/', include([
        url(r'^$', views.RegistrationView.as_view(), name='registration'),
        url(r'^finality/(?P<hashcode>\w+)/$', views.RegistrationFinalityView.as_view(), name='registration_finality'),
        url(r'^invite/(?P<code>\w+)/$', views.RegistrationWithInviteView.as_view(), name='registration_with_invite'),
    ])),

    url(r'^login_as/(?P<username>\w+)/', views.login_as, name='login_as'),

    url(r'^users/', views.users, name='users'),

    url(r'^@(?P<username>\w+)/', include([
        url(r'^$', views.user_profile, name='user_profile'),
        url(r'^publications/$', views.user_publications, name='user_publications'),
        url(r'^comments/$', views.user_comments, name='user_comments'),
        url(r'^bookmarks/publications$', views.user_publications_bookmarks, name='user_publications_bookmarks'),
        url(r'^bookmarks/comments', views.user_comments_bookmarks, name='user_comments_bookmarks'),
        url(r'^user_follows/$', views.user_follows, name='user_follows'),
        url(r'^user_followers/$', views.user_followers, name='user_followers'),
    ])),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

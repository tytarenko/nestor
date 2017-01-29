from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.conf import settings

from base import views
urlpatterns = [
    url(r'^$', views.PublicationListView.as_view(), name='main'),

    url(r'^publications/', include([
        url(r'^$', views.PublicationListView.as_view(), name='publications'),
        url(r'^(?P<publication_id>[0-9]+)/$', views.PublicationDetailView.as_view(), name='publication'),
        url(r'^(?P<publication_id>[0-9]+)/voicing/(?P<voice>like|unlike)/$', views.publication_voicing, name='publication_voicing'),
        url(r'^(?P<publication_id>[0-9]+)/comments/', include([
            url(r'^add/$', views.CommentCreateView.as_view(), name='comment_add'),
        ]))
    ])),

    url(r'^categories/$', views.CategoryListView.as_view(), name='categories'),
    url(r'^categories/(?P<slug>\w+)/$', views.CategoryDetailView.as_view(), name='category'),
    url(r'^comments/(?P<comment_id>[0-9]+)/voicing/(?P<voice>like|unlike)/$', views.comment_voicing, name='comment_voicing'),

    url(r'^comments/(?P<comment_id>[0-9]+)/edit/$', views.CommentUpdateView.as_view(), name='comment_edit'),
    url(r'^comments/(?P<comment_id>[0-9]+)/delete/$', views.CommentDeleteView.as_view(), name='comment_delete'),

    url(r'^auth/register/', include([
        url(r'^$', views.RegistrationView.as_view(), name='registration'),
        url(r'^finality/(?P<hashcode>\w+)/$', views.RegistrationFinalityView.as_view(), name='registration_finality'),
        url(r'^invite/(?P<code>\w+)/$', views.RegistrationWithInviteView.as_view(), name='registration_with_invite'),
    ])),

    url(r'^auth/close/$', TemplateView.as_view(template_name='registration/close.html')),

    url(r'^login_as/(?P<username>\w+)/', views.login_as, name='login_as'),

    url(r'^users/$', views.UsersListView.as_view(), name='users'),

    url(r'^@(?P<username>\w+)/', include([
        url(r'^$', views.UserProfileDetailView.as_view(), name='user_profile'),
        url(r'^publications/', include([
            url(r'^$', views.UserProfilePublicationsListView.as_view(type='published'), name='user_publications'),
            url(r'^drafts/$', views.UserProfilePublicationsListView.as_view(type='drafts'), name='user_publications_drafts'),
            url(r'^create/$', views.PublicationCreateView.as_view(), name='publication_create'),
            url(r'^(?P<publication_id>[0-9]+)/edit/$', views.PublicationUpdateView.as_view(), name='publication_edit'),
            url(r'^(?P<publication_id>[0-9]+)/delete/$', views.PublicationDeleteView.as_view(), name='publication_delete'),
        ])),
        url(r'^comments/$', views.UserProfileCommentsListView.as_view(), name='user_comments'),
        url(r'^bookmarks/publications$', views.UserProfilePublicationsBookmarksListView.as_view(), name='user_publications_bookmarks'),
        url(r'^bookmarks/comments/$', views.UserProfileCommentsBookmarksListView.as_view(), name='user_comments_bookmarks'),
        url(r'^follows/$', views.UserProfileFollowsListView.as_view(), name='user_follows'),
        url(r'^followers/$', views.UserProfileFollowersListView.as_view(), name='user_followers'),
        url(r'^organizations/', include([
            url(r'subscribers/$', views.UserProfileSubscribeOrganizationsListView.as_view(type='subscribers'), name='user_subscribe_organizations'),
            url(r'created/$', views.UserProfileSubscribeOrganizationsListView.as_view(type='created'), name='user_created_organizations'),
        ])),
        url(r'^projects/', include([
            url(r'subscribers/$', views.UserProfileProjectsListView.as_view(type='subscribers'), name='user_subscribe_projects'),
            url(r'created/$', views.UserProfileProjectsListView.as_view(type='created'), name='user_created_projects'),
        ])),
        url(r'^follow/$', views.follow_user, name='follow_user'),
        url(r'^unfollow/$', views.unfollow_user, name='unfollow_user'),
    ])),


    url(r'^search/$', views.search, name='search'),

    url(r'^projects/', include([
        url(r'^$', views.ProjectsListView.as_view(), name='projects'),
        url(r'^create/$', views.ProjectsCreateView.as_view(), name='project_create'),
        url(r'^(?P<slug>\w+)/', include([
            url(r'^$', views.ProjectsDetailView.as_view(), name='project'),
            url(r'^edit/$', views.ProjectsUpdateView.as_view(), name='project_edit'),
            url(r'^delete/$', views.ProjectsDeleteView.as_view(), name='project_delete'),
            url(r'^subscribe/$', views.subscribe_project, name='subscribe_project'),
            url(r'^unsubscribe/$', views.unsubscribe_project, name='unsubscribe_project'),
            url(r'^restore/$', views.ProjectRestoreView.as_view(), name='project_restore'),
        ])),
    ])),


    url(r'^organizations/', include([
        url(r'^$', views.OrganizationListView.as_view(), name='organizations'),
        url(r'^create/$', views.OrganizationCreateView.as_view(), name='organizations_create'),
        url(r'^(?P<slug>\w+)/', include([
            url(r'^$', views.OrganizationDetailView.as_view(), name='organization_profile'),
            url(r'^edit/$', views.OrganizationUpdateView.as_view(), name='organization_edit'),
            url(r'^delete/$', views.OrganizationDeleteView.as_view(), name='organization_delete'),
            url(r'^restore/$', views.OrganizationRestoreView.as_view(), name='organization_restore'),
            url(r'^blog/$', views.OrganizationPublicationListView.as_view(), name='organization_blog'),
            url(r'^subscribers/$', views.OrganizationSubscribersListView.as_view(), name='organization_subscribers'),
            url(r'^projects/$', views.OrganizationProjectsListView.as_view(), name='organization_projects'),
            url(r'^subscribe/$', views.subscribe_organization, name='subscribe_organization'),
            url(r'^unsubscribe/$', views.unsubscribe_organization, name='unsubscribe_organization'),
        ]))

    ]))


]


if settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

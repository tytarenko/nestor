import json

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import View, ListView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.contrib.auth import login, authenticate
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .forms import RegistrationForm, RegistrationFinalityForm
from .models import (User, Publication, Comment, Category, PublicationVoice,
                     CommentVoice, UserRegistrationCode, Invite, Tag,
                     Organization, Project)
from .utils import (paginator, get_best_comments, recalculate_publication_rating,
                    recalculate_comment_rating, generate_hashcode, send_registration_mail,
                    get_username)

import logging
logger = logging.getLogger(__name__)


#####################################################################
# @TODO remove production
def login_as(request, username):
    user = User.objects.get(username=username)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    if user:
        login(request, user)
    return redirect('main')
######################################################################


class OwnershipMixin:
    """
    Mixin providing a dispatch overload that checks object ownership. is_staff and is_supervisor
    are considered object owners as well. This mixin must be loaded before any class based views
    are loaded for example class SomeView(OwnershipMixin, ListView)
    """
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        # we need to manually "wake up" self.request.user which is still a SimpleLazyObject at this point
        # and manually obtain this object's owner information.
        current_user = self.request.user._wrapped if hasattr(self.request.user, '_wrapped') else self.request.user
        # @TODO
        object_owner = getattr(self.get_object(), 'author', False) or getattr(self.get_object(), 'founder')

        if current_user != object_owner and not current_user.is_superuser and not current_user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AvailableDetailViewMixin:
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        # @TODO
        current_user = self.request.user
        object_owner = getattr(self.get_object(), 'author', False) or getattr(self.get_object(), 'founder')
        obj = self.get_object()

        obj_available_status = getattr(obj, self.available_status_field, True)

        if obj_available_status != self.available_status and current_user != object_owner \
                and not current_user.is_superuser and not current_user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PublicationListView(ListView):
    queryset = Publication.objects.filter(is_published=True).order_by('-created_at')
    template_name = 'base/pages/main.html'
    paginate_by = settings.OBJECT_PER_PAGE
    context_object_name = 'publications'


class PublicationDetailView(AvailableDetailViewMixin, DetailView):
    available_status_field = 'is_published'
    available_status = True
    model = Publication
    template_name = 'base/pages/publication.html'
    pk_url_kwarg = 'publication_id'
    context_object_name = 'publication'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publication = context['publication']
        if not publication.is_published and self.request.user != publication.author:
            raise PermissionDenied
        comments = publication.comments.all()
        if comments:
            context.update({
                'comments': comments.filter(parent=None),
                'best_comments': get_best_comments(comments)
            })
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('base.add_publication', raise_exception=True), name='dispatch')
class PublicationCreateView(CreateView):
    model = Publication
    template_name = 'base/pages/create_publication_form.html'
    fields = ['title', 'categories', 'type', 'short_description', 'fulltext', 'tags']

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.is_published = False if 'submit_draft' in self.request.POST else True
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('base.change_publication', raise_exception=True), name='dispatch')
class PublicationUpdateView(OwnershipMixin, UpdateView):
    model = Publication
    pk_url_kwarg = 'publication_id'
    template_name = 'base/pages/edit_publication_form.html'
    fields = ['title', 'categories', 'type', 'short_description', 'fulltext', 'tags']
    # success_url

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.is_published = False if 'submit_draft' in self.request.POST else True
        if form.instance.is_published:
            self.success_url = reverse_lazy('publication')
        else:
            self.success_url = reverse_lazy('user_publications_drafts', kwargs={'username': self.request.user.username})
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('base.delete_publication', raise_exception=True), name='dispatch')
class PublicationDeleteView(OwnershipMixin, DeleteView):
    model = Publication
    pk_url_kwarg = 'publication_id'
    success_url = reverse_lazy('publications')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.is_published = False
        self.object.save()
        return redirect(success_url)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class CategoryListView(ListView):
    model = Category
    template_name = 'base/pages/categories.html'
    context_object_name = 'categories'


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'base/pages/category.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publications = context['category'].publications.all()
        publications = paginator(publications, self.request)
        context.update({'publications': publications})
        return context


class UsersListView(ListView):
    model = User
    template_name = 'base/pages/users.html'
    context_object_name = 'users'

    def get_queryset(self):
        groups = Group.objects.all()
        return User.objects.all() #.filter(groups__in=groups) #.order_by('-rating', '-authority')


class UserProfileDetailView(DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'base/pages/user_profile.html'
    context_object_name = 'user'


class UserProfilePublicationsListView(UserProfileDetailView):
    type = None
    template_name = 'base/pages/user_publications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.type == 'published':
            publications = context['user'].publications.filter(is_published=True).order_by('-rating')
            publications = paginator(publications, self.request)
            context.update({'publications': publications, 'subactive_page': 'in_published'})
        elif self.type == 'draft':
            publications = context['user'].publications.filter(is_published=False)
            publications = paginator(publications, self.request)
            context.update({'publications': publications, 'subactive_page': 'draft'})
        return context


class UserProfileCommentsListView(UserProfileDetailView):
    template_name = 'base/pages/user_comments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = context['user'].comments.filter(is_deleted=False)
        comments = paginator(comments, self.request)
        context.update({'comments': comments})
        return context


class UserProfilePublicationsBookmarksListView(UserProfileDetailView):
    template_name = 'base/pages/user_publications_bookmarks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publications_bookmarks = context['user'].publication_bookmark.filter(is_published=True)
        publications_bookmarks = paginator(publications_bookmarks, self.request)
        context.update({'publications_bookmarks': publications_bookmarks})
        return context


class UserProfileCommentsBookmarksListView(UserProfileDetailView):
    template_name = 'base/pages/user_comments_bookmarks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments_bookmarks = context['user'].comment_bookmark.filter(is_deleted=False)
        comments_bookmarks = paginator(comments_bookmarks, self.request)
        context.update({'comments_bookmarks': comments_bookmarks})
        return context


class UserProfileFollowsListView(UserProfileDetailView):
    template_name = 'base/pages/user_follows.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        follows = context['user'].follows.all()
        follows = paginator(follows, self.request)
        context.update({'follows': follows})
        return context


class UserProfileFollowersListView(UserProfileDetailView):
    template_name = 'base/pages/user_followers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        followers = context['user'].follower.all()
        followers = paginator(followers, self.request)
        context.update({'followers': followers})
        return context


class UserProfileSubscribeOrganizationsListView(UserProfileDetailView):
    type = None
    template_name = 'base/pages/user_organizations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organizations = []
        if self.type == 'subscribers':
            context.update({'subactive_page': 'subscribes'})
            organizations = context['user'].subscribes_organizations.filter(is_active=True)
            organizations = paginator(organizations, self.request)
        elif self.type == 'created':
            context.update({'subactive_page': 'created'})
            organizations = context['user'].organizations.all()
            organizations = paginator(organizations, self.request)
        context.update({
            'organizations': organizations,
        })
        return context


class UserProfileProjectsListView(UserProfileDetailView):
    type = None
    template_name = 'base/pages/user_projects.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = []
        if self.type == 'subscribers':
            context.update({'subactive_page': 'subscribes'})
            projects = context['user'].subscribes_projects.filter(is_active=True)
            projects = paginator(projects, self.request)
        elif self.type == 'created':
            context.update({'subactive_page': 'created'})
            projects = context['user'].founded_projects.all()
            projects = paginator(projects, self.request)
        context.update({
            'projects': projects,
        })
        return context


def get_voice(voice):
    return {
        'like': 1,
        'unlike': -1
    }.get(voice, 0)


@login_required
@permission_required('base.add_publicationvoice', raise_exception=True)
def publication_voicing(request, publication_id, voice):
    user = request.user
    if not user.can_voting_for_publication():
        raise PermissionDenied
    publication = Publication.objects.get(pk=publication_id)
    try:
        p_voice, created = PublicationVoice.objects.get_or_create(
            voter=user,
            publication=publication,
            voice=get_voice(voice)
        )
        if not created:
            data = {'error': True, 'message': 'You already voiced'}
        else:
            publication_rating = recalculate_publication_rating(publication)
            data = {'error': False, 'message': '', 'publication_rating': publication_rating}
        return HttpResponse(json.dumps(data), content_type="application/json")
    except IntegrityError as e:
        logger.error(e)
        raise


@login_required
@permission_required('base.add_commentvoice', raise_exception=True)
def comment_voicing(request, comment_id, voice):
    if not request.is_ajax():
        raise PermissionDenied
    user = request.user
    if not user.can_voting_for_comment():
        raise PermissionDenied
    comment = Comment.objects.get(pk=comment_id)
    try:
        c_voice, created = CommentVoice.objects.get_or_create(
            voter=user,
            comment=comment,
            voice=get_voice(voice)
        )
        if not created:
            data = {'error': True, 'message': 'You already voiced'}
        else:
            comment_rating = recalculate_comment_rating(comment)
            data = {'error': False, 'message': '', 'comment_id': comment_id, 'comment_rating': comment_rating}
        return HttpResponse(json.dumps(data), content_type="application/json")
    except IntegrityError as e:
        logger.error(e)
        return HttpResponse(json.dumps({'error': True, 'message': 'You already voiced'}), content_type="application/json")


class CreateUserViewMixin:
    def create_user(self, form, group=False):
        email = form.cleaned_data['email']
        username = get_username(email)
        params = {
            'email': email,
            'username': username,
            'is_active': False,
        }
        user = User.objects.create_user(**params)
        if group:
            user.groups.add(group)
        hashcode = generate_hashcode(user.username, user.date_joined)
        send_registration_mail(email, hashcode, username)
        UserRegistrationCode.objects.create(
            user=user,
            hashcode=hashcode
        )


class RegistrationView(View, CreateUserViewMixin):
    form_class = RegistrationForm
    template_name = 'registration/registration_form.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated():
            return
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})
        sid = transaction.savepoint()
        try:
            self.create_user(form)
            transaction.savepoint_commit(sid)
            return render(request, self.template_name, {'sent': True})
        except Exception as e:
            transaction.savepoint_rollback(sid)
            # @TODO fix
            logger.error(e)


class RegistrationWithInviteView(View, CreateUserViewMixin):
    form_class = RegistrationForm
    template_name = 'registration/registration_form.html'

    def get(self, request, code):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, code):
        if request.user.is_authenticated():
            return
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})
        sid = transaction.savepoint()
        try:
            invite = get_object_or_404(Invite, code=code)
            if invite.expired < timezone.now():
                return
            self.create_user(form, invite.group)
            invite.expired = timezone.now()
            invite.save()
            transaction.savepoint_commit(sid)
            return render(request, self.template_name, {'sent': True})
        except Exception as e:
            transaction.savepoint_rollback(sid)
            # @TODO fix
            logger.error(e)


class RegistrationFinalityView(View):
    form_class = RegistrationFinalityForm
    template_name = 'registration/registration_form.html'

    def get(self, request, hashcode):
        user_registration_code = get_object_or_404(UserRegistrationCode, hashcode=hashcode)
        user = user_registration_code.user
        initial = {
            'username': user.username,
            'email': user.email
        }
        form = self.form_class(initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, hashcode):
        sid = transaction.savepoint()
        try:
            user_registration_code = get_object_or_404(UserRegistrationCode, hashcode=hashcode)
            user = user_registration_code.user
            user.is_active = True
            form = self.form_class(request.POST or None, instance=user)
            if not form.is_valid():
                return render(request, self.template_name, {'form': form})
            password = form.cleaned_data['password']
            form.save()
            user.set_password(password)
            user.save()
            transaction.savepoint_commit(sid)
            user = authenticate(username=user.username, password=password)
            if not user:
                # @TODO fix
                return redirect('login')
            login(request, user)
            return redirect('main')
        except Exception as e:
            transaction.savepoint_rollback(sid)
            # @TODO fix
            logger.error(e)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('base.add_comment', raise_exception=True), name='dispatch')
class CommentCreateView(CreateView):
    model = Comment
    template_name = 'base/pages/comment_form.html'
    fields = ['comment']

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.publication_id = self.kwargs['publication_id']
        if 'parent' in self.request.GET:
            form.instance.parent_id = self.request.GET.get('parent')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('base.change_comment', raise_exception=True), name='dispatch')
class CommentUpdateView(OwnershipMixin, UpdateView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'base/pages/comment_form.html'
    fields = ['comment']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('base.delete_comment', raise_exception=True), name='dispatch')
class CommentDeleteView(OwnershipMixin, DeleteView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    success_url = reverse_lazy('publication')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.is_deleted = True
        comment.save()
        return redirect('publication', publication_id=comment.publication_id)


def search(request):
    data = {}
    if 't' in request.GET:
        ts = request.GET.get('t')
        t = ts.split('#')
        t = filter(None, map(lambda s: s.strip(), t))
        tags = Tag.objects.filter(slug__in=t)
        publications = Publication.objects.filter(tags__in=tags)
        data.update({'publications': publications, 'tags': ts})
    return render(request, 'base/pages/search_result.html', data)


@login_required
def follow_user(request, username):
    follow_user = get_object_or_404(User, username=username)
    user = request.user
    if follow_user == user:
        raise PermissionDenied
    if follow_user not in user.follows.all():
        user.follows.add(follow_user)
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def unfollow_user(request, username):
    follow_user = get_object_or_404(User, username=username)
    user = request.user
    if follow_user == user:
        raise PermissionDenied
    if follow_user in user.follows.all():
        user.follows.remove(follow_user)
    return redirect(request.META.get('HTTP_REFERER'))


class OrganizationListView(ListView):
    queryset = Organization.objects.filter(is_active=True)
    template_name = 'base/pages/organizations.html'
    paginate_by = settings.OBJECT_PER_PAGE
    context_object_name = 'organizations'


class OrganizationDetailView(AvailableDetailViewMixin, DetailView):
    available_status_field = 'is_active'
    available_status = True
    model = Organization
    template_name = 'base/pages/organization_profile.html'
    context_object_name = 'organization'


@method_decorator(login_required, name='dispatch')
# @method_decorator(permission_required('base.add_organisation', raise_exception=True), name='dispatch')
class OrganizationCreateView(CreateView):
    model = Organization
    template_name = 'base/pages/create_organization_form.html'
    fields = ['title', 'slug', 'description', 'type', 'found_at']

    def form_valid(self, form):
        form.instance.founder = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
# @method_decorator(permission_required('base.change_organisation', raise_exception=True), name='dispatch')
class OrganizationUpdateView(OwnershipMixin, UpdateView):
    model = Organization
    template_name = 'base/pages/update_organization_form.html'
    fields = ['title', 'slug', 'description', 'type', 'found_at']

    def form_valid(self, form):
        form.instance.founder = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
# @method_decorator(permission_required('base.delete_organisation', raise_exception=True), name='dispatch')
class OrganizationDeleteView(OwnershipMixin, DeleteView):
    model = Organization

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        return redirect('user_created_organizations', username=self.request.user.username)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
# @method_decorator(permission_required('base.restore_organisation', raise_exception=True), name='dispatch')
class OrganizationRestoreView(OwnershipMixin, DeleteView):
    model = Organization

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = True
        self.object.save()
        return redirect('user_created_organizations', username=self.request.user.username)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class OrganizationPublicationListView(DetailView):
    model = Organization
    template_name = 'base/pages/organization_blog.html'
    context_object_name = 'organization'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publications = context['organization'].publications.filter(is_published=True)
        context.update({'publications': publications})
        return context


class OrganizationSubscribersListView(DetailView):
    model = Organization
    template_name = 'base/pages/organization_subscribers.html'
    context_object_name = 'organization'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscribers = context['organization'].subscriber.all()
        subscribers = paginator(subscribers, self.request)
        context.update({'subscribers': subscribers})
        return context


class OrganizationProjectsListView(DetailView):
    model = Organization
    template_name = 'base/pages/organization_projects.html'
    context_object_name = 'organization'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = context['organization']
        projects = organization.founded_projects.filter(is_active=True)
        projects = paginator(projects, self.request)
        context.update({'projects': projects})
        return context


@login_required
def subscribe_organization(request, slug):
    organization = get_object_or_404(Organization, slug=slug)
    user = request.user
    if user not in organization.subscriber.all():
        organization.subscriber.add(user)
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def unsubscribe_organization(request, slug):
    organization = get_object_or_404(Organization, slug=slug)
    user = request.user
    if user in organization.subscriber.all():
        organization.subscriber.remove(user)
    return redirect(request.META.get('HTTP_REFERER'))


@receiver(post_save, sender=Organization)
@receiver(m2m_changed, sender=Organization.employee.through)
@receiver(m2m_changed, sender=Organization.subscriber.through)
def add_subscriber_and_employee_to_organization(sender, instance, **kwargs):
    action = kwargs.get('action', False)
    created = kwargs.get('created', False)
    if isinstance(instance, Organization) and (created or (action and action in ('post_add', 'post_remove', 'post_clear', 'post_save'))):
        founder = instance.founder
        if founder not in instance.subscriber.all():
            instance.subscriber.add(founder)
        if founder not in instance.employee.all():
            instance.employee.add(founder)


@receiver(post_save, sender=Project)
@receiver(m2m_changed, sender=Project.member.through)
@receiver(m2m_changed, sender=Project.subscriber.through)
def add_subscriber_and_employee_to_organization(sender, instance, **kwargs):
    action = kwargs.get('action', False)
    created = kwargs.get('created', False)
    if isinstance(instance, Project) and (created or (action and action in ('post_add', 'post_remove', 'post_clear', 'post_save'))):
        founder = instance.founder
        if founder not in instance.subscriber.all():
            instance.subscriber.add(founder)
        if founder not in instance.member.all():
            instance.member.add(founder)


class ProjectsListView(ListView):
    queryset = Project.objects.filter(is_active=True).order_by('-created_at')
    template_name = 'base/pages/projects.html'
    context_object_name = 'projects'
    paginate_by = settings.OBJECT_PER_PAGE


class ProjectsDetailView(AvailableDetailViewMixin, DetailView):
    available_status_field = 'is_active'
    available_status = True
    model = Project
    template_name = 'base/pages/project_detail.html'
    context_object_name = 'project'


@method_decorator(login_required, name='dispatch')
# @method_decorator(permission_required('base.add_project', raise_exception=True), name='dispatch')
class ProjectsCreateView(CreateView):
    model = Project
    template_name = 'base/pages/create_project_form.html'
    fields = ['title', 'slug', 'short_description', 'fulltext']

    def form_valid(self, form):
        form.instance.founder = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
# @method_decorator(permission_required('base.add_project', raise_exception=True), name='dispatch')
class ProjectsUpdateView(UpdateView):
    model = Project
    template_name = 'base/pages/update_project_form.html'
    fields = ['title', 'slug', 'short_description', 'fulltext']

    def form_valid(self, form):
        form.instance.founder = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
# @method_decorator(permission_required('base.add_project', raise_exception=True), name='dispatch')
class ProjectsDeleteView(DeleteView):
    model = Project

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        return redirect('user_created_projects', username=self.request.user.username)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class ProjectRestoreView(DeleteView):
    model = Project

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = True
        self.object.save()
        return redirect('user_created_projects', username=self.request.user.username)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

@login_required
def subscribe_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    user = request.user
    if user not in project.subscriber.all():
        project.subscriber.add(user)
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def unsubscribe_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    user = request.user
    if user in project.subscriber.all():
        project.subscriber.remove(user)
    return redirect(request.META.get('HTTP_REFERER'))

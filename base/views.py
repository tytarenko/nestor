from datetime import datetime

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db.models.aggregates import Count
from django.views.generic import ListView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.contrib.auth import login, authenticate
from django.views.generic import View
from django.db import transaction
from django.db import IntegrityError
from django.utils import timezone

from .forms import RegistrationForm, RegistrationFinalityForm
from .models import (User, Publication, Comment, Category, PublicationVoice,
                     CommentVoice, UserRegistrationCode, UserProfile, Invite, Tag)
from .utils import (paginator, sidebar, get_best_comments, recalc_publication_rating,
                    recalc_comment_rating, generate_hashcode, send_registration_mail, )

data = sidebar()

import logging

def main(request):
    publications = Publication.objects.all()
    publications = paginator(publications, request)
    data.update({'publications': publications})
    return render(request, 'base/pages/main.html', data)


class PublicationListView(ListView):
    model = Publication
    queryset = Publication.objects.filter(is_published=True)
    template_name = 'base/pages/main.html'
    paginate_by = settings.PUBLICATIONS_PER_PAGE
    context_object_name = 'publications'


class PublicationDetailView(DetailView):
    model = Publication
    template_name = 'base/pages/publication.html'
    pk_url_kwarg = 'publication_id'
    context_object_name = 'publication'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = context['publication'].comments.all()
        if comments:
            context.update({
                'comments': comments.filter(parent=None),
                'best_comments': get_best_comments(comments)
            })
        return context


class PublicationCreateView(CreateView):
    model = Publication
    template_name = 'base/pages/publication_form.html'
    fields = ['title', 'categories', 'type', 'short_description', 'fulltext', 'tags']

    def form_valid(self, form):
        form.instance.author = self.request.user
        if 'submit_draft' in self.request.POST:
            form.instance.is_published = False
        return super().form_valid(form)


class PublicationUpdateView(UpdateView):
    model = Publication
    pk_url_kwarg = 'publication_id'
    template_name = 'base/pages/publication_form.html'
    fields = ['title', 'categories', 'type', 'short_description', 'fulltext', 'tags']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PublicationDeleteView(DeleteView):
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


def categories(request, slug):
    if slug:
        category = Category.objects.get(slug=slug)
        publications = category.publications.all()
        publications = paginator(publications, request)
        data.update({'category': category, 'publications': publications})
        return render(request, 'base/pages/category.html', data)
    categories = Category.objects.all()
    data.update({'categories': categories})
    return render(request, 'base/pages/categories.html', data)


def user_profile(request, username):
    user = User.objects.get(username=username)
    data.update({'user': user})
    return render(request, 'base/pages/user_profile.html', data)


def user_publications(request, username):
    user = User.objects.get(username=username)
    publications = user.publications.filter(is_published=True).order_by('-rating')
    publications = paginator(publications, request)
    data.update({'user': user, 'publications': publications, 'subactive_page': 'in_published'})
    return render(request, 'base/pages/user_publications.html', data)


def user_publications_drafts(request, username):
    user = User.objects.get(username=username)
    publications = user.publications.filter(is_published=False)
    publications = paginator(publications, request)
    data.update({'user': user, 'publications': publications, 'subactive_page': 'draft'})
    return render(request, 'base/pages/user_publications.html', data)


def user_comments(request, username):
    user = User.objects.get(username=username)
    comments = user.comments.all()
    comments = paginator(comments, request)
    data.update({'user': user, 'comments': comments})
    return render(request, 'base/pages/user_comments.html', data)


def users(request):
    group = Group.objects.all()
    users = User.objects.filter(groups__in=group) #.order_by('-rating', '-authority')
    data.update({'users': users})
    return render(request, 'base/pages/users.html', data)


def user_publications_bookmarks(request, username):
    user = User.objects.get(username=username)
    publications_bookmarks = user.publication_bookmark.all()
    publications_bookmarks = paginator(publications_bookmarks, request)
    data.update({'user': user, 'publications_bookmarks': publications_bookmarks})
    return render(request, 'base/pages/user_publications_bookmarks.html', data)


def user_comments_bookmarks(request, username):
    user = User.objects.get(username=username)
    comments_bookmarks = user.comment_bookmark.all()
    comments_bookmarks = paginator(comments_bookmarks, request)
    data.update({'user': user, 'comments_bookmarks': comments_bookmarks})
    return render(request, 'base/pages/user_comments_bookmarks.html', data)


def user_follows(request, username):
    user = User.objects.get(username=username)
    follows = user.follows.all()
    follows = paginator(follows, request)
    data.update({'user': user, 'follows': follows})
    return render(request, 'base/pages/user_follows.html', data)


def user_followers(request, username):
    user = User.objects.get(username=username)
    followers = user.follower.all()
    followers = paginator(followers, request)
    data.update({'user': user, 'followers': followers})
    return render(request, 'base/pages/user_followers.html', data)


def login_as(request, username):
    user = User.objects.get(username=username)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    if user:
        login(request, user)
    return redirect('main')


def get_voice(voice):
    return {
        'like': 1,
        'unlike': -1
    }.get(voice, 0)


def publication_voicing(request, publication_id, voice):
    user = request.user
    if not user.is_authenticated() or not user.can_voting_for_publication():
        return
    publication = Publication.objects.get(pk=publication_id)
    try:
        PublicationVoice.objects.get_or_create(
            voter=user,
            publication=publication,
            voice=get_voice(voice)
        )
        recalc_publication_rating(publication)
    # @TODO
    except IntegrityError:
        pass
    return redirect(request.META.get('HTTP_REFERER','/'))


def comment_voicing(request, comment_id, voice):
    user = request.user
    if not user.is_authenticated() or not user.can_voting_for_comment():
        return
    comment = Comment.objects.get(pk=comment_id)
    try:
        CommentVoice.objects.get_or_create(
            voter=user,
            comment=comment,
            voice=get_voice(voice)
        )
        recalc_comment_rating(comment)
    # @TODO
    except IntegrityError:
        pass
    return redirect(request.META.get('HTTP_REFERER', '/'))


class CreateUserViewMixin:
    def create_user(self, form, group=False):
        email = form.cleaned_data['email']
        # @TODO fix
        username, _ = email.split('@')
        username = username.replace('.', '')

        params = {
            'email': email,
            'username': username,
            'is_active': False,
        }
        user = User.objects.create_user(**params)
        if group:
            user.groups.add(group)
        hashcode = generate_hashcode(user.date_joined)
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
        except Exception:
            transaction.savepoint_rollback(sid)
            # @TODO fix
            raise


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
        except Exception:
            transaction.savepoint_rollback(sid)
            # @TODO fix
            raise


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
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            transaction.savepoint_commit(sid)
            user = authenticate(username=user.username, password=password)
            if not user:
                # @TODO fix
                return redirect('login')
            login(request, user)
            return redirect('main')
        except Exception:
            transaction.savepoint_rollback(sid)
            # @TODO fix
            raise


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


class CommentUpdateView(UpdateView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'base/pages/comment_form.html'
    fields = ['comment']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class CommentDeleteView(DeleteView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    success_url = reverse_lazy('publication')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        publication_id = comment.publication.id
        comment.delete()
        return redirect('publication', publication_id=publication_id)


def search(request):
    if 't' in request.GET:
        ts = request.GET.get('t')
        t = ts.split('#')
        t = filter(None, map(lambda s: s.strip(), t))
        tags = Tag.objects.filter(slug__in=t)
        publications = Publication.objects.filter(tags__in=tags)
        data.update({'publications': publications, 'tags': ts})
    return render(request, 'base/pages/search_result.html', data)

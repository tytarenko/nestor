from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.contrib.auth import login, authenticate
from django.views.generic import View
from django.db import transaction
from django.utils import timezone

from .forms import RegistrationForm, RegistrationFinalityForm
from .models import (User, Publication, Comment, Category, PublicationVoice,
                     CommentVoice, UserRegistrationCode, UserProfile, Invite)
from .utils import (paginator, sidebar, get_best_comments, recalc_publication_rating,
                    recalc_comment_rating, generate_hashcode, send_registration_mail, )

data = sidebar()


def main(request):
    publications = Publication.objects.all()
    publications = paginator(publications, request)
    data.update({'publications': publications})
    return render(request, 'base/pages/main.html', data)


def publication(request, publication_id):
    publication = Publication.objects.get(pk=publication_id)
    comments = publication.comments.all()
    data.update({
        'publication': publication,
        'comments': comments.filter(parent=None),
        'best_comments': get_best_comments(comments)
    })
    return render(request, 'base/pages/publication.html', data)


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
    publications = user.publications.order_by('-rating')
    publications = paginator(publications, request)
    data.update({'user': user, 'publications': publications})
    return render(request, 'base/pages/user_publications.html', data)


def user_comments(request, username):
    user = User.objects.get(username=username)
    comments = user.comments.all()
    comments = paginator(comments, request)
    data.update({'user': user, 'comments': comments})
    return render(request, 'base/pages/user_comments.html', data)


def users(request):
    # group = Group.objects.filter(name__in=['author', 'moderator', 'admin'])
    group = Group.objects.all()
    users = User.objects.filter(groups__in=group) #.order_by('-rating', '-authority')
    # users_profiles = users.userprofile.order_by('-rating', '-authority')
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
    PublicationVoice.objects.get_or_create(
        voter=user,
        publication=publication,
        voice=get_voice(voice)
    )
    recalc_publication_rating(publication)
    # return redirect(request.META.get('HTTP_REFERER','/'))

import logging
def comment_voicing(request, comment_id, voice):
    user = request.user
    # if not user.is_authenticated() or not user.can_voting_for_comment():
    #     return
    comment = Comment.objects.get(pk=comment_id)
    comment_voice, created = CommentVoice.objects.get_or_create(
        voter=user,
        comment=comment,
        voice=get_voice(voice)
    )
    logging.error({'comment': comment, 'comment_voice': comment_voice, 'created':created })
    return redirect(request.META.get('HTTP_REFERER', '/'))
    # return render(request, 'base/test.html', {'comment': comment, 'comment_voice': comment_voice, 'created':created })


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


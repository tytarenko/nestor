from django.shortcuts import render
from django.contrib.auth.models import User, Group

from .models import User, Publication, Category, UserProfile
from .utils import paginator, sidebar, get_best_comments

data = sidebar()


def main(request):
    publications = Publication.objects.all()
    publications = paginator(publications, request)
    data.update({'publications': publications})
    return render(request, 'base/pages/main.html', data)


def publication(request, pk):
    publication = Publication.objects.get(pk=pk)
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
    publications = user.publications.all()
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
    users = User.objects.filter(groups__in=group)
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

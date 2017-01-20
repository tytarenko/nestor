from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User

from .models import Category


def paginator(objects, request):
    paginate = Paginator(objects, settings.PUBLICATIONS_PER_PAGE)
    page = request.GET.get('page')
    try:
        result = paginate.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        result = paginate.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        result = paginate.page(paginate.num_pages)
    return result


def sidebar():
    categories = Category.objects.all()
    return {'categories': categories}


def recalc_users_rating():
    users = User.objects.filter(groups__name__in=['author', 'moderator', 'admin'])
    for user in users:
        user_profile = user.userprofile
        authority = user_profile.authority * settings.AUTHORITY_SCORE
        publications_rating = sum(user.publications.values_list('rating', flat=True)) * settings.TOPIC_SCORE
        comments_rating = sum(user.comments.values_list('rating', flat=True)) * settings.COMMENT_SCORE
        user_profile.rating = authority + publications_rating + comments_rating
        user_profile.save()


def get_best_comments(comments):
    comment = comments.latest('rating')
    while True:
        parent_id = comment.parent_id
        if parent_id:
            for c in comments:
                if c.id == parent_id:
                    comment = c
        else:
            break
    return comment,





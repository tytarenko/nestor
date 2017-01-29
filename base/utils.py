from hashlib import md5

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.core.mail import send_mail

from .models import User, Category


def paginator(objects, request):
    paginate = Paginator(objects, settings.OBJECT_PER_PAGE)
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


def recalculate_users_rating():
    users = User.objects.filter(groups__name__in=['author', 'moderator', 'admin'])
    for user in users:
        authority = user.authority * settings.AUTHORITY_SCORE
        publications_rating = sum(user.publications.values_list('rating', flat=True)) * settings.TOPIC_SCORE
        comments_rating = sum(user.comments.values_list('rating', flat=True)) * settings.COMMENT_SCORE
        user.rating = authority + publications_rating + comments_rating
        user.save()


def recalculate_publication_rating(publication):
    publications_voices = publication.publications_voices.all()
    publications_voices.values_list('voice', flat=True)
    publication.rating = sum(publications_voices.values_list('voice', flat=True))
    publication.save()
    return publication.rating


def recalculate_comment_rating(comment):
    comments_voices = comment.comments_voices.all()
    comments_voices.values_list('voice', flat=True)
    comment.rating = sum(comments_voices.values_list('voice', flat=True))
    comment.save()
    return comment.rating


def get_best_comments(comments):
    comment = comments.latest('rating')
    while True:
        parent = comment.parent_id
        if parent:
            for c in comments:
                if c.id == parent:
                    comment = c
        else:
            break
    return comment,


def generate_hashcode(username, datetime):
    timestamp_with_salt = '{}_{}_{}'.format(username, datetime.timestamp(), settings.REGISTRATION_SALT)
    return md5(timestamp_with_salt.encode('utf-8')).hexdigest()


# @TODO add SMTPException and setting subject and from_email and random sting
def send_registration_mail(email, hashcode, username):
    cxt = {'username': username, 'hashcode': hashcode}
    text = render_to_string('emails/reg.txt', cxt)
    html = render_to_string('emails/reg.html', cxt)
    send_mail('Finishing registration', text, 'test@mail.com', [email], html_message=html)


def get_username(email):
    username, _ = email.split('@')
    username = username.replace('.', '_')
    return username

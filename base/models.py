from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    full_name = models.CharField(_('full name'), max_length=255)
    avatar = models.ImageField(default=None, null=True)
    follower = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='follows',
    )
    publication_bookmark = models.ManyToManyField(
        'Publication',
    )
    comment_bookmark = models.ManyToManyField(
        'Comment',
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def get_full_name(self):
        return self.full_name.strip()

    def get_short_name(self):
        return self.full_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TitleSlugDescriptionModel(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        abstract = True


class TitleSlugDescriptionAuthorModel(TitleSlugDescriptionModel):
    author = models.ForeignKey(User)

    class Meta:
        abstract = True


class OrganisationType(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    pass


class Organisation(TimeStampedModel, TitleSlugDescriptionModel):
    type = models.ForeignKey(OrganisationType, related_name='organisations')
    avatar = models.ImageField(default=None, null=True)
    background_image = models.ImageField(default=None, null=True)
    founder = models.ForeignKey(User, related_name="founded_organisations")
    employee = models.ManyToManyField(
        User,
        related_name='organisations',
    )
    subscriber = models.ManyToManyField(
        User,
        related_name='subscribes_organisations',
    )
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        default=None
    )


class UserProfile(TimeStampedModel):
    background_image = models.ImageField(default=None, null=True)
    bio = models.TextField()
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    authority = models.FloatField(default=0)
    rating = models.FloatField(default=0)

    def __str__(self):
        return self.full_name


class Category(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    class Meta:
        verbose_name_plural = "categories"


class Tag(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    pass


class PublicationType(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    pass


class Blog(TimeStampedModel):
    organisation = models.OneToOneField(
        Organisation,
        on_delete=models.CASCADE,
        primary_key=True,
    )


class Publication(TimeStampedModel):
    title = models.TextField()
    type = models.ForeignKey(PublicationType, related_name='publications')
    short_description = models.TextField()
    fulltext = models.TextField()
    categories = models.ManyToManyField(Category, related_name='publications')
    tags = models.ManyToManyField(Tag, related_name='publications')
    author = models.ForeignKey(User, related_name='publications')
    blog = models.ForeignKey(
        Blog,
        related_name='publications',
        default=None,
        null=True
    )
    rating = models.IntegerField(default=0)
    published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Comment(TimeStampedModel):
    comment = models.TextField()
    author = models.ForeignKey(User, related_name="comments")
    publication = models.ForeignKey(Publication, related_name="comments")
    rating = models.IntegerField(default=0)
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        default=None
    )

    def __str__(self):
        return self.comment[:75] + (self.comment[75:] and '...')


class PublicationVoice(TimeStampedModel):
    publication = models.ForeignKey(Publication, related_name="publications_voices")
    voter = models.ForeignKey(User, related_name="publications_voices")
    voice = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = (('publication', 'voter'),)


class CommentVoice(TimeStampedModel):
    comment = models.ForeignKey(Comment, related_name="comments_voices")
    voter = models.ForeignKey(User, related_name="comments_voices")
    voice = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = (('comment', 'voter'),)


class UserVoice(TimeStampedModel):
    user = models.ForeignKey(User, related_name="users_voices")
    voter = models.ForeignKey(User, related_name="voters_voices")
    voice = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = (('user', 'voter'),)

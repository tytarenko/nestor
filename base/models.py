from datetime import date

from django.contrib.auth.models import AbstractUser, Group
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

import logging
logger = logging.getLogger(__name__)


class User(AbstractUser):
    avatar = models.ImageField(default=None, null=True)
    avatar_url = models.CharField(max_length=255, default=None, null=True)
    follower = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='follows',
    )
    publication_bookmark = models.ManyToManyField('Publication')
    comment_bookmark = models.ManyToManyField('Comment')
    is_verified = models.BooleanField(default=False)
    background_image = models.ImageField(default=None, null=True)
    bio = models.TextField()
    authority = models.FloatField(default=0)
    rating = models.FloatField(default=0)
    founded_projects = GenericRelation('Project')

    def get_group(self):
        return self.groups.first() or 'reader'

    # @TODO:
    def can_voting_for_publication(self):
        # return True if self.get_goup() and self.userprofile.rating >= -15 else False
        return True

    # @TODO:
    def can_voting_for_comment(self):
        return True if self.get_group() and self.userprofile.rating >= -15 else False

    # @TODO
    def can_create_organization(self):
        return True

    def is_my_follower(self, user):
        return user in self.follower.all()

    def is_follow_user(self, user):
        return user in self.follows.all()


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


class OrganizationType(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    pass


class Organization(TimeStampedModel, TitleSlugDescriptionModel):
    type = models.ForeignKey(OrganizationType, related_name='organizations')
    avatar = models.ImageField(default=None, null=True)
    background_image = models.ImageField(default=None, null=True)
    founder = models.ForeignKey(User, related_name="founded_organizations")
    employee = models.ManyToManyField(
        User,
        related_name='organizations',
    )
    subscriber = models.ManyToManyField(
        User,
        related_name='subscribes_organizations',
    )
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        default=None
    )
    is_active = models.BooleanField(default=True)
    found_at = models.DateField(_("was found "), default=date.today)
    founded_projects = GenericRelation('Project')

    def get_publications_count(self):
        return self.publications.filter(is_published=True).count()

    def get_subscribers_count(self):
        return self.subscriber.count()

    def get_absolute_url(self):
        return reverse('organization_profile', kwargs={'slug': self.slug})


class Category(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    class Meta:
        verbose_name_plural = "categories"

    def publications_count(self):
        return self.publications.filter(is_published=True).count()


class Tag(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    pass


class PublicationType(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    pass


class Publication(TimeStampedModel):
    title = models.TextField()
    type = models.ForeignKey(PublicationType, related_name='publications')
    short_description = models.TextField()
    fulltext = models.TextField()
    categories = models.ManyToManyField(Category, related_name='publications')
    tags = models.ManyToManyField(Tag, related_name='publications')
    author = models.ForeignKey(User, related_name='publications')
    organization = models.ForeignKey(
        Organization,
        related_name='publications',
        default=None,
        null=True
    )
    rating = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('publication', kwargs={'publication_id': self.pk})


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
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.comment[:75] + (self.comment[75:] and '...')

    def get_absolute_url(self):
        return reverse('publication', kwargs={'publication_id': self.publication.pk})


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


class InviteType(TimeStampedModel, TitleSlugDescriptionAuthorModel):
    pass


class Invite(TimeStampedModel):
    type = models.ForeignKey(InviteType, related_name='invites')
    inviter = models.ForeignKey(User, related_name="invites")
    email = models.EmailField(null=True, default=None)
    expired = models.DateTimeField(null=True, default=None)
    code = models.CharField(max_length=255)
    invited = models.OneToOneField(
        User,
        related_name="invited",
        null=True,
        default=None,
        blank=True,
    )
    group = models.OneToOneField(
        Group,
        related_name="invites",
        null=True,
        default=None
    )


class UserRegistrationCode(TimeStampedModel):
    expired = models.DateTimeField(null=True, default=None)
    hashcode = models.CharField(max_length=255, null=True, default=None)
    user = models.OneToOneField(
        User,
        related_name="registration_code"
    )


class Project(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    short_description = models.TextField()
    fulltext = models.TextField()
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    founder = GenericForeignKey('content_type', 'object_id')
    is_active = models.BooleanField(default=True)
    subscriber = models.ManyToManyField(
        User,
        related_name='subscribes_projects',
    )
    member = models.ManyToManyField(
        User,
        related_name='working_projects',
    )

    def __str__(self):
        return '{} ({})'.format(self.title, self.content_type)

    def get_absolute_url(self):
        return reverse('project', kwargs={'slug': self.slug})

import random

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.db import IntegrityError
import elizabeth

from base.models import (User, OrganizationType, Organization, Category, Tag,
                         PublicationType, Publication, Comment, PublicationVoice,
                         CommentVoice, UserVoice, Project, InviteType, Invite)

from base.utils import recalculate_users_rating, recalculate_publication_rating, recalculate_comment_rating


class Command(BaseCommand):

    roles = (
        (None, 1),
        ('author', 5),
        ('journalist', 3),
        ('moderator', 2),
        ('admin', 1),
    )

    count_categories = (3, 5,)
    count_tags = (5, 10,)
    count_publications = (1, 5, )
    count_comments = (2, 7, )
    count_voices_publication = (1, 3, )
    count_voices_comment = (1, 3, )
    count_voices_users = (1, 3, )
    count_organization_type = 3
    organizations = 5
    count_publications_per_organization = (1, 3, )
    count_bookmarks_publications = (2, 5)
    count_bookmarks_comments = (1, 3)
    count_followers = (1, 3)
    count_projects = 10
    count_invite_type = 4

    # roles = (
    #     (None, 10),
    #     ('author', 20),
    #     ('journalist', 10),
    #     ('moderator', 5),
    #     ('admin', 3),
    # )
    #
    # count_categories = (5, 10,)
    # count_tags = (15, 25,)
    # count_publications = (3, 5, )
    # count_comments = (5, 10, )
    # count_voices_publication = (0, 7, )
    # count_voices_comment = (0, 7, )
    # count_voices_users = (0, 7, )
    # count_organization_type = 2
    # organizations = 5
    # count_publications_per_organization = (0, 5, )
    # count_bookmarks_publications = (0, 5)
    # count_bookmarks_comments = (0, 5)
    # count_followers = (0, 5)

    def handle(self, *args, **options):
        self.print_success('Start generate data')

        self.generate_groups()
        self.generate_users()
        self.generate_categories()
        self.generate_publication_types()
        self.generate_tags()
        self.generate_publications()
        self.generate_comments()
        self.generate_publication_voices()
        self.generate_comment_voices()
        self.generate_user_voices()
        self.generate_organization_type()
        self.generate_organizations()
        self.generate_organization_publications()
        self.generate_bookmarks_publications()
        self.generate_bookmarks_comments()
        self.generate_followers()
        self.generate_subscribers()
        self.generate_permissions()
        self.generate_projects()
        self.generate_invite_types()
        self.generate_invites()

        self.print_success('Finished generated all data')

    def print_success(self, message):
        self.stdout.write(self.style.SUCCESS(message))

    def print_notice(self, message):
        self.stdout.write(self.style.NOTICE(message))

    def print_warning(self, message):
        self.stdout.write(self.style.WARNING(message))

    def print_error(self, message):
        self.stdout.write(self.style.ERROR(message))

    def get_organizations(self):
        return Organization.objects.all()

    def get_publications(self):
        return Publication.objects.all()

    def get_moderators(self):
        return User.objects.filter(groups__name='moderator')

    def get_authors(self):
        return User.objects.filter(groups__name__in=['author', 'journalist'])

    def get_groups(self):
        return Group.objects.all()

    def get_tags(self):
        return Tag.objects.all()

    def get_categories(self):
        return Category.objects.all()

    def get_publication_types(self):
        return PublicationType.objects.all()

    def generate_groups(self):
        self.print_notice('Start generate groups')
        count = 0
        for count, (role, _) in enumerate(self.roles, 1):
            if not role:
                continue
            Group.objects.create(name=role)
            if count % 100 == 0 and count > 0:
                self.print_success('Generated {} groups'.format(count))
        self.print_success('Successfully generate {} groups'.format(count))

    def generate_users(self):
        self.print_notice('Start generate users')
        person = elizabeth.Personal('ru')
        groups = self.get_groups()
        count = 1
        for role, count_users in self.roles:
            for _ in range(count_users):
                gender = random.choice(['female', 'male'])
                first_name, last_name = person.full_name(gender).split()
                user = User.objects.create_user(
                    username=person.username(gender),
                    email=person.email(gender),
                    first_name=first_name,
                    last_name=last_name
                )
                user.set_password('q1j2t17g')
                user.save()
                if role:
                    group = groups.get(name=role)
                    user.groups.add(group)
                if count % 100 == 0 and count > 0:
                    self.print_success('Generated {} users'.format(count))
                count += 1
        self.print_success('Successfully generate {} users'.format(count))

    def generate_categories(self):
        self.print_notice('Start generate categories')
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        moderators = self.get_moderators()
        count = 0
        for count, _ in enumerate(range(random.randint(*self.count_categories)), 1):
            moderator = random.choice(moderators)
            Category.objects.create(
                title=' '.join(text_en.words(quantity=random.randint(1, 3))).title(),
                slug=text_en.word(),
                description=text_ru.text(quantity=5),
                author=moderator
            )
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} categories'.format(count))
        self.print_success('Successfully generate {} categories'.format(count))

    def generate_publication_types(self):
        self.print_notice('Start generate publication types')
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        moderators = self.get_moderators()
        count = 0
        for count, _ in enumerate(range(self.count_organization_type), 1):
            moderator = random.choice(moderators)
            PublicationType.objects.create(
                title=' '.join(text_en.words(quantity=1)),
                slug=text_en.word(),
                description=text_ru.text(quantity=5),
                author=moderator
            )
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} publication types'.format(count))
        self.print_success('Successfully generate {} publication types'.format(count))

    def generate_tags(self):
        self.print_notice('Start generate tags')
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        moderators = self.get_moderators()
        count = 0
        for count, _ in enumerate(range(random.randint(*self.count_tags)), 1):
            moderator = random.choice(moderators)
            Tag.objects.create(
                title=' '.join(text_en.words(quantity=random.randint(1, 3))).title(),
                slug=text_en.word(),
                description=text_ru.text(quantity=5),
                author=moderator
            )
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} tags'.format(count))
        self.print_success('Successfully generate {} tags'.format(count))

    def generate_publications(self):
        self.print_notice('Start generate publications')
        text = elizabeth.Text('ru')
        authors = self.get_authors()
        types = self.get_publication_types()
        categories = self.get_categories()
        tags = self.get_tags()
        count = 0
        for author in authors:
            for _ in range(random.randint(*self.count_publications)):
                publication = Publication.objects.create(
                    title=text.title(),
                    type=random.choice(types),
                    short_description=text.text(quantity=random.randint(5, 10)),
                    fulltext=text.text(quantity=random.randint(25, 75)),
                    author=author
                )
                cat = {random.choice(categories) for _ in range(random.randint(3, 7))}
                tg = {random.choice(tags) for _ in range(random.randint(3, 7))}
                publication.categories.add(*cat)
                publication.tags.add(*tg)
                if count % 50 == 0 and count > 0:
                    self.print_success('Generated {} publications'.format(count))
                count += 1
        self.print_success('Successfully generate {} publications'.format(count))

    def generate_comments(self):
        self.print_notice('Start generate comments')
        text = elizabeth.Text('ru')
        authors = self.get_authors()
        publications = self.get_publications()
        count = 0
        for publication in publications:
            prev_comment = None
            for _ in range(random.randint(*self.count_comments)):
                comment = Comment.objects.create(
                    comment=text.text(quantity=random.randint(1, 15)),
                    author=random.choice(authors),
                    publication=publication,
                )
                if prev_comment and bool(random.getrandbits(1)):
                    comment.parent = prev_comment
                    comment.save()
                prev_comment = comment
                if count % 50 == 0 and count > 0:
                    self.print_success('Generated {} comments'.format(count))
                count += 1
        self.print_success('Successfully generate {} comments'.format(count))

    def generate_publication_voices(self):
        self.print_notice('Start generate publication\'s voices')
        authors = self.get_authors()
        publications = self.get_publications()
        count = 0
        for publication in publications:
            excluded_authors = authors.filter(~Q(id=publication.author_id))
            for _ in range(random.randint(*self.count_voices_publication)):
                author = random.choice(excluded_authors)
                try:
                    PublicationVoice.objects.get_or_create(
                        voter=author,
                        publication=publication,
                        voice=random.choice([-1, 1])
                    )
                except IntegrityError:
                    pass
                if count % 50 == 0 and count > 0:
                    self.print_success('Generated {} publication\'s voices'.format(count))
                count += 1
        self.print_success('Successfully generate {} publication\'s voices'.format(count))
        self.print_notice('Start recalculate publication\'s voices')
        publications = Publication.objects.all()
        for publication in publications:
            recalculate_publication_rating(publication)
        self.print_notice('Finished recalculate publication\'s voices')

    def generate_comment_voices(self):
        self.print_notice('Start generate comment\'s voices')
        authors = self.get_authors()
        comments = Comment.objects.all()
        count = 0
        for comment in comments:
            excluded_authors = authors.filter(~Q(id=comment.author_id))
            for _ in range(random.randint(*self.count_voices_comment)):
                author = random.choice(excluded_authors)
                try:
                    CommentVoice.objects.get_or_create(
                        voter=author,
                        comment=comment,
                        voice=random.choice([-1, 1])
                    )
                    if count % 50 == 0 and count > 0:
                        self.print_success('Generated {} comment\'s voices'.format(count))
                    count += 1
                except IntegrityError:
                    pass
        self.print_success('Successfully generate {} comment\'s voices'.format(count))
        self.print_notice('Start recalculate comment\'s voices')
        comments = Comment.objects.all()
        for comment in comments:
            recalculate_comment_rating(comment)
        self.print_notice('Finished recalculate comment\'s voices')

    def generate_user_voices(self):
        self.print_notice('Start generate user\'s voices')
        users = voters = self.get_authors()
        count = 0
        for user in users:
            excluded_voters = voters.filter(~Q(id=user.id))
            for _ in range(random.randint(*self.count_voices_users)):
                voter = random.choice(excluded_voters)
                try:
                    UserVoice.objects.get_or_create(
                        voter=voter,
                        user=user,
                        voice=random.choice([-1, 1])
                    )
                except IntegrityError:
                    continue
                if count % 50 == 0 and count > 0:
                    self.print_success('Generated {} user\'s voices'.format(count))
                count += 1
        self.print_success('Successfully generate {} user\'s voices'.format(count))
        self.print_notice('Start recalculate user\'s voices')
        recalculate_users_rating()
        self.print_notice('Finished recalculate user\'s voices')

    def generate_organization_type(self):
        self.print_notice('Start generate organizations types')
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        moderators = self.get_moderators()
        count = 0
        for count, _ in enumerate(range(self.count_organization_type), 1):
            moderator = random.choice(moderators)
            OrganizationType.objects.create(
                title=' '.join(text_en.words(quantity=1)),
                slug=text_en.word(),
                description=text_ru.text(quantity=5),
                author=moderator
            )
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} organizations types'.format(count))
        self.print_success('Successfully generate {} organizations types'.format(count))

    def generate_organizations(self):
        self.print_notice('Start generate organizations')
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        users = self.get_authors()[:self.organizations]
        types = OrganizationType.objects.all()
        prev_organization = None
        count = 0
        for count, user in enumerate(users, 1):
            organization = Organization.objects.create(
                title=text_ru.title(),
                type=random.choice(types),
                slug=text_en.word(),
                description=text_ru.text(quantity=5),
                founder=user,
            )
            organization.employee.add(user)
            organization.save()
            if prev_organization and bool(random.getrandbits(1)):
                organization.parent = prev_organization
                organization.save()
            prev_organization = organization
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} organizations'.format(count))
        self.print_success('Successfully generate {} organizations'.format(count))

    def generate_organization_publications(self):
        self.print_notice('Start generate organization\'s publications')
        organizations = self.get_organizations()
        count = 0
        for count, organization in enumerate(organizations, 1):
            for count_publication in range(random.randint(*self.count_publications_per_organization)):
                authors = User.objects.filter(organizations=organization)
                author = random.choice(authors)
                publications = author.publications.all()
                publication = random.choice(publications)
                organization.publications.add(publication)
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} organization\'s publications'.format(count))
        self.print_success('Successfully generate {} organization\'s publications'.format(count))

    def generate_bookmarks_publications(self):
        self.print_notice('Start generate bookmarks publications')
        authors = self.get_authors()
        count = 0
        for author in authors:
            publications = Publication.objects.exclude(author=author)
            pubs = [random.choice(publications) for _ in range(random.randint(*self.count_bookmarks_publications))]
            author.publication_bookmark.add(*pubs)
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} bookmarks publications'.format(count))
            count += 1
        self.print_success('Successfully generate {} bookmarks publications'.format(count))

    def generate_bookmarks_comments(self):
        self.print_notice('Start generate bookmarks comments')
        authors = self.get_authors()
        count = 0
        for author in authors:
            comments = Comment.objects.exclude(author=author)
            cmms = [random.choice(comments) for _ in range(random.randint(*self.count_bookmarks_comments))]
            author.comment_bookmark.add(*cmms)
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} bookmarks comments'.format(count))
            count += 1
        self.print_success('Successfully generate {} bookmarks comments'.format(count))

    def generate_followers(self):
        self.print_notice('Start generate followers')
        authors = self.get_authors()
        count = 0
        for count, author in enumerate(authors, 1):
            users = User.objects.exclude(id=author.id)
            followers = [random.choice(users) for _ in range(random.randint(*self.count_followers))]
            author.follower.add(*followers)
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} followers'.format(count))
        self.print_success('Successfully generate {} followers'.format(count))

    def generate_subscribers(self):
        self.print_notice('Start generate subscribers')
        organizations = self.get_organizations()
        count = 0
        for count, organization in enumerate(organizations, 1):
            users = User.objects.all()
            subscribers = [random.choice(users) for _ in range(random.randint(*self.count_followers))]
            organization.subscriber.add(*subscribers)
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} subscribers'.format(count))
        self.print_success('Successfully generate {} subscribers'.format(count))

    def generate_permissions(self):
        self.print_notice('Start adding permissions to authors')
        user_permissions = self.get_author_permissions()
        authors = self.get_authors()
        for author in authors:
            author.user_permissions.set(user_permissions)
        self.print_success('Successfully added permissions to authors')

    @staticmethod
    def get_author_permissions():
        user_permissions = []

        permissions = Permission.objects.all()

        publication_permissions = [permission for permission in permissions if permission.codename.endswith('publication')]
        comment_permissions = [permission for permission in permissions if permission.codename.endswith('comment')]
        publicationvoice_permissions = [permission for permission in permissions if permission.codename.endswith('publicationvoice')]
        commentvoice_permissions = [permission for permission in permissions if permission.codename.endswith('commentvoice')]
        uservoice_permissions = [permission for permission in permissions if permission.codename.endswith('uservoice')]
        organization_permissions = [permission for permission in permissions if permission.codename.endswith('organization')]

        user_permissions.extend(publication_permissions)
        user_permissions.extend(comment_permissions)
        user_permissions.extend([pvp for pvp in publicationvoice_permissions if pvp.codename.startswith('add') or pvp.codename.startswith('change')])
        user_permissions.extend([cvp for cvp in commentvoice_permissions if cvp.codename.startswith('add') or cvp.codename.startswith('change')])
        user_permissions.extend([uvp for uvp in uservoice_permissions if uvp.codename.startswith('add') or uvp.codename.startswith('change')])
        user_permissions.extend(organization_permissions)

        return user_permissions

    def generate_projects(self):
        self.print_notice('Start generate projects')
        users = self.get_authors()
        organizations = Organization.objects.all()
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        count = 0
        for count in range(self.count_projects):
            queryset = random.choice([organizations, users])
            founder = random.choice(queryset)
            Project.objects.create(
                founder=founder,
                title=text_ru.title(),
                slug=text_en.word(),
                short_description=text_ru.text(quantity=random.randint(5, 10)),
                fulltext=text_ru.text(quantity=random.randint(25, 75)),
            )
        self.print_success('Successfully generate {} followers'.format(count))

    def generate_invite_types(self):
        self.print_notice('Start generate invite\'s types')
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        moderators = self.get_moderators()
        count = 0
        for count, _ in enumerate(range(self.count_invite_type), 1):
            moderator = random.choice(moderators)
            InviteType.objects.create(
                title=' '.join(text_en.words(quantity=random.randint(1, 3))),
                slug=text_en.word(),
                description=text_ru.text(quantity=5),
                author=moderator
            )
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} invite\'s types'.format(count))
        self.print_success('Successfully generate {} invite\'s types'.format(count))

    def generate_invites(self):
        pass

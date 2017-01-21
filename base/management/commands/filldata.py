import random

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import elizabeth

from base.models import (User, OrganisationType, Organisation, UserProfile, Category, Tag,
                         PublicationType, Blog, Publication, Comment, PublicationVoice,
                         CommentVoice, UserVoice)


class Command(BaseCommand):

    roles = (
        (None, 1),
        ('author', 7),
        ('journalist', 3),
        ('moderator', 2),
        ('admin', 1),
    )

    count_categories = (3, 5,)
    count_tags = (10, 25,)
    count_publications = (1, 3, )
    count_comments = (2, 5, )
    count_voices_publication = (1, 3, )
    count_voices_comment = (1, 3, )
    count_voices_users = (1, 3, )
    count_organisation_type = 3
    organisations = 5
    count_publications_per_organisation = (1, 3, )
    count_bookmarks_publications = (2, 5)
    count_bookmarks_comments = (1, 3)
    count_followers = (1, 3)

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
    # count_organisation_type = 2
    # organisations = 5
    # count_publications_per_organisation = (0, 5, )
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
        self.generate_organisation_type()
        self.generate_organisations()
        self.generate_blogs()
        self.generate_blog_publications()
        self.generate_bookmarks_publications()
        self.generate_bookmarks_comments()
        self.generate_followers()
        self.generate_subscribers()

        self.print_success('Finished generated all data')

    def print_success(self, message):
        self.stdout.write(self.style.SUCCESS(message))

    def print_notice(self, message):
        self.stdout.write(self.style.NOTICE(message))

    def print_warning(self, message):
        self.stdout.write(self.style.WARNING(message))

    def print_error(self, message):
        self.stdout.write(self.style.ERROR(message))

    def get_organisations(self):
        return Organisation.objects.all()

    def get_publications(self):
        return Publication.objects.all()

    def get_moderators(self):
        return User.objects.filter(groups__name='moderator')

    def get_blogs(self):
        return Blog.objects.all()

    def get_authors(self):
        return User.objects.filter(groups__name='author')

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
                    password='q1j2t17g',
                    first_name=first_name,
                    last_name=last_name
                )
                UserProfile.objects.create(
                    user=user
                )
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
        for count, _ in enumerate(range(self.count_organisation_type), 1):
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
            publications_voices = publication.publications_voices.all()
            publications_voices.values_list('voice', flat=True)
            publication.rating = sum(publications_voices.values_list('voice', flat=True))
            publication.save()
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
            comments_voices = comment.comments_voices.all()
            comments_voices.values_list('voice', flat=True)
            comment.rating = sum(comments_voices.values_list('voice', flat=True))
            comment.save()
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
        users = User.objects.all()
        for user in users:
            try:
                user_voters_voices = user.voters_voices.all()
                user_profile = user.userprofile
                user_profile.authority = sum(user_voters_voices.values_list('voice', flat=True))
                user_profile.save()
            except ObjectDoesNotExist:
                pass
        self.print_notice('Finished recalculate user\'s voices')

    def generate_organisation_type(self):
        self.print_notice('Start generate organisations types')
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        moderators = self.get_moderators()
        count = 0
        for count, _ in enumerate(range(self.count_organisation_type), 1):
            moderator = random.choice(moderators)
            OrganisationType.objects.create(
                title=' '.join(text_en.words(quantity=1)),
                slug=text_en.word(),
                description=text_ru.text(quantity=5),
                author=moderator
            )
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} organisations types'.format(count))
        self.print_success('Successfully generate {} organisations types'.format(count))

    def generate_organisations(self):
        self.print_notice('Start generate organisations')
        text_ru = elizabeth.Text('ru')
        text_en = elizabeth.Text('en')
        users = self.get_authors()[:self.organisations]
        types = OrganisationType.objects.all()
        prev_organisation = None
        count = 0
        for count, user in enumerate(users, 1):
            organisation = Organisation.objects.create(
                title=text_ru.title(),
                type=random.choice(types),
                slug=text_en.word(),
                description=text_ru.text(quantity=5),
                founder=user,
            )
            organisation.employee.add(user)
            organisation.save()
            if prev_organisation and bool(random.getrandbits(1)):
                organisation.parent = prev_organisation
                organisation.save()
            prev_organisation = organisation
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} organisations'.format(count))
        self.print_success('Successfully generate {} organisations'.format(count))

    def generate_blogs(self):
        self.print_notice('Start generate blogs')
        organisations = self.get_organisations()
        count = 0
        for count, organisation in enumerate(organisations, 1):
            Blog.objects.create(
                organisation=organisation
            )
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} blogs'.format(count))
        self.print_success('Successfully generate {} blogs'.format(count))

    def generate_blog_publications(self):
        self.print_notice('Start generate blog\'s publications')
        blogs = self.get_blogs()
        count = 0
        for count, blog in enumerate(blogs, 1):
            for count_publication in range(random.randint(*self.count_publications_per_organisation)):
                authors = User.objects.filter(organisations=blog.organisation)
                author = random.choice(authors)
                publications = author.publications.all()
                publication = random.choice(publications)
                publication.blog = blog
                publication.save()
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} blog\'s publications'.format(count))
        self.print_success('Successfully generate {} blogs publications'.format(count))

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
        organisations = self.get_organisations()
        count = 0
        for count, organisation in enumerate(organisations, 1):
            users = User.objects.all()
            subscribers = [random.choice(users) for _ in range(random.randint(*self.count_followers))]
            organisation.subscriber.add(*subscribers)
            if count % 50 == 0 and count > 0:
                self.print_success('Generated {} subscribers'.format(count))
        self.print_success('Successfully generate {} subscribers'.format(count))

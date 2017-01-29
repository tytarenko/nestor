from django.contrib import admin
from .models import (User, OrganizationType, Organization, Category, Tag,
                     PublicationType, Publication, Comment, UserRegistrationCode,
                     Invite, Project)

admin.site.register(User)
admin.site.register(OrganizationType)
admin.site.register(Organization)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(PublicationType)
admin.site.register(Publication)
admin.site.register(Comment)
admin.site.register(UserRegistrationCode)
admin.site.register(Invite)
admin.site.register(Project)

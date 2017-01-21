from django.contrib import admin
from .models import (User, OrganisationType, Organisation, UserProfile, Category, Tag,
                     PublicationType, Blog, Publication, Comment,)

admin.site.register(User)
admin.site.register(OrganisationType)
admin.site.register(Organisation)
admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(PublicationType)
admin.site.register(Blog)
admin.site.register(Publication)
admin.site.register(Comment)

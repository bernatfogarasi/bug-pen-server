from django.contrib import admin
from bug_tracker import models
import django.contrib.auth.models as default

admin.site.register(
    [
        models.Assignment,
        models.Bug,
        models.Mark,
        models.Membership,
        models.Project,
        models.Tag,
        models.User,
    ]
)

admin.site.unregister([default.User, default.Group])

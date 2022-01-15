from django.contrib import admin

from bug_tracker import models

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

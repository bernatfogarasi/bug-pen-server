from django.urls import path
from . import views

urlpatterns = [
    path("project-create", views.project_create),
    path("projects-my", views.projects_my),
    path("project-get", views.project_get),
    path("project-edit", views.project_edit),
    path("bug-report", views.bug_report),
    path("bug-edit", views.bug_edit),
    path("memberships-count", views.memberships_count),
    path("profiles-search", views.profiles_search),
    path("profile-get", views.profile_get),
    path("member-add", views.member_add),
    path("member-remove", views.member_remove),
    path("member-authorize", views.member_authorize),
    path("me", views.me),
    path("tag-create", views.tag_create),
    path("tag-remove", views.tag_remove),
    path("tag-add", views.tag_add),
    path("mark-remove", views.mark_remove),
    path("assign", views.assign),
    path("assign-remove", views.assign_remove),
    path("attach", views.attach),
    path("attachment-get", views.attachment_get),
    path("attachment-remove", views.attachment_remove),
]

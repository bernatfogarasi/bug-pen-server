from django.urls import path
from . import views

urlpatterns = [
    path("project-create", views.project_create),
    path("projects-my", views.projects_my),
    path("project-get", views.project_get),
    path("bug-report", views.bug_report),
    path("memberships-count", views.memberships_count),
    path("profiles-search", views.profiles_search),
    path("profile-get", views.profile_get),
    path("member-add", views.member_add),
    path("member-remove", views.member_remove),
    path("member-authorize", views.member_authorize),
    path("me", views.me),
]

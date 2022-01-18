from django.urls import path
from . import views

urlpatterns = [
    path("project-create/", views.project_create),
    path("projects-my/", views.projects_my),
    path("project-get/", views.project_get),
    path("bug-report", views.bug_report),
    path("memberships-count/", views.memberships_count),
]

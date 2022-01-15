from django.urls import path
from . import views

urlpatterns = [
    path("project-create/", views.project_create),
    path("projects-my/", views.projects_my),
]

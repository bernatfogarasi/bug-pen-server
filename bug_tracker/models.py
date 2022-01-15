from django.db import models
from django.contrib.auth.models import User


class User(models.Model):
    userId = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.userId


class Project(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title


class Membership(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.project.title


class Bug(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title


class Assignment(models.Model):  # Assigning a bug to a member
    date_created = models.DateTimeField(auto_now_add=True)
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.bug.title


class Tag(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    style = models.TextField(max_length=1000)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title


class Mark(models.Model):  # Marking a bug with a tag
    date_created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.bug.title


# class Change(models.Model):
#     date_created = models.DateTimeField(auto_now_add=True)
#     title = models.CharField(max_length=200)
#     description = models.TextField(max_length=1000)
#     creator = models.ForeignKey(User, on_delete=models.CASCADE)
#     bug = models.ForeignKey(Bug, on_delete=models.CASCADE, blank=True, null=True)

#     def __str__(self) -> str:
#         return self.title

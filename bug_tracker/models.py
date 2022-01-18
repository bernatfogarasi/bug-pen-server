from django.db import models
from django.contrib.auth.models import User
import string
import random
from django.core.validators import MaxValueValidator, MinValueValidator


def generate_id(
    length=10,
    characters=string.ascii_uppercase + string.digits,
):
    return "".join(random.choice(characters) for _ in range(length))


class User(models.Model):
    user_id = models.CharField(max_length=200, unique=True)
    email = models.EmailField()
    email_verified = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    locale = models.CharField(max_length=20, default="en")
    picture = models.URLField()

    def __str__(self) -> str:
        return self.user_id


class Project(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="projects_created"
    )
    bug_index = models.IntegerField(default=0)
    project_id = models.CharField(max_length=10, null=True, blank=True, unique=True)

    def save(self):
        while (
            not self.project_id
            or Project.objects.filter(project_id=self.project_id).exists()
        ):
            self.project_id = generate_id(length=10)
        return super(Project, self).save()

    def __str__(self) -> str:
        return self.title


class Membership(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="memberships"
    )

    def __str__(self) -> str:
        return self.project.title


class Bug(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    index = models.IntegerField()
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bugs")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="bugs")
    reproducible = models.BooleanField(default=True)
    impact = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=3
    )
    urgency = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=3
    )

    """
    class Scale(models.TextChoices):
        VERY_HIGH = "very high"
        HIGH = "high"
        MEDIUM = "medium"
        LOW = "low"
        VERY_LOW = "very low"

    impact = models.CharField(choices=Scale, default=Scale.MEDIUM)
    urgency = models.CharField(choices=Scale, default=Scale.MEDIUM)
    """

    def __str__(self) -> str:
        return self.title


class Assignment(models.Model):  # Assigning a bug to a member
    date_created = models.DateTimeField(auto_now_add=True)
    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="assignments"
    )
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name="assignments")

    def __str__(self) -> str:
        return self.bug.title


class Tag(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    style = models.TextField(max_length=1000)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")

    def __str__(self) -> str:
        return self.title


class Mark(models.Model):  # Marking a bug with a tag
    date_created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="marks")
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name="marks")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="marks")

    def __str__(self) -> str:
        return self.bug.title


class Attachment(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name="attachments")
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="attachments"
    )

    def __str__(self) -> str:
        return self.title


# class Change(models.Model):
#     date_created = models.DateTimeField(auto_now_add=True)
#     title = models.CharField(max_length=200)
#     description = models.TextField(max_length=1000)
#     creator = models.ForeignKey(User, on_delete=models.CASCADE)
#     bug = models.ForeignKey(Bug, on_delete=models.CASCADE, blank=True, null=True)

#     def __str__(self) -> str:
#         return self.title

from django.http import JsonResponse, HttpResponseServerError, HttpResponse
from .models import Membership, Project


def project_create(request):
    if request.method == "POST":
        try:
            project = Project(creator=request.user, **request.data)
            project.save()
        except Exception as error:
            print("ERROR", error)
            return HttpResponseServerError("could not save project")
        try:
            membership = Membership(user=request.user, project=project)
            membership.save()
        except Exception as error:
            print("ERROR", error)
            return HttpResponseServerError("could not save membership")

        return HttpResponse()


def projects_my(request):
    if request.method == "GET":
        try:
            memberships = Membership.objects.filter(user=request.user)
            memberships = list(memberships)
            projects = map(
                lambda membership: {"title": membership.project.title}, memberships
            )
        except Exception as error:
            print("ERROR", error)
            return HttpResponseServerError("could not get memberships")
        return JsonResponse({"data": [*projects]})

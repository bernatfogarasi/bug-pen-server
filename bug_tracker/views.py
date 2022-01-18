from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseServerError,
)
from .models import Bug, Membership, Project
from django.shortcuts import redirect
from django.db.models import Max


def printError(*args, **kwargs):
    print("ERROR", *args, **kwargs)


def getUser(user):
    return {
        "id": user.id,
        "name": f"{user.first_name} {user.last_name}",
        "firstName": user.first_name,
        "lastName": user.last_name,
    }


def getAttachment(attachment):
    return {
        "id": attachment.id,
        "title": attachment.title,
        "createdAt": attachment.date_created,
    }


def getBug(bug):
    return {
        "id": bug.id,
        "index": bug.index,
        "title": bug.title,
        "description": bug.description,
        "reporter": getUser(bug.reporter),
        "createdAt": bug.date_created,
        "updatedAt": bug.date_modified,
        "reproducible": bug.reproducible,
        "impact": bug.impact,
        "urgency": bug.urgency,
        "attachments": [
            getAttachment(attachment) for attachment in bug.attachments.all()
        ],
    }


def getProject(project):
    return {
        "id": project.id,
        "projectId": project.project_id,
        "title": project.title,
        "createdAt": project.date_created,
        "updatedAt": project.date_modified,
        "creator": getUser(project.creator),
        "bugs": [getBug(bug) for bug in project.bugs.all()],
        "members": [
            getUser(membership.user) for membership in project.memberships.all()
        ],
    }


def project_create(request):
    if request.method == "POST":
        try:
            project = Project(creator=request.user, **request.data)
            project.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not save project")

        try:
            membership = Membership(user=request.user, project=project)
            membership.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not save membership")

        return redirect("/projects-my")


def projects_my(request):
    if request.method == "GET":
        try:
            memberships = Membership.objects.filter(user=request.user)
            memberships = list(memberships)
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not get memberships")

        try:
            projects = map(
                lambda membership: {
                    "id": membership.project.id,
                    "title": membership.project.title,
                    "projectId": membership.project.project_id,
                },
                memberships,
            )
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not get projects")

        return JsonResponse({"projects": [*projects]})


def project_get(request):
    if request.method == "GET":
        try:
            project_id = request.GET["projectId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("projectId not found")

        try:
            membership = Membership.objects.filter(
                user=request.user, project__project_id=project_id
            ).first()
            if not membership:
                raise Exception("membership is None")
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("membership not found")

        try:
            project = getProject(membership.project)
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not get project")

        return JsonResponse({"project": project})


def memberships_count(request):
    if request.method == "GET":
        try:
            count = len(Membership.objects.all())
        except Exception as error:
            HttpResponseServerError("could not count members")

        return JsonResponse({"membershipCount": count})


def bug_report(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("projectId not found")

        try:
            membership = Membership.objects.filter(
                user=request.user, project__project_id=project_id
            ).first()
            if not membership:
                raise Exception("membership is None")
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("membership not found")

        try:
            project = membership.project
            project.bug_index += 1
            bug = Bug(
                index=project.bug_index,
                reporter=request.user,
                project=membership.project,
                **request.data,
            )
            bug.save()
            project.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not save bug or project")

        return redirect(f"/project-get?projectId={project_id}")

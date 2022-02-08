from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
    JsonResponse,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseServerError,
)
from .models import Bug, Membership, Project, User
from django.shortcuts import redirect
from django.db.models import Q, Max


def printError(*args, **kwargs):
    print("ERROR", *args, **kwargs)


def getUser(user):
    return {
        "id": user.id,
        "userId": user.user_id,
        "name": f"{user.first_name} {user.last_name}",
        "firstName": user.first_name,
        "lastName": user.last_name,
        "picture": user.picture,
        "membershipsCount": len(user.memberships.all()),
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
            {
                "authorization": membership.get_authorization_display(),
                **getUser(membership.user),
            }
            for membership in project.memberships.all()
        ],
    }


def me(request):
    if request.method == "GET":
        me = {"userId": request.user.user_id}
        return JsonResponse({"me": me})


def project_create(request):
    if request.method == "POST":
        try:
            project = Project(creator=request.user, **request.data)
            project.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not save project")

        try:
            membership = Membership(
                user=request.user, authorization="ADM", project=project
            )
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
            projects = [
                {
                    "id": membership.project.id,
                    "title": membership.project.title,
                    "projectId": membership.project.project_id,
                    "authorization": membership.get_authorization_display(),
                    "memberCount": len(membership.project.memberships.all()),
                }
                for membership in memberships
            ]
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not get projects")

        return JsonResponse({"projects": projects})


def project_get(request):
    if request.method == "GET":
        try:
            project_id = request.GET["projectId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("projectId not specified")

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
            project = {
                "authorization": membership.get_authorization_display(),
                **getProject(membership.project),
            }
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

        return JsonResponse({"membershipsCount": count})


def bug_report(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("projectId not specified")

        try:
            membership = Membership.objects.filter(
                user=request.user, project__project_id=project_id
            ).first()
            if not membership:
                raise Exception("membership is None")
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("membership not found")

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


def profiles_search(request):
    if request.method == "GET":
        try:
            text = request.GET["text"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("search text not specified")

        try:
            # https://stackoverflow.com/a/17361729/15371114
            users = User.objects.all()
            for word in text.split():
                users = users.filter(
                    Q(first_name__contains=word) | Q(last_name__contains=word)
                )
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not search")

        try:
            profiles = [getUser(user) for user in users[:10]]
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not get users")

        return JsonResponse({"profiles": profiles})


def profile_get(request):
    if request.method == "GET":
        try:
            user_id = request.GET["userId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("userId not specified")

        try:
            user = User.objects.filter(user_id=user_id).first()
            if not user:
                raise Exception("user is None")
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("user not found")

        try:
            profile = getUser(user)
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not get profile")

        return JsonResponse({"profile": profile})


def member_add(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("projectId not specified")

        try:
            user_id = request.GET["userId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("userId not specified")

        try:
            project = Project.objects.filter(project_id=project_id).first()
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("project not found")

        try:
            user = User.objects.filter(user_id=user_id).first()
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("user not found")

        try:
            membership_requester = Membership.objects.filter(
                user=request.user, project=project
            ).first()
            if not membership_requester:
                raise Exception("requester membership not found")
            if membership_requester.authorization not in ["ADM", "DIR"]:
                raise Exception("authorization not sufficient")
            membership_subject = Membership.objects.filter(user=user, project=project)
            if membership_subject:
                raise Exception("subject membership already exists")
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("not authorized")

        try:
            membership = Membership(user=user, project=project, authorization="SPE")
            membership.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not create membership")

        return JsonResponse({})


def member_remove(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("projectId not specified")

        try:
            user_id = request.GET["userId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("userId not specified")

        # try:
        #     if request.user_id == user_id:
        #         raise Exception("cannot remove self")
        # except Exception as error:
        #     return HttpResponseForbidden("cannot remove self")

        try:
            project = Project.objects.filter(project_id=project_id).first()
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("project not found")

        try:
            user = User.objects.filter(user_id=user_id).first()
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("user not found")

        try:
            membership_subject = Membership.objects.filter(user=user, project=project)
            if not membership_subject:
                raise Exception("subject membership not found")
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("subject membership not found")

        try:
            membership_requester = Membership.objects.filter(
                user=request.user, project=project
            ).first()
            if not membership_requester:
                raise Exception("requester membership not found")
            if membership_requester.authorization not in ["ADM", "DIR"] or (
                membership_requester.authorization == "DIR"
                and membership_subject.authorization in ["ADM", "DIR"]
            ):
                raise Exception("authorization not sufficient")
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("not authorized")

        try:
            membership_subject.delete()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not delete membership")

        return redirect(f"/project-get?projectId={project_id}")


def member_authorize(request):
    if request.method == "POST":
        try:
            user_id = request.GET["userId"]
            project_id = request.GET["projectId"]
            authorization = request.GET["authorization"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        # try:
        #     user = User.objects.filter(user_id=user_id).first()
        #     if not user:
        #         raise Exception("subject not found")
        # except Exception as error:
        #     printError(error)
        #     return HttpResponseNotFound("subject not found")

        try:
            membership_requester = Membership.objects.filter(user=request.user).first()
            if not membership_requester:
                raise Exception("requester not member")
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("requester not member")

        try:
            membership_subject = Membership.objects.filter(
                user__user_id=user_id, project__project_id=project_id
            ).first()
            if not membership_subject:
                raise Exception("subject not member")
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("subject not member")

        convert = {
            "Administrator": "ADM",
            "Director": "DIR",
            "Contributor": "CON",
            "Spectator": "SPE",
        }

        allowed = {
            "ADM": {
                "ADM": ["DIR", "CON", "SPE"],
                "DIR": ["ADM", "CON", "SPE"],
                "CON": ["ADM", "DIR", "SPE"],
                "SPE": ["ADM", "DIR", "CON"],
            },
            "DIR": {"CON": ["SPE"], "SPE": ["CON"]},
        }

        try:
            print(
                membership_requester.authorization,
                membership_subject.authorization,
                authorization,
            )
            if not (
                membership_requester.authorization in allowed
                and membership_subject.authorization
                in allowed[membership_requester.authorization]
                and convert[authorization]
                in allowed[membership_requester.authorization][
                    membership_subject.authorization
                ]
            ):
                raise Exception("not authorized")
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("not authorized")

        try:
            membership_subject.authorization = convert[authorization]
            membership_subject.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not save")

        return redirect(f"/project-get?projectId={project_id}")

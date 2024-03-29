import random
import string

from django.db.models import Max, Q
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import redirect

from .models import Assignment, Attachment, Bug, Mark, Membership, Project, Tag, User


def generate_id(
    length=10,
    characters=string.ascii_uppercase + string.digits,
):
    return "".join(random.choice(characters) for _ in range(length))


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
        "size": attachment.size,
        "contentType": attachment.content_type,
        "creator": getUser(attachment.creator),
        "createdAt": attachment.date_created,
    }


def getTag(tag):
    return {
        "id": tag.id,
        "createdAt": tag.date_created,
        "creator": getUser(tag.creator),
        "title": tag.title,
        "textColor": tag.text_color,
        "backgroundColor": tag.background_color,
        "borderColor": tag.border_color,
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
        "tags": [getTag(mark.tag) for mark in bug.marks.all()],
        "attachments": [
            getAttachment(attachment) for attachment in bug.attachments.all()
        ],
        "assignees": [
            getUser(assignment.membership.user) for assignment in bug.assignments.all()
        ],
    }


def getProject(project):
    return {
        "id": project.id,
        "projectId": project.project_id,
        "title": project.title,
        "description": project.description,
        "createdAt": project.date_created,
        "updatedAt": project.date_modified,
        "creator": getUser(project.creator),
        "bugs": [getBug(bug) for bug in project.bugs.all()],
        "tags": [getTag(tag) for tag in project.tags.all()],
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
            project_id = None
            while (
                not project_id or Project.objects.filter(project_id=project_id).exists()
            ):
                project_id = generate_id(length=10)
            project = Project(
                creator=request.user, project_id=project_id, **request.data
            )
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
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
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
            count = len(User.objects.all())
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
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
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
            user = User.objects.get(user_id=user_id)
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
            membership_requester = Membership.objects.get(
                user=request.user, project=project
            )
            if membership_requester.authorization not in ["ADM", "DIR"]:
                raise Exception("authorization not sufficient")
            membership_subject = Membership.objects.filter(
                user=user, project=project
            ).exists()
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
            user_id = request.GET["userId"]
        except Exception as error:
            printError(error)
            return HttpResponseForbidden("parameter not specified")

        try:
            membership_subject = Membership.objects.get(
                user__user_id=user_id, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("subject membership not found")

        try:
            membership_requester = membership_subject.project.memberships.get(
                user=request.user
            )
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

        try:
            membership_requester = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("requester not member")

        try:
            membership_subject = membership_requester.project.memberships.get(
                user__user_id=user_id
            )
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


def tag_create(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            parameters = {
                "title": request.data["title"],
                "text_color": request.data["textColor"],
                "border_color": request.data["borderColor"],
                "background_color": request.data["backgroundColor"],
            }
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("bad body")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            tag = Tag.objects.filter(project=membership.project, **parameters).exists()
            if tag:
                raise Exception("tag already exists")
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("tag already exists")

        try:
            tag = Tag(project=membership.project, creator=membership.user, **parameters)
            tag.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not save")

        return redirect(f"/project-get?projectId={project_id}")


def tag_remove(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
            tag_id = request.GET["tagId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            tag = membership.project.tags.get(id=tag_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("tag not found")

        try:
            tag.delete()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not delete")

        return redirect(f"/project-get?projectId={project_id}")


def project_edit(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            changes = {}
            for key in ["title", "description"]:
                if key in request.data:
                    changes[key] = request.data[key]
            if not changes:
                raise Exception("changes not found")
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("changes not found")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            membership.project.update(**changes)
            membership.project.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could update")

        return redirect(f"/project-get?projectId={project_id}")


def bug_edit(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
            bug_id = request.GET["bugId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            changes = {}
            for key in ["title", "description", "reproducible", "impact", "urgency"]:
                if key in request.data:
                    changes[key] = request.data[key]
            print(changes)
            if not changes:
                raise Exception("changes not found")
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("changes not found")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            bug = membership.project.bugs.get(id=bug_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("bug not found")

        try:
            bug.update(**changes)
            bug.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could update")

        return redirect(f"/project-get?projectId={project_id}")


def tag_add(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
            bug_id = request.GET["bugId"]
            tag_id = request.GET["tagId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            bug = membership.project.bugs.get(id=bug_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("bug not found")

        try:
            tag = membership.project.tags.get(id=tag_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("tag not found")

        try:
            mark = bug.marks.filter(tag=tag).first()
            if mark:
                return HttpResponseNotAllowed("tag already added")
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("tag already added")

        try:
            mark = Mark(creator=request.user, bug=bug, tag=tag)
            mark.save()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not save mark")

        return redirect(f"/project-get?projectId={project_id}")


def mark_remove(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
            bug_id = request.GET["bugId"]
            tag_id = request.GET["tagId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            bug = membership.project.bugs.get(id=bug_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("bug not found")

        try:
            tag = membership.project.tags.get(id=tag_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("tag not found")

        try:
            mark = bug.marks.get(tag=tag)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("mark not found")

        try:
            mark.delete()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not delete mark")

        return redirect(f"/project-get?projectId={project_id}")


def assign(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
            bug_id = request.GET["bugId"]
            user_id = request.GET["userId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            membership_requester = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("requester not member")

        try:
            membership_subject = membership_requester.project.memberships.get(
                user__user_id=user_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("subject not member")

        try:
            bug = membership_requester.project.bugs.get(id=bug_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("bug not found")

        try:
            assignment = bug.assignments.filter(membership=membership_subject).first()
            if assignment:
                return HttpResponseNotAllowed("already assigned")
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("already assigned")

        try:
            assignment = Assignment(membership=membership_subject, bug=bug)
            assignment.save()
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("could not save assignment")

        return redirect(f"/project-get?projectId={project_id}")


def assign_remove(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
            bug_id = request.GET["bugId"]
            user_id = request.GET["userId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            membership_requester = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("requester not member")

        try:
            membership_subject = membership_requester.project.memberships.get(
                user__user_id=user_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("subject not member")

        try:
            bug = membership_requester.project.bugs.get(id=bug_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("bug not found")

        try:
            assignment = bug.assignments.get(membership=membership_subject)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("could not find assignment")

        try:
            assignment.delete()
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("could not remove assignment")

        return redirect(f"/project-get?projectId={project_id}")


def attach(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
            bug_id = request.GET["bugId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            bug = membership.project.bugs.get(id=bug_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("bug not found")

        try:
            for file in request.FILES.values():
                attachment = Attachment(
                    bug=bug,
                    creator=request.user,
                    title=file.name,
                    file=file,
                    content_type=file.content_type,
                    size=file.size,
                )
                attachment.save()
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("could not process files")

        return redirect(f"/project-get?projectId={project_id}")


def attachment_get(request):
    if request.method == "GET":
        try:
            project_id = request.GET["projectId"]
            bug_id = request.GET["bugId"]
            attachment_id = request.GET["attachmentId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            bug = membership.project.bugs.get(id=bug_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("bug not found")

        try:
            attachment = bug.attachments.get(id=attachment_id)
            file = attachment.file
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("attachment not found")

        try:
            response = HttpResponse(
                attachment.file, content_type=attachment.content_type
            )
            response[
                "Content-Disposition"
            ] = f'attachment; filename="{attachment.title}";'

        except Exception as error:
            printError(error)
            return HttpResponseNotFound("attachment not found")

        return response


def attachment_remove(request):
    if request.method == "POST":
        try:
            project_id = request.GET["projectId"]
            bug_id = request.GET["bugId"]
            attachment_id = request.GET["attachmentId"]
        except Exception as error:
            printError(error)
            return HttpResponseBadRequest("parameter not found")

        try:
            membership = Membership.objects.get(
                user=request.user, project__project_id=project_id
            )
        except Exception as error:
            printError(error)
            return HttpResponseNotAllowed("not member")

        try:
            bug = membership.project.bugs.get(id=bug_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("bug not found")

        try:
            attachment = bug.attachments.get(id=attachment_id)
        except Exception as error:
            printError(error)
            return HttpResponseNotFound("attachment not found")

        try:
            attachment.file.delete()
            attachment.delete()
        except Exception as error:
            printError(error)
            return HttpResponseServerError("could not delete attachment")

        return redirect(f"/project-get?projectId={project_id}")

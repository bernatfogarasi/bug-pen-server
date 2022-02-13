from pprint import pprint
from django.conf import settings
from django.http import HttpResponseServerError, JsonResponse, HttpResponseForbidden

from bug_tracker.views import printError
from .models import User
import json
import jwt
import requests
import string
import random


def public(request):
    return (
        request.path.startswith("/admin")
        or request.path.startswith("/favicon.ico")
        or request.path.startswith("/memberships-count")
    )


def generate_id(
    length=10,
    characters=string.ascii_uppercase + string.digits,
):
    return "".join(random.choice(characters) for _ in range(length))


class Authenticate:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if public(request):
            return self.get_response(request)

        DOMAIN = "dev-su34m38a.us.auth0.com"
        ISSUER = f"https://{DOMAIN}/"
        AUDIENCE = settings.ORIGIN
        ALGORITHM = "RS256"
        JWKS_URL = f"{ISSUER}.well-known/jwks.json"

        try:
            authorization = request.headers.get("Authorization")
            request.token = authorization.split()[1]
        except Exception as error:
            print("ERROR", error)
            return HttpResponseForbidden("token not found")

        try:
            header = jwt.get_unverified_header(request.token)
            jwks = requests.get(JWKS_URL).json()
            for jwk in jwks["keys"]:
                if jwk["kid"] == header["kid"]:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            request.payload = jwt.decode(
                request.token,
                public_key,
                audience=AUDIENCE,
                issuer=ISSUER,
                algorithms=[ALGORITHM],
            )
            request.auth_id = request.payload["sub"]
        except Exception as error:
            print("ERROR", error)
            return HttpResponseForbidden("token not valid")

        try:
            request.user_info = requests.get(
                request.payload["aud"][1],
                headers={"Authorization": f"Bearer {request.token}"},
            ).json()

            if "error" in request.user_info:
                print("ERROR", request.user_info)
                return HttpResponseServerError(request.user_info["error_description"])
        except Exception as error:
            print("ERROR", error)
            return HttpResponseServerError("cannot get user info")

        return self.get_response(request)


class UserFindCreate:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if public(request):
            return self.get_response(request)

        try:
            user, created = User.objects.update_or_create(
                auth_id=request.auth_id,
                email=request.user_info["email"]
                if "email" in request.user_info
                else print("WARNING", "could not get email", request.user_info),
                email_verified=request.user_info["email_verified"],
                last_name=request.user_info["family_name"],
                first_name=request.user_info["given_name"],
                locale=request.user_info["locale"],
                picture=request.user_info["picture"],
            )
            if created:
                while User.objects.filter(user_id=user.user_id).exists():
                    user.user_id = generate_id(
                        length=6, characters=string.ascii_lowercase + string.digits
                    )
                user.save()
            request.user = user
        except Exception as error:
            print("ERROR", error)
            return HttpResponseForbidden("cannot find or create user")

        return self.get_response(request)


class ParseBody:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if public(request):
            return self.get_response(request)

        if request.method == "POST":
            try:
                request.data = json.loads(request.body.decode("utf-8"))
            except Exception as error:
                print("ERROR", error)
                return HttpResponseForbidden("cannot read body")

        return self.get_response(request)

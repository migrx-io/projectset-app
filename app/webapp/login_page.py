from flask import (Blueprint, render_template, request, redirect, url_for,
                   make_response, session)

from flask_jwt_extended import get_jwt, verify_jwt_in_request, decode_token, create_access_token
import yaml

import logging as log
import os
from app.util.auth import authenticate, jwt_required
from authlib.integrations.requests_client import OAuth2Session
import requests

login_page = Blueprint('login_page', __name__)


def get_oauth_data():
    data = None

    with open(os.environ.get("APP_CONF", "app.yaml"), 'r',
              encoding="utf-8") as file:

        data = yaml.safe_load(file)["auth"]["github"]

    return data


def get_auth_types():
    return os.environ.get("AUTH_TYPES", "ldap").split(",")


def is_only_chat(claims):

    log.debug("is_only_chat: %s", claims)
    chat_only = ""
    with open(os.environ.get("APP_CONF", "app.yaml"), 'r',
              encoding="utf-8") as file:

        data = yaml.safe_load(file)

        chat_only = data.get("chat_only", "")

    if chat_only in claims.get("groups", []):
        return True

    return False


def get_user_repo_permission(user, conf):

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {conf['token']}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    response = requests.get(conf["url"].format(**{"user": user}),
                            timeout=10,
                            headers=headers)

    if response.status_code == 200:
        data = response.json()

        log.debug("get_user_repo_permission: data: %s", data)

        return [conf["group_map"].get(data["role_name"])]

    return []


@login_page.route("github/callback", methods=["GET"])
def callback():
    """ Retrieving an access token.
    """

    with open(os.environ.get("APP_CONF", "app.yaml"), 'r',
              encoding="utf-8") as file:

        data = yaml.safe_load(file)["auth"]

    log.debug("callback: data: %s", data)

    github = OAuth2Session(data["github"]["client_id"],
                           state=session['oauth_state'])

    log.debug("callback: github: %s", github)

    token = github.fetch_token(data["github"]["token_url"],
                               client_secret=data["github"]["client_secret"],
                               authorization_response=request.url)

    log.debug("callback: token: %s", token)

    github = OAuth2Session(data["github"]["client_id"], token=token)
    profile = github.get(data["github"]["profile_url"]).json()

    log.debug("callback: profile: %s", profile)

    group_search = data["github"]["groupSearch"]

    # get user permission
    log.debug("callback: groupSearch: %s", group_search)

    user_roles = get_user_repo_permission(profile["login"], group_search)

    access_token = create_access_token(
        identity=profile["login"], additional_claims={"groups": user_roles})

    # set jwt cookie
    response = make_response(redirect(url_for('login_page.login')))
    response.set_cookie('access_token_cookie', access_token)

    return response


@login_page.route('/', methods=['GET', 'POST'])
def login():

    error = None
    auth_types = get_auth_types()

    if request.method == 'GET':

        if request.args.get('error'):
            return render_template('login_page.html',
                                   error=request.args.get("error"),
                                   auth_types=auth_types)

        access_token = request.cookies.get('access_token_cookie')

        if access_token is None:
            return render_template('login_page.html',
                                   error=error,
                                   auth_types=auth_types)

        verify_jwt_in_request()
        if is_only_chat(get_jwt()):
            return redirect(url_for('chat_page.chat'))

        return redirect(url_for('repo_page.repo'))

    # Check which button presssed
    is_github = request.form.get("github")
    # is_ldap = request.form.get("ldap")

    # auth type
    if is_github:

        data = get_oauth_data()

        github = OAuth2Session(data["client_id"])
        authorization_url, state = github.create_authorization_url(
            data["authorization_base_url"])

        log.debug("authorization_url: %s", authorization_url)

        # State is used to prevent CSRF, keep this for later.
        session['oauth_state'] = state
        return redirect(authorization_url)

    # POST form
    email = request.form.get('email')
    password = request.form.get('password')

    is_auth, data = authenticate(email, password)

    if not is_auth:
        return render_template("login_page.html",
                               error=data,
                               auth_types=auth_types)

    log.debug("make response..")

    if is_only_chat(decode_token(data)):
        response = make_response(redirect(url_for('chat_page.chat')))
    else:
        response = make_response(
            redirect(url_for('projectset_page.projectset')))

    # set jwt cookie
    response.set_cookie('access_token_cookie', data)

    return response


@login_page.route('/logout', methods=['GET', 'POST'])
@jwt_required(True)
def logout():

    response = make_response(redirect(url_for('login_page.login')))
    response.set_cookie('access_token_cookie', '', expires=0)
    return response

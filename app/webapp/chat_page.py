import logging as log
from flask import Blueprint, render_template, request, jsonify
from app.util.auth import jwt_required
from app.crds.chat import (
    chat_call, )

from app.crds.repos import get_envs
import json
from flask_jwt_extended import get_jwt_identity
import uuid

chat_page = Blueprint('chat_page', __name__)

FIRST_MSG = "Hello! I will assist you with project onboarding. "\
        "Do you know which cluster you want to deploy your project to? "\
        "Avaliable clusters: {}"


@chat_page.route('/', methods=['GET'])
@jwt_required(True)
def chat():

    log.debug("start chat page..")
    suuid = uuid.uuid4()

    envs = [f"{k} - {v['description']}" for k, v in get_envs().items()]

    log.info("envs: %s", envs)

    return render_template('chat_page.html',
                           first_msg=FIRST_MSG.format(", ".join(envs)),
                           session=suuid)


@chat_page.route('/data/<session>', methods=['POST'])
@jwt_required(True)
def get_data(session):

    log.debug("get chat message, request: %s, data: %s", request, request.data)

    data = json.loads(request.data)

    user_input = data.get('data')

    login = get_jwt_identity()

    log.debug("login: %s, user_input: %s", login, user_input)

    try:

        envs = list(get_envs().keys())
        output = chat_call(session, login, user_input,
                           FIRST_MSG.format(",".join(envs)))

        return jsonify({"response": True, "message": output}), 200

    except Exception as e:
        log.error(e)
        return jsonify({"message": f'Error: {str(e)}', "response": False}), 200

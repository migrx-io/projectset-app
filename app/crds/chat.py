import logging as log
import os
import app
import json
from app.crds.repos import get_envs
from app.crds.projectsets import get_projectset, create_projectset
import yaml

HISTORY_DIR = os.environ.get("HISTORY_DIR", "/tmp")

FINAL_MSG = "That's it. "\
        "I created pull request here {}. "\
        "Once your request is approved, your project will be onboarded! "\
        "If you need to onboard one more project, continue the conversation. "\
        "Otherwise, you can close this chat."


def chatcompletion(client, system, chat_history):

    log.debug("chatcompletion:\n system: %s\n chat_history: %s", system,
              chat_history)

    messages = [
        {
            "role": "system",
            "content": system
        },
    ]

    log.debug("AGENDA: %s", messages)
    log.debug("chat_history: %s", chat_history)

    messages.extend(chat_history)

    log.debug("chat log: %s", messages)
    # gpt-4
    output = client.chat.completions.create(model=os.environ.get(
        "OPENAI_MODEL", "gpt-3.5-turbo"),
                                            messages=messages,
                                            temperature=0,
                                            max_tokens=1024,
                                            top_p=1,
                                            frequency_penalty=0,
                                            presence_penalty=0)

    return output.choices[0].message.content


def get_chat_history(login, first_message):

    file_path = f"{HISTORY_DIR}/{login}.txt"

    if not os.path.exists(file_path):
        # File doesn't exist, create it
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(json.dumps(first_message))

            return first_message

    else:
        with open(file_path, 'r', encoding="utf-8") as f:
            return json.loads(f.read())


def append_chat_history(login, message):

    file_path = f"{HISTORY_DIR}/{login}.txt"

    log.debug("append_chat_history: file: %s", file_path)

    data = []

    if os.path.exists(file_path):

        with open(file_path, 'r', encoding="utf-8") as f:
            data = json.loads(f.read())
            data.append(message)

        log.debug("append_chat_history: data: %s", data)

        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(json.dumps(data))

    return data


def delete_chat_history(login):

    file_path = f"{HISTORY_DIR}/{login}.txt"

    if os.path.exists(file_path):
        os.remove(file_path)


def get_spec(data):

    data_spec = yaml.safe_load(data["data"])["spec"]
    data_spec_raw = data_spec.copy()

    for k in data_spec_raw:
        if k not in ["limitRange", "resourceQuota", "networkPolicy"]:
            del data_spec[k]

    return data_spec


def create_cr_request(text):

    log.debug("create_cr_request: %s", text)

    try:
        cluster = [
            x.split(":")[1].strip() for x in text.split("```")[0].split("\n")
            if x.startswith("Cluster:")
        ][0]

        repo = get_envs().get(cluster)

        if repo is None:
            raise Exception(f"Cluster {cluster} is not found")

        repo = repo["url"]

        ydata = "\n".join(text.split("```")[1].split("\n")[1:])
    except Exception as e:
        log.error("create_cr_request: %s", e)
        raise Exception(
            "I apologize, but something went wrong and I cannot generate the final CR properly." \
                    "Could you please try again? Thank you"
        )

    log.debug("create_cr_request: cluster: %s, repo: %s, ydata: %s", cluster,
              repo, ydata)

    create_projectset("projectset", repo, cluster, ydata)

    return repo[:-4] + "/pulls"


def chat_call(session, login, user_input, first_msg):

    client = app.openai_client

    chat_history = get_chat_history(session, [{
        "role": "assistant",
        "content": first_msg
    }])

    log.debug("chat_history: %s", chat_history)

    system = ""
    with open(os.environ.get("PROMT", "promt.txt"), encoding="utf-8") as f:
        system = f.read()

        # format clusters and templates
        envs = {k: {"desc": v["description"]} for k, v in get_envs().items()}
        log.debug("chat_call: envs: %s", envs)

        templates = yaml.dump({
            v["name"]: {
                "spec": get_spec(v)
            }
            for v in get_projectset("projectset_template")
        })

        log.debug("chat_call: templates: %s", templates)

        system = system.format(clusters=envs, templates=templates)
        log.debug("system: %s", system)

    log.debug("Create chat message from %s", login)

    chat_history = append_chat_history(session, {
        "role": "user",
        "content": user_input
    })

    log.debug("append_chat_history: chat_history: %s", chat_history)
    output = chatcompletion(client, system, chat_history)

    # if final cr is created
    if output.find("### FINAL CR") >= 0:
        log.debug("FINAL CR:\n %s", output)

        repo = create_cr_request(output)

        delete_chat_history(session)
        output = FINAL_MSG.format(repo)
    else:
        append_chat_history(session, {"role": "assistant", "content": output})

    return output

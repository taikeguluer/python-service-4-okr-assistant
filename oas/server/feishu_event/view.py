from datetime import datetime
import json
from flask_restful import Resource
from flask import current_app, jsonify
from .event import EventManager, UrlVerificationEvent, MessageReceiveEvent
from oas.client import tencentcloudai_api_client, feishu_api_client
from oas.db.model import Director, Group, Doc
from oas.server.feishu_event.util import formated_content_picker

EMPLOYEE_CAREER_DEVELOPMENT_PLAN_COMMAND_NAME = "制定个人职业发展规划"
ONEBYONE_MSG_COMMAND_NAME = "群发助手"
MAGIC_COMMAND_NAME = "我有事儿找组织"
UNIT_TEST_COMMAND_NAME = "我在做测试"


event_manager = EventManager()


@event_manager.register("url_verification")
def request_url_verify_handler(req_data: UrlVerificationEvent):
    # url verification, just need return challenge
    if req_data.event.token != current_app.config["VERIFICATION_TOKEN"]:
        raise Exception("VERIFICATION_TOKEN is invalid")
    return jsonify({"challenge": req_data.event.challenge})


@event_manager.register("im.message.receive_v1")
def message_receive_event_handler(req_data: MessageReceiveEvent):
    sender_id = req_data.event.sender.sender_id
    message = req_data.event.message
    if message.message_type != "text":
        current_app.logger.warning("Other types of messages have not been processed yet")
        return jsonify()
        # get open_id and text_content
    sender_open_id = sender_id.open_id
    director = Director.query.filter_by(id=sender_open_id).first()
    text_content = message.content
    chat_groups = Group.query.filter_by(director_id=sender_open_id).all()
    members = {}
    flag = True
    for cg in chat_groups:
        if flag:
            members[cg.name] = feishu_api_client.get_open_ids_with_chat_id(cg.id, True)
            flag = False
        else:
            members[cg.name] = feishu_api_client.get_open_ids_with_chat_id(cg.id)

    if message.chat_type == "p2p":
        # response to the director command
        if director is not None:
            message_resolution = analyse_content(text_content, chat_groups, members)
            if "command_name" in message_resolution.keys():
                if message_resolution["command_name"] == UNIT_TEST_COMMAND_NAME:
                    # weekly_meeting_notification()
                    # monthly_meeting_notification()
                    # notification_on_monthly_meeting()
                    return jsonify()
            if "chat_name" in message_resolution.keys():
                send_notice_and_task(message_resolution, members, director.id)
                return jsonify()
        else:
            message_resolution = analyse_content(text_content, chat_groups, members)
            if "command_name" in message_resolution.keys():
                if message_resolution["command_name"] == MAGIC_COMMAND_NAME:
                    chat_groups = Group.query.filter_by(name=message_resolution["chat_name"]).all()
                    if len(chat_groups) <= 0:
                        return jsonify()
                    if len(chat_groups) >= 1:
                        for cg in chat_groups:
                            for key, value in feishu_api_client.get_open_ids_with_chat_id(cg.id):
                                if sender_open_id == value:

                                    director_last_name = Director.query.filter_by(id=cg.director_id).first().name[0:1]
                                    pure_content = json.loads(message_resolution["text_content"])
                                    text_content = "{\"text\":\"" + key + ": " + pure_content["text"] + "\"}"
                                    feishu_api_client.send("open_id", cg.director_id, text_content)
                                    text_content = "{\"text\":\"收到，稍晚"+director_last_name+"总会直接找您：）\"}"
                                    feishu_api_client.send("open_id", sender_open_id, text_content)
                                    return jsonify()
    json_content = json.loads(text_content)
    ai_response = "{\"text\":\"" + tencentcloudai_api_client.get_ai_response(sender_open_id, json_content["text"]) \
                  + "\"} "
    if message.chat_type == "p2p":
        feishu_api_client.send("open_id", sender_open_id, ai_response)
    else:
        feishu_api_client.send("chat_id", message.chat_id, ai_response)

    return jsonify()


class FeishuEventView(Resource):

    @staticmethod
    def post():
        # init callback instance and handle
        event_handler, event = event_manager.get_handler_with_event(current_app.config["VERIFICATION_TOKEN"],
                                                                    current_app.config["ENCRYPT_KEY"])

        return event_handler(event)


def send_notice_and_task(message_resolution, members, director_id):
    command_name = ""
    at_list = members[message_resolution["chat_name"]]
    if "command_name" in message_resolution.keys():
        command_name = message_resolution["command_name"]
    if len(message_resolution["at_list"]) > 0:
        at_list = message_resolution["at_list"]
    career_plan_template = Doc.query.filter_by(director_id=director_id, type="career_plan_template").first()
    career_plan_folder = Doc.query.filter_by(director_id=director_id, type="career_plan_folder").first()
    if "task_deadline_time_stamp" in message_resolution.keys():
        for key in at_list.keys():
            file_info = {}
            if command_name == EMPLOYEE_CAREER_DEVELOPMENT_PLAN_COMMAND_NAME:
                file_info = feishu_api_client.copy_file_from_template(
                    career_plan_template.token, "doc",
                    career_plan_folder.token, "个人职业发展规划-" + key)
                feishu_api_client.set_perm_on_file(file_info["token"], "doc", "full_access", (at_list[key],))
                feishu_api_client.set_perm_on_file(file_info["token"], "doc", "view", (director_id,))
            task_content = message_resolution["task_content"]
            text_content = message_resolution["text_content"]
            if "url" in file_info.keys():
                task_content += " " + file_info["url"]
                pure_content = json.loads(text_content)
                text_content = "{\"text\":\"" + pure_content["text"] + " " + file_info["url"] + "\"}"
                feishu_api_client.send("open_id", at_list[key], text_content)
            else:
                if command_name == ONEBYONE_MSG_COMMAND_NAME:
                    feishu_api_client.send("open_id", at_list[key], text_content)
            task_id = feishu_api_client.create_task(task_content, message_resolution["task_deadline_time_stamp"])
            feishu_api_client.set_task_stakeholders(task_id, (at_list[key],))
            feishu_api_client.set_task_stakeholders(task_id, (director_id,), True)
    else:
        if command_name == ONEBYONE_MSG_COMMAND_NAME:
            for key in at_list.keys():
                feishu_api_client.send("open_id", at_list[key], message_resolution["text_content"])

    if command_name not in (EMPLOYEE_CAREER_DEVELOPMENT_PLAN_COMMAND_NAME, ONEBYONE_MSG_COMMAND_NAME):
        feishu_api_client.send("chat_id", message_resolution["chat_id"], message_resolution["text_content"])


def analyse_content(content, chat_groups, members):
    # ###通知群组名称###@@@人员飞书姓名@@@$$$yyyymmddhhmm$$$***特殊命令***正常内容
    result = {}
    text_content = content
    if "###" in text_content:
        result["chat_name"] = formated_content_picker(text_content, "###")
        for cg in chat_groups:
            if cg.name == result["chat_name"]:
                result["chat_id"] = cg.id
                break
        text_content = text_content.replace("###" + result["chat_name"] + "###", "")
    if "***" in text_content:
        result["command_name"] = formated_content_picker(text_content, "***")
        text_content = text_content.replace("***" + result["command_name"] + "***", "")
    if "$$$" in text_content:
        date_string = formated_content_picker(text_content, "$$$")
        task_deadline = datetime.strptime(date_string + "+0800", "%Y%m%d%H%M%z")
        other_style_date_string = task_deadline.strftime("%-m月%-d日%-H:%M")
        text_content = text_content.replace("$$$" + date_string + "$$$", other_style_date_string)
        result["task_deadline_time_stamp"] = int(task_deadline.timestamp())
    at_list = {}
    pure_content = json.loads(text_content)
    task_content = pure_content["text"]
    while "@@@" in text_content:
        at_name = formated_content_picker(text_content, "@@@")
        text_content = text_content.replace("@@@" + at_name + "@@@", "<at user_id=\\\"" + members[result["chat_name"]][
            at_name] + "\\\">" + at_name + "</at> ")
        task_content = task_content.replace("@@@" + at_name + "@@@", "@" + at_name)
        at_list[at_name] = members[result["chat_name"]][at_name]
    result["text_content"] = text_content
    result["task_content"] = task_content
    result["at_list"] = at_list
    return result

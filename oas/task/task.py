import json
from datetime import datetime, timedelta
import pytz
from flask import current_app
from sqlalchemy import or_, and_
from sqlalchemy.sql.expression import func
from sqlalchemy.sql import sqltypes

from oas.manager import celery, db, logger
from oas.db.model import Group, Doc, MessageTemplate, Schedule, CancelledWeeklyMeeting
from oas.server.feishu_event.view import send_notice_and_task
from oas.client import feishu_api_client


@celery.task
def weekly_meeting_notification(weekly_beat):
    d = datetime.now(tz=pytz.timezone('Asia/Shanghai')).replace(hour=int(weekly_beat["notification_time"][0:2]),
                                                                minute=int(weekly_beat["notification_time"][3:]),
                                                                second=0, microsecond=0)
    # d = datetime.strptime("202202111730+0800", "%Y%m%d%H%M%z")
    ready_time = (d + timedelta((int(weekly_beat["ready_date"]) - int(weekly_beat["notification_date"]) + 7) % 7)). \
        replace(hour=int(weekly_beat["ready_time"][0:2]), minute=int(weekly_beat["ready_time"][3:]), second=0,
                microsecond=0)
    report_start_time = ready_time - timedelta(7)
    start_time = (d + timedelta((int(weekly_beat["start_date"]) - int(weekly_beat["notification_date"]) + 7) % 7)). \
        replace(hour=int(weekly_beat["start_time"][0:2]), minute=int(weekly_beat["start_time"][3:]), second=0,
                microsecond=0)
    kernel_chat_group = Group.query.filter_by(director_id=weekly_beat["director_id"], type="kernel").first()
    members = {
        kernel_chat_group.name: feishu_api_client.get_open_ids_with_chat_id(kernel_chat_group.id, True)
    }
    weekly_template = Doc.query.filter_by(director_id=weekly_beat["director_id"], type="weekly_template").first()
    weekly_folder = Doc.query.filter_by(director_id=weekly_beat["director_id"], type="weekly_folder").first()

    weekly_report = feishu_api_client.copy_file_from_template(weekly_template.token, "doc",
                                                              weekly_folder.token,
                                                              "OKR周报" + report_start_time.strftime("%Y/%m/%d") + "-"
                                                              + ready_time.strftime("%m/%d"))

    msg_template = MessageTemplate.query.filter_by(director_id=weekly_beat["director_id"], type='weekly').first()
    task_content = msg_template.content.format(start_time.strftime("%-m月%-d日%H:%M"),
                                               ready_time.strftime("%-m月%-d日%H:%M"),
                                               weekly_report["url"])
    notice_content = "{\"text\":\"" + task_content + "\"} "
    message_resolution = {"chat_name": kernel_chat_group.name, "chat_id": kernel_chat_group.id,
                          "command_name": "", "task_deadline_time_stamp": int(ready_time.timestamp()),
                          "text_content": notice_content, "task_content": task_content, "at_list": {}}
    send_notice_and_task(message_resolution, members, weekly_beat["director_id"])


@celery.task
def monthly_meeting_notification(monthly_beat):
    d = datetime.now(tz=pytz.timezone('Asia/Shanghai'))
    # d = datetime.strptime("202202250830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202203250830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202204280830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202205270830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202206240830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202207290830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202208260830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202209160830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202210280830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202211250830+0800", "%Y%m%d%H%M%z")
    # d = datetime.strptime("202212230830+0800", "%Y%m%d%H%M%z")
    current_year = d.year
    current_month = monthly_beat["type"]
    monthly_content = build_monthly_content(monthly_beat, current_year, current_month)
    ready_time = datetime.strptime(monthly_beat["ready_date"]+monthly_beat["ready_time"] + "+0800", "%Y-%m-%d%H:%M%z")
    report_name = monthly_content["report_name"]
    kernel_notice_content = monthly_content["kernel_notice_content"]
    team_notice_content = monthly_content["team_notice_content"]
    kernel_chat_group = Group.query.filter_by(director_id=monthly_beat["director_id"], type="kernel").first()
    team_chat_group = Group.query.filter_by(director_id=monthly_beat["director_id"], type="team").first()
    members = {
        kernel_chat_group.name: feishu_api_client.get_open_ids_with_chat_id(kernel_chat_group.id, True),
        team_chat_group.name: feishu_api_client.get_open_ids_with_chat_id(team_chat_group.id)
    }
    monthly_template = Doc.query.filter_by(director_id=monthly_beat["director_id"], type="monthly_template").first()
    monthly_folder = Doc.query.filter_by(director_id=monthly_beat["director_id"], type="monthly_folder").first()
    monthly_report = feishu_api_client.copy_file_from_template(monthly_template.token, "doc",
                                                               monthly_folder.token, report_name)
    kernel_notice_content = kernel_notice_content.replace("$$$monthly_report_url$$$", monthly_report["url"])
    pure_content = json.loads(kernel_notice_content)
    kernel_task_content = pure_content["text"]
    message_resolution = {"chat_name": kernel_chat_group.name, "chat_id": kernel_chat_group.id,
                          "command_name": "",
                          "task_deadline_time_stamp": int(ready_time.timestamp()),
                          "text_content": kernel_notice_content, "task_content": kernel_task_content, "at_list": {}}
    send_notice_and_task(message_resolution, members, monthly_beat["director_id"])
    pure_content = json.loads(team_notice_content)
    team_task_content = pure_content["text"]
    message_resolution = {"chat_name": team_chat_group.name, "chat_id": team_chat_group.id,
                          "command_name": "",
                          "text_content": team_notice_content, "task_content": team_task_content, "at_list": {}}
    if current_month in (3, 6, 9, 12):
        message_resolution = {"chat_name": team_chat_group.name, "chat_id": team_chat_group.id,
                              "command_name": "", "task_deadline_time_stamp": int(ready_time.timestamp()),
                              "text_content": team_notice_content, "task_content": team_task_content, "at_list": {}}
    send_notice_and_task(message_resolution, members, monthly_beat["director_id"])


@celery.task
def notification_on_monthly_meeting(monthly_beat):
    start_time = datetime.strptime(monthly_beat["start_date"]+monthly_beat["start_time"] + "+0800", "%Y-%m-%d%H:%M%z")

    d = datetime.now(tz=pytz.timezone('Asia/Shanghai')).replace(hour=start_time.hour + 12, minute=0, second=0,
                                                                microsecond=0)
    # d = datetime.strptime("202203011200+0800", "%Y%m%d%H%M%z")
    team_notice_content = "{\"text\":\"各位领导和同事，请大家在" + d.strftime(
        "%Y年%-m月%-d日%-H:%M") + "前，完成快问卷机器人发送的OKR评价问卷，并完成飞书任务。\"}"
    pure_content = json.loads(team_notice_content)
    team_task_content = pure_content["text"]
    team_chat_group = Group.query.filter_by(director_id=monthly_beat["director_id"], type="team").first()
    members = {
        team_chat_group.name: feishu_api_client.get_open_ids_with_chat_id(team_chat_group.id, True)
    }
    message_resolution = {"chat_name": team_chat_group.name, "chat_id": team_chat_group.id,
                          "command_name": "", "task_deadline_time_stamp": int(d.timestamp()),
                          "text_content": team_notice_content, "task_content": team_task_content, "at_list": {}}
    send_notice_and_task(message_resolution, members, monthly_beat["director_id"])


def build_monthly_content(monthly_beat, current_year, current_month):
    result = {}
    report_name = str(current_year) + "年"
    meeting_name = str(current_year) + "年"
    next_season = ""
    ready_time = datetime.strptime(monthly_beat["ready_date"]+monthly_beat["ready_time"] + "+0800", "%Y-%m-%d%H:%M%z")
    start_time = datetime.strptime(monthly_beat["start_date"]+monthly_beat["start_time"] + "+0800", "%Y-%m-%d%H:%M%z")
    kernel_notice_content = MessageTemplate.query.filter_by(director_id=monthly_beat["director_id"], type=current_month,
                                                            group="kernel").first().content
    team_notice_content = MessageTemplate.query.filter_by(director_id=monthly_beat["director_id"], type=current_month,
                                                          group="team").first().content
    '''
    kernel_notice_content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} " \
                            "2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$"
    team_notice_content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用" \
                          "飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
    '''
    month_trans = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
    if month_trans[current_month] in (1, 2, 4, 5, 7, 8, 10, 11):
        report_name += str(month_trans[current_month]) + "月OKR月报"
        meeting_name += str(month_trans[current_month]) + "月OKR月会"
        kernel_notice_content = kernel_notice_content.format(meeting_name, start_time.strftime("%Y年%-m月%-d日%-H:%M"),
                                                             ready_time.strftime("%Y年%-m月%-d日%-H:%M"), report_name)
        team_notice_content = team_notice_content.format(meeting_name, start_time.strftime("%Y年%-m月%-d日%-H:%M"))
        kernel_notice_content = "{\"text\":\"" + kernel_notice_content + "\"}"
        team_notice_content = "{\"text\":\"" + team_notice_content + "\"}"
        '''
        kernel_notice_content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$".format(
            meeting_name, monthly_meeting_dates[current_month - 1].strftime("%Y年%-m月%-d日%-H:%M"),
            monthly_report_deadline_dates[current_month - 1].strftime("%Y年%-m月%-d日%-H:%M"), report_name)
        team_notice_content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，" \
                              "请其他同事使用飞书日历中日程里的飞书视频会议地址参会。".format(meeting_name, monthly_meeting_dates[current_month - 1].strftime("%Y年%-m月%-d日%-H:%M"))
        kernel_notice_content = "{\"text\":\"" + kernel_notice_content + "\"}"
        team_notice_content = "{\"text\":\"" + team_notice_content + "\"}"
        '''
    else:
        if month_trans[current_month] == 3:
            report_name += "1季度OKR季报"
            meeting_name += "1季度OKR季度会"
            next_season = "2"
        if month_trans[current_month] == 6:
            report_name += "OKR半年报"
            meeting_name += "OKR半年会"
            next_season = "3"
        if month_trans[current_month] == 9:
            report_name += "3季度OKR季报"
            meeting_name += "3季度OKR季度会"
            next_season = "4"
        if month_trans[current_month] == 12:
            report_name += "OKR年报"
            meeting_name += "OKR年会"
            next_season = "下年OKR及下年1"
        okr_folder_url = Doc.query.filter_by(director_id=monthly_beat["director_id"], type="okr_folder").first().url
        okr_weekly_report_template_url = Doc.query.filter_by(director_id=monthly_beat["director_id"],
                                                             type="weekly_template").first().url
        okr_monthly_report_template_url = Doc.query.filter_by(director_id=monthly_beat["director_id"],
                                                              type="monthly_template").first().url
        kernel_notice_content = "{\"text\":\"" + kernel_notice_content.format(meeting_name,
                                                                              start_time.strftime("%Y年%-m月%-d日%-H:%M"),
                                                                              ready_time.strftime("%Y年%-m月%-d日%-H:%M"),
                                                                              next_season, okr_folder_url, next_season,
                                                                              okr_weekly_report_template_url,
                                                                              okr_monthly_report_template_url,
                                                                              report_name) + "\"}"
        team_notice_content = "{\"text\":\"" + team_notice_content.format(meeting_name,
                                                                          start_time.strftime("%Y年%-m月%-d日%-H:%M"),
                                                                          ready_time.strftime("%Y年%-m月%-d日%-H:%M"),
                                                                          next_season, okr_folder_url) + "\"}"

    result["report_name"] = report_name
    result["meeting_name"] = meeting_name
    result["kernel_notice_content"] = kernel_notice_content
    result["team_notice_content"] = team_notice_content
    return result


@celery.task
def midnight_check():
    cur_d = datetime.now(tz=pytz.timezone('Asia/Shanghai'))
    all_beats = Schedule.query.filter(or_(Schedule.queued_date == None,
                                          func.str_to_date(Schedule.queued_date, "%Y-%m-%d")
                                          < cur_d.replace(hour=0, minute=0, second=0, microsecond=0)),
                                      or_(and_(Schedule.type == 'weekly',
                                               Schedule.notification_date == str(cur_d.isoweekday()-1)),
                                               Schedule.notification_date == cur_d.strftime("%Y-%m-%d"))).all()

    current_app.logger.info(all_beats)
    for b in all_beats:
        eta = datetime.strptime(cur_d.strftime("%Y-%m-%d")+b.notification_time+"+0800", "%Y-%m-%d%H:%M%z")
        current_app.logger.info(b)
        if b.type == 'weekly':
            not_cancelled = True
            cancelled_dates = CancelledWeeklyMeeting.query.filter(CancelledWeeklyMeeting.director_id == b.director_id).all()
            for cd in cancelled_dates:
                if eta.strftime("%Y-%m-%d") == cd.cancelled_notification_date:
                    not_cancelled = False
                    break
            if not_cancelled:
                task_info = weekly_meeting_notification.apply_async((b.to_json(),), eta=eta)
                b.queued_date = cur_d.strftime("%Y-%m-%d")
                b.queued_time = cur_d.strftime("%H:%M")
                b.queued_task_id = task_info.id
        else:
            task_info = monthly_meeting_notification.apply_async((b.to_json(),), eta=eta)
            b.queued_date = cur_d.strftime("%Y-%m-%d")
            b.queued_time = cur_d.strftime("%H:%M")
            b.queued_task_id = task_info.id
            eta = datetime.strptime(b.start_date+b.start_time+"+0800", "%Y-%m-%d%H:%M%z")
            notification_on_monthly_meeting.apply_async((b.to_json(),), eta=eta)
    db.session.commit()
    return "done"

@celery.task
def celery_test():
    # logger.error("celery task testing by taikeguluer")
    return "celery task testing by taikeguluer"


@celery.task
def init_tenant(session_from_code):
    user_access_token = session_from_code["data"]["access_token"]
    director_id = session_from_code["data"]["open_id"]
    robot_info = feishu_api_client.get_robot_info(True)
    robot_ids = (robot_info["bot"]["open_id"],)
    root_folder = feishu_api_client.get_root_folder(False, user_access_token)

    okr_assistant_folder = feishu_api_client.create_folder(root_folder["data"]["token"], "OKR助理", False,
                                                           user_access_token)
    okr_folder = feishu_api_client.create_folder(okr_assistant_folder["data"]["token"], "OKR", False, user_access_token)
    okr_trace_folder = feishu_api_client.create_folder(okr_folder["data"]["token"], "跟踪", False, user_access_token)
    weekly_folder = feishu_api_client.create_folder(okr_trace_folder["data"]["token"], "周会", False, user_access_token)
    monthly_folder = feishu_api_client.create_folder(okr_trace_folder["data"]["token"], "月会", False, user_access_token)
    career_plan_folder = feishu_api_client.create_folder(okr_assistant_folder["data"]["token"], "个人职业发展规划", False,
                                                         user_access_token)
    okr_template = feishu_api_client.copy_file_from_template("shtcnbfHAWqOlIekBBs1ol9ReLc", "sheet",
                                                             okr_folder["data"]["token"], "<模板>okr-团队-姓名", False,
                                                             user_access_token)
    career_plan_template = feishu_api_client.copy_file_from_template("doxcnDcr4lz4g7fKK928325z4hc", "docx",
                                                                     career_plan_folder["data"]["token"],
                                                                     "<模板>个人职业发展画布-姓名", False, user_access_token)
    monthly_template = feishu_api_client.copy_file_from_template("doxcnGoilEOWvvco3P5fqCj5N0f", "docx",
                                                                 monthly_folder["data"]["token"], "<模板>####年##月OKR**报",
                                                                 False, user_access_token)
    weekly_template = feishu_api_client.copy_file_from_template("doxcnSHfULJhNmAJFxPndkuB9CO", "docx",
                                                                weekly_folder["data"]["token"],
                                                                "<模板>OKR周报####/##/##-##/##", False, user_access_token)
    try:

        docs = [
            {
                'token':career_plan_template["token"],
                'name':"<模板>个人职业发展画布-姓名",
                'url':career_plan_template["url"],
                'type':"career_plan_template"
            },
            {
                'token': career_plan_folder["data"]["token"],
                'name': "个人职业发展规划",
                'url': career_plan_folder["data"]["url"],
                'type': "career_plan_folder"
            },
            {
                'token': weekly_template["token"],
                'name': "<模板>OKR周报####/##/##-##/##",
                'url': weekly_template["url"],
                'type': "weekly_template"
            },
            {
                'token': weekly_folder["data"]["token"],
                'name': "周会",
                'url': weekly_folder["data"]["url"],
                'type': "weekly_folder"
            },
            {
                'token': monthly_template["token"],
                'name': "<模板>####年##月OKR**报",
                'url': monthly_template["url"],
                'type': "monthly_template"
            },
            {
                'token': monthly_folder["data"]["token"],
                'name': "月会",
                'url': monthly_folder["data"]["url"],
                'type': "monthly_folder"
            },
            {
                'token': okr_folder["data"]["token"],
                'name': "OKR",
                'url': okr_folder["data"]["url"],
                'type': "okr_folder"
            },
            {
                'token': okr_template["token"],
                'name': "<模板>okr-团队-姓名",
                'url': okr_template["url"],
                'type': "okr_template"
            }
        ]
        for doc in docs:
            doc_in_db = Doc(doc['token'], doc['name'], doc['url'], doc['type'], director_id)
            db.session.add(doc_in_db)

        cancelled_dates = ("2022-02-25", "2022-04-01", "2022-04-29", "2022-05-27", "2022-07-01", "2022-07-29", "2022-08-26",
                           "2022-09-23", "2022-09-30", "2022-10-28", "2022-11-25", "2022-12-30")
        for cd in cancelled_dates:
            cd_in_db = CancelledWeeklyMeeting()
            cd_in_db.director_id = director_id
            cd_in_db.cancelled_notification_date = cd
            db.session.add(cd_in_db)

        message_templates = [
            {
                'type': "weekly",
                'group': "kernel",
                'content': "各位领导，本周周会将于{}在12号楼26层1会议室正常召开，请在{}前完成周报。{} "
            },
            {
                'type': "mar",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
            },
            {
                'type': "mar",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} 2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "jun",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
            },
            {
                'type': "jun",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} 2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "sep",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
            },
            {
                'type': "sep",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} 2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "dec",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
            },
            {
                'type': "dec",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} 2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "nov",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
            },
            {
                'type': "nov",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "oct",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
            },
            {
                'type': "oct",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "aug",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
            },
            {
                'type': "aug",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "jul",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
            },
            {
                'type': "jul",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "may",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
            },
            {
                'type': "may",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "apr",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
            },
            {
                'type': "apr",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "feb",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
            },
            {
                'type': "feb",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
            },
            {
                'type': "jan",
                'group': "team",
                'content': "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
            },
            {
                'type': "jan",
                'group': "kernel",
                'content': "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
            }
        ]
        for mt in message_templates:
            mt_in_db = MessageTemplate()
            mt_in_db.director_id = director_id
            mt_in_db.type = mt["type"]
            mt_in_db.group = mt['group']
            mt_in_db.content = mt['content']
            db.session.add(mt_in_db)

        schedules = [
            {
                'type': 'weekly',
                'notification_date': "4",
                'ready_date': "0",
                'start_date': "1"
            },
            {
                'type': 'dec',
                'notification_date': "2022-12-23",
                'ready_date': "2022-12-30",
                'start_date': "2023-01-03"
            },
            {
                'type': 'nov',
                'notification_date': "2022-11-25",
                'ready_date': "2022-11-28",
                'start_date': "2022-11-29"
            },
            {
                'type': 'oct',
                'notification_date': "2022-10-28",
                'ready_date': "2022-10-31",
                'start_date': "2022-11-01"
            },
            {
                'type': 'sep',
                'notification_date': "2022-09-16",
                'ready_date': "2022-09-26",
                'start_date': "2022-09-27"
            },
            {
                'type': 'aug',
                'notification_date': "2022-08-26",
                'ready_date': "2022-08-29",
                'start_date': "2022-08-30"
            },
            {
                'type': 'jul',
                'notification_date': "2022-07-29",
                'ready_date': "2022-08-01",
                'start_date': "2022-08-02"
            },
            {
                'type': 'jun',
                'notification_date': "2022-06-24",
                'ready_date': "2022-07-04",
                'start_date': "2022-07-05"
            },
            {
                'type': 'may',
                'notification_date': "2022-05-27",
                'ready_date': "2022-05-30",
                'start_date': "2022-05-31"
            },
            {
                'type': 'apr',
                'notification_date': "2022-04-28",
                'ready_date': "2022-04-29",
                'start_date': "2022-05-05"
            },
            {
                'type': 'mar',
                'notification_date': "2022-03-25",
                'ready_date': "2022-04-01",
                'start_date': "2022-04-02"
            },
            {
                'type': 'feb',
                'notification_date': "2022-02-25",
                'ready_date': "2022-02-28",
                'start_date': "2022-03-01"
            },
            {
                'type': 'jan',
                'notification_date': "2022-01-29",
                'ready_date': "2022-02-07",
                'start_date': "2022-02-08"
            }
        ]
        for s in schedules:
            s_in_db = Schedule()
            s_in_db.director_id = director_id
            s_in_db.type = s['type']
            s_in_db.notification_date = s['notification_date']
            s_in_db.ready_date = s['ready_date']
            s_in_db.start_date = s['start_date']
            s_in_db.notification_time = "08:30"
            s_in_db.ready_time = "17:30"
            s_in_db.start_time = "08:30"
            db.session.add(s_in_db)

        db.session.commit()
    except Exception as e:
        # 数据库出错回滚
        db.session.rollback()
        current_app.logger.error(e)

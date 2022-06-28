from flask_restful import Resource
from flask_restful import reqparse
from flask import current_app, request

from oas.client import feishu_api_client
from oas.manager import db
from oas.db.model import Director, CancelledWeeklyMeeting, Doc, Group, Leader, MessageTemplate, Schedule, Team, Rank
from oas.db.schema import DirectorSchema, DocSchema, CancelledWeeklyMeetingSchema, GroupSchema, LeaderSchema, \
    MessageTemplateSchema, ScheduleSchema, TeamSchema

HARDCODE_ADMIN_NAME = "宋翔(songxiang9)"
HARDCODE_ADMIN_ID = "ou_7f3f463f04a9ab7b7c096a5c29cd45ab"

get_parser = reqparse.RequestParser()
get_parser.add_argument('Authorization-Code', type=str, required=True, location='headers', help='please login')

conf_parser = reqparse.RequestParser()
conf_parser.add_argument('Authorization-Code', type=str, required=True, location='headers', help='please login')
conf_parser.add_argument('configurations', type=dict, action="post")

actions_parser = reqparse.RequestParser()
actions_parser.add_argument('Authorization-Code', type=str, required=True, location='headers', help='please login')
actions_parser.add_argument('actions', type=dict, action="post")

class ActivationView(Resource):

    def get(self):
        current_app.logger.info("{} {} {}".format(request.method, request.url, ' '.join(
            "{}:{}".format(k, v) for k, v in request.headers.items())))
        args = get_parser.parse_args()
        current_app.logger.info(args)
        session_from_code = feishu_api_client.get_session_from_code(args['Authorization-Code'], True)
        director_id = session_from_code["data"]["open_id"]
        directors = Director.query.filter_by(id=director_id).all()
        result = {
            "bot": feishu_api_client.get_robot_info()["bot"],
            "activated": len(directors) == 1,
            "director_info": feishu_api_client.get_user_info(director_id)
        }
        return result

    def post(self):
        args = get_parser.parse_args()
        session_from_code = feishu_api_client.get_session_from_code(args['Authorization-Code'], True)
        # session_from_code["data"]["access_token"]
        user_info = feishu_api_client.get_user_info(session_from_code["data"]["open_id"])
        director = Director(id=session_from_code["data"]["open_id"], name=user_info["name"])
        try:
            db.session.add(director)
            db.session.commit()
        except Exception as e:
            # 数据库出错回滚
            db.session.rollback()
            current_app.logger.error(e)
            return {"errno": 0, "errmsg": "数据库查询异常"}
        from oas.task.task import init_tenant
        init_tenant.delay(session_from_code)
        return {"errno": 1, "errmsg": "激活成功"}


class DbInitiationView(Resource):

    def post(self):
        args = get_parser.parse_args()
        session_from_code = feishu_api_client.get_session_from_code(args['Authorization-Code'], True)
        # session_from_code["data"]["access_token"]
        director_id = session_from_code["data"]["open_id"]
        user_info = feishu_api_client.get_user_info(director_id)
        director_name = user_info["data"]["user"]["name"]
        if director_name == HARDCODE_ADMIN_NAME \
                and director_id == HARDCODE_ADMIN_ID:
            directors = Director.query.filter_by(id=director_id).all()
            if len(directors) > 0:
                return {"errno": 0, "errmsg": "数据库已经完成初始化"}
            try:
                director = Director(id=director_id, name=director_name)
                db.session.add(director)

                cancelled_dates = ("20220225", "20220401", "20220429", "20220527", "20220701", "20220729", "20220826",
                                   "20220923", "20220930", "20221028", "20221125", "20221230")
                for cd in cancelled_dates:
                    cd_in_db = CancelledWeeklyMeeting()
                    cd_in_db.director_id = session_from_code["data"]["open_id"]
                    cd_in_db.year = "2022"
                    cd_in_db.cancelled_notification_date = cd
                    db.session.add(cd_in_db)

                career_plan_template = Doc("doccnaPv3Upb3Jp8nijemzGBXWh", "个人职业发展画布-姓名(万信id)",
                                           "https://wanda.feishu.cn/docs/doccnaPv3Upb3Jp8nijemzGBXWh",
                                           "career_plan_template", director_id)
                db.session.add(career_plan_template)
                career_plan_folder = Doc("fldcnGQcmMChWc27XjtnCkkdmxd", "数据与技术团队职业发展画布",
                                         "https://wanda.feishu.cn/drive/folder/fldcnGQcmMChWc27XjtnCkkdmxd",
                                         "career_plan_folder", director_id)
                db.session.add(career_plan_folder)
                weekly_template = Doc("doccn7a9k4PIVuezz1b6mHcXSWd", "OKR周报####/##/##-##/##",
                                      "https://wanda.feishu.cn/docs/doccn7a9k4PIVuezz1b6mHcXSWd",
                                      "weekly_template", director_id)
                db.session.add(weekly_template)
                weekly_folder = Doc("fldcnbpUnn7EnRGd6xeOSp9t0jU", "核心周会",
                                    "https://wanda.feishu.cn/drive/folder/fldcnbpUnn7EnRGd6xeOSp9t0jU",
                                    "weekly_folder", director_id)
                db.session.add(weekly_folder)
                monthly_template = Doc("doccnPipdpudvwU41Ncp3OmRzgb", "####年##月OKR**报",
                                       "https://wanda.feishu.cn/docs/doccnPipdpudvwU41Ncp3OmRzgb",
                                       "monthly_template", director_id)
                db.session.add(monthly_template)
                monthly_folder = Doc("fldcn2YXoQPa0EdujwNZOYOVLGh", "全员月会",
                                     "https://wanda.feishu.cn/drive/folder/fldcn2YXoQPa0EdujwNZOYOVLGh",
                                     "monthly_folder", director_id)
                db.session.add(monthly_folder)
                okr_folder = Doc("fldcnWcPGOGVbmnYqnZD5QNxzuc", "数据与技术团队OKR",
                                 "https://wanda.feishu.cn/drive/folder/fldcnWcPGOGVbmnYqnZD5QNxzuc",
                                 "okr_folder", director_id)
                db.session.add(okr_folder)
                kcg = Group("oc_2f0aea37b7001d514117cf3448a55043", "数据与技术团队核心", "kernel", director_id)
                db.session.add(kcg)
                tcg = Group("oc_914bbd6e9164da186a1b1920b09f1c10", "数据与技术团队", "team", director_id)
                db.session.add(tcg)
                quan_hao = Leader("ou_b7497d0534f17b8fcb619527a2359446", "全昊(quanhao3)", director_id)
                wang_lei = Leader("ou_6b5a313ace12ef33052e44bf12048a99", "王雷(wanglei0)", director_id)
                xu_lu = Leader("ou_d80aa2cb101d310888b659ecf11eb0de", "徐璐(xulu53)", director_id)
                li_ke = Leader("ou_69ab8e70e2694063a00a7078d9a02b50", "李可(like81)", director_id)
                bao_yi = Leader("ou_13344595c94e969ae10e46f4d643e059", "包毅(baoyi5)", director_id)
                li_xia = Leader("ou_f3b1ea330bbcf513d3f31227340fef70", "李夏(lixia103)", director_id)
                db.session.add(quan_hao)
                db.session.add(wang_lei)
                db.session.add(xu_lu)
                db.session.add(li_ke)
                db.session.add(bao_yi)
                db.session.add(li_xia)

                weekly_notice = MessageTemplate()
                weekly_notice.director_id = director_id
                weekly_notice.type = 0
                weekly_notice.team = "kernel"
                weekly_notice.content = "各位领导，本周周会将于{}在12号楼26层1会议室正常召开，请在{}前完成周报。{} "
                db.session.add(weekly_notice)

                notice10 = MessageTemplate()
                notice10.director_id = director_id
                notice10.type = 1
                notice10.team = "kernel"
                notice10.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
                db.session.add(notice10)

                notice11 = MessageTemplate()
                notice11.director_id = director_id
                notice11.type = 1
                notice11.team = "team"
                notice11.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
                db.session.add(notice11)

                notice20 = MessageTemplate()
                notice20.director_id = director_id
                notice20.type = 2
                notice20.team = "kernel"
                notice20.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
                db.session.add(notice20)

                notice21 = MessageTemplate()
                notice21.director_id = director_id
                notice21.type = 2
                notice21.team = "team"
                notice21.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
                db.session.add(notice21)

                notice40 = MessageTemplate()
                notice40.director_id = director_id
                notice40.type = 4
                notice40.team = "kernel"
                notice40.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
                db.session.add(notice40)

                notice41 = MessageTemplate()
                notice41.director_id = director_id
                notice41.type = 4
                notice41.team = "team"
                notice41.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
                db.session.add(notice41)

                notice50 = MessageTemplate()
                notice50.director_id = director_id
                notice50.type = 5
                notice50.team = "kernel"
                notice50.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
                db.session.add(notice50)

                notice51 = MessageTemplate()
                notice51.director_id = director_id
                notice51.type = 5
                notice51.team = "team"
                notice51.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
                db.session.add(notice51)
                notice70 = MessageTemplate()
                notice70.director_id = director_id
                notice70.type = 7
                notice70.team = "kernel"
                notice70.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
                db.session.add(notice70)

                notice71 = MessageTemplate()
                notice71.director_id = director_id
                notice71.type = 7
                notice71.team = "team"
                notice71.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
                db.session.add(notice71)
                notice80 = MessageTemplate()
                notice80.director_id = director_id
                notice80.type = 8
                notice80.team = "kernel"
                notice80.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
                db.session.add(notice80)

                notice81 = MessageTemplate()
                notice81.director_id = director_id
                notice81.type = 8
                notice81.team = "team"
                notice81.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
                db.session.add(notice81)
                notice100 = MessageTemplate()
                notice100.director_id = director_id
                notice100.type = 10
                notice100.team = "kernel"
                notice100.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
                db.session.add(notice100)

                notice101 = MessageTemplate()
                notice101.director_id = director_id
                notice101.type = 10
                notice101.team = "team"
                notice101.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
                db.session.add(notice101)
                notice110 = MessageTemplate()
                notice110.director_id = director_id
                notice110.type = 11
                notice110.team = "kernel"
                notice110.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成{} $$$monthly_report_url$$$ "
                db.session.add(notice110)

                notice111 = MessageTemplate()
                notice111.director_id = director_id
                notice111.type = 11
                notice111.team = "team"
                notice111.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。"
                db.session.add(notice111)

                notice30 = MessageTemplate()
                notice30.director_id = director_id
                notice30.type = 3
                notice30.team = "kernel"
                notice30.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} 2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$ "
                db.session.add(notice30)

                notice31 = MessageTemplate()
                notice31.director_id = director_id
                notice31.type = 3
                notice31.team = "team"
                notice31.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
                db.session.add(notice31)

                notice60 = MessageTemplate()
                notice60.director_id = director_id
                notice60.type = 6
                notice60.team = "kernel"
                notice60.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} 2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$ "
                db.session.add(notice60)

                notice61 = MessageTemplate()
                notice61.director_id = director_id
                notice61.type = 6
                notice61.team = "team"
                notice61.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
                db.session.add(notice61)

                notice90 = MessageTemplate()
                notice90.director_id = director_id
                notice90.type = 9
                notice90.team = "kernel"
                notice90.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} 2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$ "
                db.session.add(notice90)

                notice91 = MessageTemplate()
                notice91.director_id = director_id
                notice91.type = 9
                notice91.team = "team"
                notice91.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
                db.session.add(notice91)

                notice120 = MessageTemplate()
                notice120.director_id = director_id
                notice120.type = 12
                notice120.team = "kernel"
                notice120.content = "各位领导，{}将于{}在12号楼26层1会议室召开，请在{}前完成：1、个人和团队的{}季度OKR的制定； {} 2、根据{}季度OKR对OKR周报模板 {} 和OKR月报模板 {} 中对应部分进行更新；3、完成{} $$$monthly_report_url$$$ "
                db.session.add(notice120)

                notice121 = MessageTemplate()
                notice121.director_id = director_id
                notice121.type = 12
                notice121.team = "team"
                notice121.content = "各位领导和同事，{}将于{}在12号楼26层1会议室召开，请各团队负责人准时到会议室参会，请其他同事使用飞书日历中日程里的飞书视频会议地址参会。请在{}前完成个人{}季度OKR的制定。 {}"
                db.session.add(notice121)

                weeklys = Schedule()
                weeklys.director_id = director_id
                weeklys.type = 0
                weeklys.year = 2022
                weeklys.notification_time = "5-------0830"
                weeklys.ready_time = "1-------1730"
                weeklys.start_time = "2-------0830"
                db.session.add(weeklys)
                '''
                KERNAL_CHAT_NAME = "数据与技术团队核心"
                TEAM_CHAT_NAME = "数据与技术团队"
                # KERNAL_CHAT_NAME = "宋翔的核心测试群"
                # TEAM_CHAT_NAME = "宋翔的团队测试群"
                TEST_CHAT_NAME = "宋翔的测试群"
                DEPT_CHAT_NAME = "信息科技中心"
                ADMIN_NAME = "宋翔(songxiang9)"
                # EMPLOYEE_CAREER_DEVELOPMENT_PLAN_TEMPLATE_TOKEN = "boxcnVP8mRDAU73d7a6nkcvAChg"
                EMPLOYEE_CAREER_DEVELOPMENT_PLAN_TEMPLATE_TOKEN = "doccnaPv3Upb3Jp8nijemzGBXWh"

                EMPLOYEE_CAREER_DEVELOPMENT_PLAN_FOLDER_TOKEN = "fldcnGQcmMChWc27XjtnCkkdmxd"
                WEEKLY_REPORT_TEMPLATE_TOKEN = "doccn7a9k4PIVuezz1b6mHcXSWd"
                WEEKLY_REPORT_FOLDER_TOKEN = "fldcnbpUnn7EnRGd6xeOSp9t0jU"
                MONTHLY_REPORT_TEMPLATE_TOKEN = "doccnPipdpudvwU41Ncp3OmRzgb"
                MONTHLY_REPORT_FOLDER_TOKEN = "fldcn2YXoQPa0EdujwNZOYOVLGh"


                monthly_meeting_notification_dates = (
                    datetime(2022, 1, 29, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 2, 25, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 3, 25, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 4, 28, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 5, 27, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 6, 24, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 7, 29, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 8, 26, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 9, 16, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 10, 28, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 11, 25, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 12, 23, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')))
                monthly_report_deadline_dates = (
                    datetime(2022, 2, 7, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 2, 28, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 4, 1, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 4, 29, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 5, 30, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 7, 4, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 8, 1, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 8, 29, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 9, 26, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 10, 31, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 11, 28, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 12, 30, 17, 30, 0, 0, pytz.timezone('Asia/Shanghai')))

                monthly_meeting_dates = (
                    datetime(2022, 2, 8, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 3, 1, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 4, 2, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 5, 5, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 5, 31, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 7, 5, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 8, 2, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 8, 30, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 9, 27, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 11, 1, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2022, 11, 29, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')),
                    datetime(2023, 1, 3, 8, 30, 0, 0, pytz.timezone('Asia/Shanghai')))

                okr_folder_url = "https://***.feishu.cn/drive/folder/fldcnWcPGOGVbmnYqnZD5QNxzuc"
                okr_weekly_report_template_url = "https://***.feishu.cn/docs/doccn7a9k4PIVuezz1b6mHcXSWd"
                okr_monthly_report_template_url = "https://***.feishu.cn/docs/doccnPipdpudvwU41Ncp3OmRzgb"
                team_kernel = ("*")
                team_leaders = ("*")
                '''
                monthlys1 = Schedule()
                monthlys1.director_id = director_id
                monthlys1.type = 1
                monthlys1.year = 2022
                monthlys1.notification_time = "202201290830"
                monthlys1.ready_time = "202202071730"
                monthlys1.start_time = "202202080830"
                db.session.add(monthlys1)

                monthlys2 = Schedule()
                monthlys2.director_id = director_id
                monthlys2.type = 2
                monthlys2.year = 2022
                monthlys2.notification_time = "202202250830"
                monthlys2.ready_time = "202202281730"
                monthlys2.start_time = "202203010830"
                db.session.add(monthlys2)

                monthlys3 = Schedule()
                monthlys3.director_id = director_id
                monthlys3.type = 3
                monthlys3.year = 2022
                monthlys3.notification_time = "202203250830"
                monthlys3.ready_time = "202204011730"
                monthlys3.start_time = "202204020830"
                db.session.add(monthlys3)

                monthlys4 = Schedule()
                monthlys4.director_id = director_id
                monthlys4.type = 4
                monthlys4.year = 2022
                monthlys4.notification_time = "202204280830"
                monthlys4.ready_time = "202204291730"
                monthlys4.start_time = "202205050830"
                db.session.add(monthlys4)

                monthlys5 = Schedule()
                monthlys5.director_id = director_id
                monthlys5.type = 5
                monthlys5.year = 2022
                monthlys5.notification_time = "202205270830"
                monthlys5.ready_time = "202205301730"
                monthlys5.start_time = "202205310830"
                db.session.add(monthlys5)

                monthlys6 = Schedule()
                monthlys6.director_id = director_id
                monthlys6.type = 6
                monthlys6.year = 2022
                monthlys6.notification_time = "202206240830"
                monthlys6.ready_time = "202207041730"
                monthlys6.start_time = "202207050830"
                db.session.add(monthlys6)

                monthlys7 = Schedule()
                monthlys7.director_id = director_id
                monthlys7.type = 7
                monthlys7.year = 2022
                monthlys7.notification_time = "202207290830"
                monthlys7.ready_time = "202208011730"
                monthlys7.start_time = "202208020830"
                db.session.add(monthlys7)

                monthlys8 = Schedule()
                monthlys8.director_id = director_id
                monthlys8.type = 8
                monthlys8.year = 2022
                monthlys8.notification_time = "202208260830"
                monthlys8.ready_time = "202208291730"
                monthlys8.start_time = "202208300830"
                db.session.add(monthlys8)

                monthlys9 = Schedule()
                monthlys9.director_id = director_id
                monthlys9.type = 9
                monthlys9.year = 2022
                monthlys9.notification_time = "202209160830"
                monthlys9.ready_time = "202209261730"
                monthlys9.start_time = "202209270830"
                db.session.add(monthlys9)

                monthlys10 = Schedule()
                monthlys10.director_id = director_id
                monthlys10.type = 10
                monthlys10.year = 2022
                monthlys10.notification_time = "202210280830"
                monthlys10.ready_time = "202210311730"
                monthlys10.start_time = "202211010830"
                db.session.add(monthlys10)

                monthlys11 = Schedule()
                monthlys11.director_id = director_id
                monthlys11.type = 11
                monthlys11.year = 2022
                monthlys11.notification_time = "202211250830"
                monthlys11.ready_time = "202211281730"
                monthlys11.start_time = "202211290830"
                db.session.add(monthlys11)

                monthlys12 = Schedule()
                monthlys12.director_id = director_id
                monthlys12.type = 12
                monthlys12.year = 2022
                monthlys12.notification_time = "202212230830"
                monthlys12.ready_time = "202212301730"
                monthlys12.start_time = "202301030830"
                db.session.add(monthlys12)

                team1 = Team()
                team1.leader_id = "ou_b7497d0534f17b8fcb619527a2359446"
                team1.name = "经营决策支撑大数据团队"
                db.session.add(team1)

                team2 = Team()
                team2.leader_id = "ou_6b5a313ace12ef33052e44bf12048a99"
                team2.name = "运维服务与安全部"
                db.session.add(team2)
                team3 = Team()
                team3.leader_id = "ou_d80aa2cb101d310888b659ecf11eb0de"
                team3.name = "人工智能团队"
                db.session.add(team3)
                team4 = Team()
                team4.leader_id = "ou_69ab8e70e2694063a00a7078d9a02b50"
                team4.name = "数据技术平台团队"
                db.session.add(team4)
                team5 = Team()
                team5.leader_id = "ou_13344595c94e969ae10e46f4d643e059"
                team5.name = "业务增长支撑团队"
                db.session.add(team5)
                team6 = Team()
                team6.leader_id = "ou_f3b1ea330bbcf513d3f31227340fef70"
                team6.name = "技术研发部"
                db.session.add(team6)

                db.commit()

            except Exception as e:
                # 数据库出错回滚
                db.session.rollback()
                current_app.logger.error(e)
                return {"errno": 0, "errmsg": "数据库查询异常"}
            # init_tenant.delay(session_from_code)
            return {"errno": 1, "errmsg": "激活成功"}
        return {"errno": 0, "errmsg": "无效的用户权限"}


class ConfigurationView(Resource):

    def get(self):
        args = get_parser.parse_args()
        session_from_code = feishu_api_client.get_session_from_code(args['Authorization-Code'], True)
        director_id = session_from_code["data"]["open_id"]
        resp = {"configurations": self.get_configuration(director_id)}
        if len(resp["configurations"]["docs"]) == 0:
            resp["errno"] = 2
            resp["errmg"] = "请稍后重试"
        else:
            resp["errno"] = 1
            resp["errmg"] = "成功"
        return resp

    '''def post(self):
        args = parser.parse_args()
        current_app.logger.info(args)
        session_from_code = feishu_api_client.get_session_from_code(args['Authorization-Code'], True)
        robot_info = feishu_api_client.get_robot_info()
        robot_ids = [robot_info["bot"]["open_id"]]
        director_id = session_from_code["data"]["open_id"]
        db_json = self.input_to_db(args["configurations"])
        cancelled_weekly_meetings = db_json["cancelled_weekly_meetings"]
        groups = db_json["groups"]
        leaders = db_json["leaders"]
        message_templates = db_json["message_templates"]
        schedules = db_json["schedules"]
        teams = db_json["teams"]
        try:
            CancelledWeeklyMeeting.query.filter_by(director_id=director_id).delete()
            cancelled_weekly_meeting_schema = CancelledWeeklyMeetingSchema(many=True)
            cwms = cancelled_weekly_meeting_schema.load(cancelled_weekly_meetings, session=db.session)
            for i in range(len(cwms)):
                cwms[i].director_id = director_id
            db.session.add_all(cwms)

            Group.query.filter_by(director_id=director_id).delete()
            group_schema = GroupSchema(many=True)
            groups_in_db = group_schema.load(groups, session=db.session)
            for i in range(len(groups_in_db)):
                groups_in_db[i].director_id = director_id
                feishu_api_client.invite_on_to_chat(groups_in_db[i].id, robot_ids, False,
                                                    session_from_code['data']['access_token'])
            db.session.add_all(groups_in_db)

            Leader.query.filter_by(director_id=director_id).delete()
            leader_schema = LeaderSchema(many=True)
            leaders_in_db = leader_schema.load(leaders, session=db.session)
            for i in range(len(leaders_in_db)):
                leaders_in_db[i].director_id = director_id
            db.session.add_all(leaders_in_db)

            MessageTemplate.query.filter_by(director_id=director_id).delete()
            message_template_schema = MessageTemplateSchema(many=True)
            message_templates_in_db = message_template_schema.load(message_templates, session=db.session)
            for i in range(len(message_templates_in_db)):
                message_templates_in_db[i].director_id = director_id
            db.session.add_all(message_templates_in_db)

            Schedule.query.filter_by(director_id=director_id).delete()
            schedule_schema = ScheduleSchema(many=True)
            schedules_in_db = schedule_schema.load(schedules, session=db.session)
            for i in range(len(schedules_in_db)):
                schedules_in_db[i].director_id = director_id
            db.session.add_all(schedules_in_db)

            Team.query.filter_by(director_id=director_id).delete()
            team_schema = TeamSchema(many=True)
            teams_in_db = team_schema.load(teams, session=db.session)
            for i in range(len(teams_in_db)):
                teams_in_db[i].director_id = director_id
            db.session.add_all(teams_in_db)

            db.session.commit()

        except Exception as e:
            # 数据库出错回滚
            db.session.rollback()
            current_app.logger.error(e)
            return {"errno": 0, "errmsg": "数据库操作异常"}

        return {"errno": 1, "errmsg": "配置成功"}
'''

    def post(self):
        current_app.logger.info("{} {} {}".format(request.method, request.url, ' '.join(
            "{}:{}".format(k, v) for k, v in request.headers.items())))
        args = conf_parser.parse_args()
        current_app.logger.info(args)
        session_from_code = feishu_api_client.get_session_from_code(args['Authorization-Code'], True)
        director_id = session_from_code["data"]["open_id"]
        db_json = self.input_to_db(args["configurations"])
        try:
            if "groups" in db_json.keys():
                Group.query.filter_by(director_id=director_id).delete()
                group_schema = GroupSchema(many=True)
                groups_in_db = group_schema.load(db_json["groups"], session=db.session)
                robot_info = feishu_api_client.get_robot_info()
                robot_ids = [robot_info["bot"]["open_id"]]
                for i in range(len(groups_in_db)):
                    groups_in_db[i].director_id = director_id
                    feishu_api_client.invite_on_to_chat(groups_in_db[i].id, robot_ids, False,
                                                        session_from_code['data']['access_token'])
                db.session.add_all(groups_in_db)
            if "cancelled_weekly_meetings" in db_json.keys():

                CancelledWeeklyMeeting.query.filter_by(director_id=director_id).delete()
                cancelled_weekly_meeting_schema = CancelledWeeklyMeetingSchema(many=True)
                cwms = cancelled_weekly_meeting_schema.load(db_json["cancelled_weekly_meetings"], session=db.session)
                for i in range(len(cwms)):
                    cwms[i].director_id = director_id
                db.session.add_all(cwms)

            if "leaders" in db_json.keys():

                Leader.query.filter_by(director_id=director_id).delete()
                leader_schema = LeaderSchema(many=True)
                leaders_in_db = leader_schema.load(db_json["leaders"], session=db.session)
                for i in range(len(leaders_in_db)):
                    leaders_in_db[i].director_id = director_id
                db.session.add_all(leaders_in_db)
            if "message_templates" in db_json.keys():

                MessageTemplate.query.filter_by(director_id=director_id).delete()
                message_template_schema = MessageTemplateSchema(many=True)
                message_templates_in_db = message_template_schema.load(db_json["message_templates"], session=db.session)
                for i in range(len(message_templates_in_db)):
                    message_templates_in_db[i].director_id = director_id
                db.session.add_all(message_templates_in_db)
            if "schedules" in db_json.keys():

                Schedule.query.filter_by(director_id=director_id).delete()
                schedule_schema = ScheduleSchema(many=True)
                schedules_in_db = schedule_schema.load(db_json["schedules"], session=db.session)
                for i in range(len(schedules_in_db)):
                    schedules_in_db[i].director_id = director_id
                db.session.add_all(schedules_in_db)
            if "teams" in db_json.keys():

                Team.query.filter_by(director_id=director_id).delete()
                team_schema = TeamSchema(many=True)
                teams_in_db = team_schema.load(db_json["teams"], session=db.session)
                for i in range(len(teams_in_db)):
                    teams_in_db[i].director_id = director_id
                db.session.add_all(teams_in_db)

            db.session.commit()

        except Exception as e:
            # 数据库出错回滚
            db.session.rollback()
            current_app.logger.error(e)
            return {"errno": 0, "errmsg": "数据库操作异常"}

        return {"errno": 1, "errmsg": "配置成功"}

    def delete(self):
        args = get_parser.parse_args()
        session_from_code = feishu_api_client.get_session_from_code(args['Authorization-Code'], True)
        director_id = session_from_code["data"]["open_id"]
        try:
            #CancelledWeeklyMeeting.query.filter_by(director_id=director_id).delete()
            #Group.query.filter_by(director_id=director_id).delete()
            #Leader.query.filter_by(director_id=director_id).delete()
            #MessageTemplate.query.filter_by(director_id=director_id).delete()
            #Schedule.query.filter_by(director_id=director_id).delete()
            #Team.query.filter_by(director_id=director_id).delete()
            #Rank.query.filter_by(director_id=director_id).delete()
            Director.query.filter_by(id=director_id).delete()

            db.session.commit()

        except Exception as e:
            # 数据库出错回滚
            db.session.rollback()
            current_app.logger.error(e)
            return {"errno": 0, "errmsg": "数据库操作异常"}
        return {"errno": 1, "errmsg": "配置数据删除成功"}

    def get_configuration(self, director_id):
        resp = {}

        cancelled_weekly_meetings = CancelledWeeklyMeeting.query.filter_by(director_id=director_id).all()
        cancelled_weekly_meeting_schema = CancelledWeeklyMeetingSchema(many=True)
        resp["cancelled_weekly_meetings"] = cancelled_weekly_meeting_schema.dump(cancelled_weekly_meetings)

        docs = Doc.query.filter_by(director_id=director_id).all()
        doc_schema = DocSchema(many=True)
        resp["docs"] = doc_schema.dump(docs)

        groups = Group.query.filter_by(director_id=director_id).all()
        group_schema = GroupSchema(many=True)
        resp["groups"] = group_schema.dump(groups)

        leaders = Leader.query.filter_by(director_id=director_id).all()
        leader_schema = LeaderSchema(many=True)
        resp["leaders"] = leader_schema.dump(leaders)
        leader_ids = []
        for leader in leaders:
            leader_ids.append(leader.id)

        message_templates = MessageTemplate.query.filter_by(director_id=director_id).all()
        message_template_schema = MessageTemplateSchema(many=True)
        resp["message_templates"] = message_template_schema.dump(message_templates)

        schedules = Schedule.query.filter_by(director_id=director_id).all()
        schedule_schema = ScheduleSchema(many=True)
        resp["schedules"] = schedule_schema.dump(schedules)

        teams = Team.query.filter(Team.leader_id.in_(leader_ids)).all()
        team_schema = TeamSchema(many=True)
        resp["teams"] = team_schema.dump(teams)

        return self.db_to_output(resp)

    @staticmethod
    def db_to_output(db_json):
        output = {
            "cancelled_weekly_meetings": db_json["cancelled_weekly_meetings"],
            "docs": {},
            "groups": {},
            "teams": [],
            "schedules": {}
        }

        docs = {"doc_template": {}, "doc_folder": {}}
        for doc in db_json["docs"]:
            if doc["type"] == "monthly_template":
                docs["doc_template"]["jan"] = doc
                docs["doc_template"]["feb"] = doc
                docs["doc_template"]["mar"] = doc
                docs["doc_template"]["apr"] = doc
                docs["doc_template"]["may"] = doc
                docs["doc_template"]["jun"] = doc
                docs["doc_template"]["jul"] = doc
                docs["doc_template"]["aug"] = doc
                docs["doc_template"]["sep"] = doc
                docs["doc_template"]["oct"] = doc
                docs["doc_template"]["nov"] = doc
                docs["doc_template"]["dec"] = doc
                continue
            if doc["type"] == "weekly_template":
                docs["doc_template"]["weekly"] = doc
                continue
            if doc["type"] == "monthly_folder":
                docs["doc_folder"]["jan"] = doc
                docs["doc_folder"]["feb"] = doc
                docs["doc_folder"]["mar"] = doc
                docs["doc_folder"]["apr"] = doc
                docs["doc_folder"]["may"] = doc
                docs["doc_folder"]["jun"] = doc
                docs["doc_folder"]["jul"] = doc
                docs["doc_folder"]["aug"] = doc
                docs["doc_folder"]["sep"] = doc
                docs["doc_folder"]["oct"] = doc
                docs["doc_folder"]["nov"] = doc
                docs["doc_folder"]["dec"] = doc
                continue
            if doc["type"] == "weekly_folder":
                docs["doc_folder"]["weekly"] = doc
                continue
            if doc["type"] in ["career_plan_template", "career_plan_folder", "okr_folder", "okr_template"]:
                output["docs"][doc["type"]] = doc

        for group in db_json["groups"]:
            output["groups"][group["type"]] = group

        for team in db_json["teams"]:
            for leader in db_json["leaders"]:
                if leader["id"] == team["leader_id"]:
                    team["leader_name"] = leader["name"]
                    team["meeting_1on1_weekth"] = leader["meeting_1on1_weekth"]
                    team["meeting_1on1_weekday"] = leader["meeting_1on1_weekday"]
                    team["meeting_1on1_time"] = leader["meeting_1on1_time"]
                    break
            output["teams"].append(team)

        message_templates = {}
        for message_template in db_json["message_templates"]:
            if message_template["type"] not in message_templates.keys():
                message_templates[message_template["type"]] = {}
            message_templates[message_template["type"]][message_template["group"]] = message_template["content"]
        for schedule in db_json["schedules"]:
            output["schedules"][schedule["type"]] = schedule
            output["schedules"][schedule["type"]]["kernel_content"] = message_templates[schedule["type"]]["kernel"]
            if schedule["type"] != 'weekly':
                output["schedules"][schedule["type"]]["team_content"] = message_templates[schedule["type"]]["team"]
            output["schedules"][schedule["type"]]["doc_template"] = docs["doc_template"][schedule["type"]]
            output["schedules"][schedule["type"]]["doc_folder"] = docs["doc_folder"][schedule["type"]]

        return output

    @staticmethod
    def input_to_db(input_json):
        db_json = {}
        if "cancelled_weekly_meetings" in input_json.keys():
            db_json["cancelled_weekly_meetings"] = []
            for cwm in input_json["cancelled_weekly_meetings"]:
                db_json["cancelled_weekly_meetings"].append(cwm)

        if "groups" in input_json.keys():
            db_json["groups"] = []
            if "kernel" in input_json["groups"].keys():
                temp_var = {
                    "id": input_json["groups"]["kernel"]["id"],
                    "type": "kernel",
                    "name": input_json["groups"]["kernel"]["name"]
                }
                db_json["groups"].append(temp_var)
            if "team" in input_json["groups"].keys():
                temp_var = {
                    "id": input_json["groups"]["team"]["id"],
                    "type": "team",
                    "name": input_json["groups"]["team"]["name"]
                }
                db_json["groups"].append(temp_var)
        if "teams" in input_json.keys():
            db_json["teams"] = []
            db_json["leaders"] = []

            leaders = {}
            for team in input_json["teams"]:
                temp_var = {
                    'name': team["name"],
                    'leader_id': team["leader_id"]
                }
                db_json["teams"].append(temp_var)
                leaders[team["leader_id"]] = team

            for leader in leaders.values():
                temp_var = {
                    "id": leader["leader_id"],
                    "name": leader["leader_name"],
                    "meeting_1on1_weekth": leader["meeting_1on1_weekth"],
                    "meeting_1on1_weekday": leader["meeting_1on1_weekday"],
                    "meeting_1on1_time": leader["meeting_1on1_time"]
                }
                db_json["leaders"].append(temp_var)
        if "schedules" in input_json.keys():
            db_json["schedules"] = []
            db_json["message_templates"] = []

            for key in input_json["schedules"]:
                temp_var1 = {
                    "type": key,
                    "notification_date": input_json["schedules"][key]["notification_date"],
                    "notification_time": input_json["schedules"][key]["notification_time"],
                    "ready_date": input_json["schedules"][key]["ready_date"],
                    "ready_time": input_json["schedules"][key]["ready_time"],
                    "start_date": input_json["schedules"][key]["start_date"],
                    "start_time": input_json["schedules"][key]["start_time"]
                }
                db_json["schedules"].append(temp_var1)
                temp_var2 = {
                    "type": key,
                    "group": "kernel",
                    "content": input_json["schedules"][key]["kernel_content"]
                }
                db_json["message_templates"].append(temp_var2)
                if key != 'weekly':
                    temp_var3 = {
                        "type": key,
                        "group": "team",
                        "content": input_json["schedules"][key]["team_content"]
                    }
                    db_json["message_templates"].append(temp_var3)
        current_app.logger.info(db_json)
        return db_json


class ToolView(Resource):

    def post(self):
        args = actions_parser.parse_args()
        actions = args['actions']
        commands = ["complain"]
        session_from_code = feishu_api_client.get_session_from_code(args['Authorization-Code'], True)
        open_id = session_from_code["data"]["open_id"]
        if "complain" in actions.keys():
            director_id = Group.query.filter_by(id=actions["complain"]["group_id"]).first().director_id
            director_last_name = Director.query.filter_by(id=director_id).first().name[0:1]
            text_content = "{\"text\":\"" + actions["complain"]["user_name"] + ": " + actions["complain"][
                "content"] + "\"}"
            feishu_api_client.send("open_id", director_id, text_content)
            text_content = "{\"text\":\"收到，稍晚" + director_last_name + "总会直接找您：）\"}"
            feishu_api_client.send("open_id", open_id, text_content)
            return {"errno": 1, "errmsg": "成功找到组织"}
        return {"errno": 0, "errmsg": "没有动作被执行"}

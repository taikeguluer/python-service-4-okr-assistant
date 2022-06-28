from oas.db.model import Director, CancelledWeeklyMeeting, Group, Doc, Leader, MessageTemplate, Schedule, Team
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field


class DirectorSchema(SQLAlchemySchema):
    class Meta:
        model = Director
        load_instance = True

    id = auto_field()
    name = auto_field()


class CancelledWeeklyMeetingSchema(SQLAlchemySchema):
    class Meta:
        model = CancelledWeeklyMeeting
        load_instance = True

    cancelled_notification_date = auto_field()


class DocSchema(SQLAlchemySchema):
    class Meta:
        model = Doc
        load_instance = True

    token = auto_field()
    name = auto_field()
    url = auto_field()
    type = auto_field()


class GroupSchema(SQLAlchemySchema):
    class Meta:
        model = Group
        load_instance = True

    id = auto_field()
    name = auto_field()
    type = auto_field()


class LeaderSchema(SQLAlchemySchema):
    class Meta:
        model = Leader
        load_instance = True

    id = auto_field()
    name = auto_field()
    meeting_1on1_weekth = auto_field()
    meeting_1on1_weekday = auto_field()
    meeting_1on1_time = auto_field()


class MessageTemplateSchema(SQLAlchemySchema):
    class Meta:
        model = MessageTemplate
        load_instance = True

    content = auto_field()
    type = auto_field()
    group = auto_field()


class ScheduleSchema(SQLAlchemySchema):
    class Meta:
        model = Schedule
        load_instance = True

    type = auto_field()
    notification_date = auto_field()
    ready_date = auto_field()
    start_date = auto_field()
    notification_time = auto_field()
    ready_time = auto_field()
    start_time = auto_field()


class TeamSchema(SQLAlchemySchema):
    class Meta:
        model = Team
        load_instance = True

    name = auto_field()
    leader_id = auto_field()

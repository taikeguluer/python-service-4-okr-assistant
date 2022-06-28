from oas.manager import db


class Director(db.Model):
    __tablename__ = "director"

    id = db.Column(db.String(100), primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    cancelled_weekly_meetings = db.relationship('CancelledWeeklyMeeting', backref='director',
                                                lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True)
    docs = db.relationship('Doc', backref='director', lazy='dynamic', cascade='all, delete-orphan',
                           passive_deletes=True)
    groups = db.relationship('Group', backref='director', lazy='dynamic', cascade='all, delete-orphan',
                             passive_deletes=True)
    leaders = db.relationship('Leader', backref='director', lazy='dynamic', cascade='all, delete-orphan',
                              passive_deletes=True)
    message_templates = db.relationship('MessageTemplate', backref='director', lazy='dynamic',
                                        cascade='all, delete-orphan', passive_deletes=True)
    schedules = db.relationship('Schedule', backref='director', lazy='dynamic', cascade='all, delete-orphan',
                                passive_deletes=True)
    teams = db.relationship('Team', backref='director', lazy='dynamic', cascade='all, delete-orphan',
                            passive_deletes=True)
    ranks = db.relationship('Rank', backref='director', lazy='dynamic', cascade='all, delete-orphan',
                            passive_deletes=True)

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return '<Director {}>'.format(self.name)

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class CancelledWeeklyMeeting(db.Model):
    __tablename__ = "cancelled_weekly_meeting"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    # yyyy-mm-dd
    cancelled_notification_date = db.Column(db.String(50), nullable=False)
    director_id = db.Column(db.String(100), db.ForeignKey('director.id', ondelete='CASCADE'))

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class Doc(db.Model):
    __tablename__ = "doc"

    token = db.Column(db.String(100), primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    # career_plan_template, career_plan_folder, weekly_template, weekly_folder, monthly_template, monthly_folder
    # okr_folder, okr_template
    type = db.Column(db.String(50), nullable=False)
    director_id = db.Column(db.String(100), db.ForeignKey('director.id', ondelete='CASCADE'))

    def __init__(self, token, name, url, type, director_id):
        self.token = token
        self.name = name
        self.url = url
        self.type = type
        self.director_id = director_id

    def __repr__(self):
        return '<Doc {}>'.format(self.name)

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class Group(db.Model):
    __tablename__ = "group"

    id = db.Column(db.String(100), primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    # kernel, team
    type = db.Column(db.String(50), nullable=False)
    director_id = db.Column(db.String(100), db.ForeignKey('director.id', ondelete='CASCADE'))

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class Leader(db.Model):
    __tablename__ = "leader"

    id = db.Column(db.String(100), primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    meeting_1on1_weekth = db.Column(db.Integer, nullable=False)
    meeting_1on1_weekday = db.Column(db.Integer, nullable=False)
    # hh:mm
    meeting_1on1_time = db.Column(db.String(50), nullable=False)
    director_id = db.Column(db.String(100), db.ForeignKey('director.id', ondelete='CASCADE'))

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class MessageTemplate(db.Model):
    __tablename__ = "message_template"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    # weekly, jan, ..., dec
    type = db.Column(db.String(50), nullable=False)
    # kernel, team,
    group = db.Column(db.String(50), nullable=False)
    director_id = db.Column(db.String(100), db.ForeignKey('director.id', ondelete='CASCADE'))

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class Schedule(db.Model):
    __tablename__ = "schedule"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    # weekly, jan, ..., dec
    type = db.Column(db.String(50), nullable=False)
    # weekly: w,1<=w<=7
    # other: yyyy-mm-dd
    notification_date = db.Column(db.String(50), nullable=False)
    # hh:mm
    notification_time = db.Column(db.String(50), nullable=False)
    # weekly: w,1<=w<=7
    # other: yyyy-mm-dd
    ready_date = db.Column(db.String(50), nullable=False)
    # hh:mm
    ready_time = db.Column(db.String(50), nullable=False)
    # weekly: w,1<=w<=7
    # other: yyyy-mm-dd
    start_date = db.Column(db.String(50), nullable=False)
    # hh:mm
    start_time = db.Column(db.String(50), nullable=False)
    director_id = db.Column(db.String(100), db.ForeignKey('director.id', ondelete='CASCADE'))
    # weekly: w,1<=w<=7
    # other: yyyy-mm-dd
    queued_date = db.Column(db.String(50))
    # hh:mm
    queued_time = db.Column(db.String(50))
    queued_task_id = db.Column(db.String(100))

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class Team(db.Model):
    __tablename__ = "team"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    leader_id = db.Column(db.String(100))
    director_id = db.Column(db.String(100), db.ForeignKey('director.id', ondelete='CASCADE'))

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class Rank(db.Model):
    __tablename__ = "rank"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    judge_id = db.Column(db.String(100), nullable=False)
    leader_id = db.Column(db.String(100))
    schedule_id = db.Column(db.Integer)
    director_id = db.Column(db.String(100), db.ForeignKey('director.id', ondelete='CASCADE'))

    def __repr__(self):
        return '<Rank {}>'.format(self.judge_id)

    def to_json(self):
        if hasattr(self, '__table__'):
            return {i.name: getattr(self, i.name) for i in self.__table__.columns}
        raise AssertionError('<%r> does not have attribute for __table__' % self)

from app import app, db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from sqlalchemy.sql import func

# authorization
roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("role_id", db.String(255), db.ForeignKey("role.role_id")),
)


class Role(db.Model):
    role_id = db.Column(db.String(255), primary_key=True)
    description = db.Column(db.Text())
    is_active = db.Column(db.Boolean(), default=True)

    def __repr__(self):
        return "<Role {}>".format(self.role_id)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_date = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    phrases = db.relationship("UserPhrase")
    documents = db.relationship("Document")
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=blank&s={}".format(digest, size)

    def get_roles(self):
        # return a list of role names
        roles = [r.role_id for r in self.roles]
        return roles if len(roles) > 0 else None

    def has_role(self, role=None):
        return role in [r.role_id for r in self.roles]

    def add_role(self, role=None):
        if not self.has_role(role):
            this_role = Role.query.get(role)
            if not this_role:
                raise Exception("Role not found: {}".format(role))
            self.roles.append(this_role)
            db.session.commit()

    def remove_role(self, role=None):
        if self.has_role(role):
            this_role = Role.query.get(role)
            if not this_role:
                raise Exception("Role not found: {}".format(role))
            self.roles.remove(this_role)
            db.session.commit()
        else:
            raise Exception("User does not have role: {}".format(role))

    @staticmethod
    def get_all():
        return User.query.all()

    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

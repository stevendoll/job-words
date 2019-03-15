#!/usr/bin/env python
import datetime as dt
from datetime import timedelta
import unittest
from app import app, db
from config import TestConfig

import os
from config import basedir

app.config.from_object(TestConfig)

from app.models import User, Role, Phrase, UserPhrase, Finding, PhraseGroup


class StartupCase(unittest.TestCase):
    def setUp(self):
 
        self.app = app
        self.client = self.app.test_client

        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_index(self):
        response = self.client().get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Job Words', str(response.data))


class UserCase(unittest.TestCase):
    def setUp(self):

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        self.app = app
        self.app.client = app.test_client()


        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

        # registered user
        u1 = User(username='john', email='john@example.com')
        u1.set_password('johnpassword')

        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self, username, password):
        return self.app.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.client.get('/logout', follow_redirects=True)

    def register(self, username, email, password, password2):
        return self.app.client.post('/signup', data=dict(
            username=username,
            email=email,
            password=password,
            password2=password2,
        ), follow_redirects=True)

    def test_get_user(self):
        username = 'john'
        user_in_db = db.session.query(User).filter_by(username=username).first()
        self.assertEqual(user_in_db.email, 'john@example.com')

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_login_logout(self):
 
        response = self.login('john','johnpassword')
        self.assertIn('Logout', str(response.data))
        self.assertIn('Welcome back john', str(response.data))

        response = self.logout()
        self.assertIn('Goodbye', str(response.data)) 
        self.assertIn('Login', str(response.data))
        self.assertNotIn('Welcome back john', str(response.data))

        response = self.login('john','notpassword')
        self.assertIn('Invalid username or password', str(response.data))

        self.logout()
        response = self.login('susan','johnpassword')
        self.assertIn('Invalid username or password', str(response.data))


    def test_register(self):
 
        # add to db if doesn't exist, convert to lowercase
        result = self.register('anneusername', 'anne@example.com', 'annpassword', 'annpassword')
        self.assertIn('Congratulations, you are now a registered user!', str(result.data))        

        result = self.login('anneusername','annpassword')
        self.assertIn('Logout', str(result.data))        
        self.assertIn('Welcome back anneusername', str(result.data))
        self.logout()

        # redirect to login if already registered
        result = self.register('john', 'john@example.com', 'johnpassword', 'johnpassword')
        self.assertIn('Have you already registered? Otherwise please use a different username.', str(result.data))        

    def test_user_list_protected(self):
        response = self.app.client.get('/users', content_type='teml/text')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('john', str(response.data))
        self.assertIn('You should be redirected automatically to target URL: <a href="/login?next=%2Fusers">/login?next=%2Fusers</a>', str(response.data))

    def test_user_list(self):
        self.login('john','johnpassword')
        response = self.app.client.get('/users',follow_redirects=True)
        
        self.assertIn('john', str(response.data))
        self.assertIn('susan@example.com', str(response.data))


    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=blank&s=128'))

class RoleCase(unittest.TestCase):
    def setUp(self):

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        self.app = app
        self.app.client = app.test_client()


        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

        r1 = Role(role_id='Pawn')
        r2 = Role(role_id='Rook')
        r3 = Role(role_id='Queen')
        r4 = Role(role_id='Knight')
        db.session.add_all([r1, r2, r3, r4])

        # registered user
        u1 = User(username='patricia', email='patricia@example.com')
        u1.set_password('patriciapassword')
        u1.roles.append(r1)
        u1.roles.append(r2)

        u2 = User(username='felicia', email='felicia@example.com')
        u2.set_password('feliciapassword')

        u3 = User(username='denise', email='denise@example.com')

        db.session.add_all([u1, u2, u3])

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # role in db
    def test_role_in_db(self):
        role_in_db = Role.query.get('Pawn')
        self.assertNotEqual(role_in_db, None)

    # can get roles
    def test_get_roles(self):
        user_with_roles = User.get_by_username('patricia')
        
        roles = user_with_roles.get_roles()

        self.assertTrue('Pawn' in roles)
        self.assertTrue('Rook' in roles)
        self.assertEqual(len(roles), 2)

    # can check if user has role
    def test_has_role(self):
        admin_user = User.get_by_username('patricia')
        self.assertTrue(admin_user.has_role('Pawn'))
        self.assertTrue(admin_user.has_role('Rook'))
        self.assertFalse(admin_user.has_role('Knight'))
        self.assertFalse(admin_user.has_role('Joker'))
        self.assertFalse(admin_user.has_role())
        self.assertFalse(admin_user.has_role(''))

    # can add role
    def test_add_role(self):
        user = User.get_by_username('patricia')
        self.assertFalse(user.has_role('Knight'))

        user.add_role('Knight')
        self.assertTrue(user.has_role('Knight'))

    # add role that doesn't exist raises exception
    def test_add_role_not_found(self):
        user = User.get_by_username('patricia')
        self.assertFalse(user.has_role('Joker'))

        self.assertRaises(Exception, user.add_role, 'Joker')

    # can remove role
    def test_remove_role(self):
        user = User.get_by_username('patricia')
        self.assertTrue(user.has_role('Rook'))

        user.remove_role('Rook')
        self.assertFalse(user.has_role('Rook'))
        self.assertTrue(user.has_role('Pawn')) # still has other role

    # remove role that doesn't exist raises exception
    def test_remove_role_not_found(self):
        user = User.get_by_username('patricia')
        self.assertFalse(user.has_role('Joker'))

        self.assertRaises(Exception, user.remove_role, 'Joker')

    # default user has no roles
    def test_default_user_has_no_roles(self):
        # home page
        result = self.app.client.get('/')
        self.assertEqual(result.status_code, 200)

        user = User.get_by_username('denise')
        self.assertEqual(user.get_roles(), None)

    # registered user has User role
    def test_registered_user_has_no_role(self):

        # looks up user if doesn't exist
        result = UserCase.register(self, 'anne','anne@example.com','annepassword','annepassword')
        self.assertIn('Congratulations, you are now a registered user!', str(result.data))        

        user = User.get_by_username('anne')
        self.assertEqual(user.get_roles(), None)
        self.assertFalse(user.has_role('User'))
        self.assertFalse(user.has_role('Admin'))

    # def test_phrase_group_list_not_authenticated(self):
    #     result = self.app.client.get('/documents', content_type='html/text')
    #     self.assertEqual(result.status_code, 302)
    #     self.assertNotIn('API incremental update started', str(result.data))
    #     self.assertIn('You should be redirected automatically to target URL: <a href="/login?next=%2Fapis%2Fdx-queue%2Fupdate">/login?next=%2Fapis%2Fdx-queue%2Fupdate</a>', str(result.data))

    #     result = self.app.client.get('/apis/dx-queue/refresh', content_type='html/text')
    #     self.assertEqual(result.status_code, 302)
    #     self.assertNotIn('Rebuilding all API records.', str(result.data))
    #     self.assertIn('You should be redirected automatically to target URL: <a href="/login?next=%2Fapis%2Fdx-queue%2Frefresh">/login?next=%2Fapis%2Fdx-queue%2Frefresh</a>', str(result.data))

    # def test_stream_update_not_authenticated(self):
    #     result = self.app.client.get('/streams/dx-queue/update', content_type='html/text')
    #     self.assertEqual(result.status_code, 302)
    #     self.assertNotIn('Stream incremental update started', str(result.data))
    #     self.assertIn('You should be redirected automatically to target URL: <a href="/login?next=%2Fstreams%2Fdx-queue%2Fupdate">/login?next=%2Fstreams%2Fdx-queue%2Fupdate</a>', str(result.data))

    #     result = self.app.client.get('/streams/dx-queue/refresh', content_type='html/text')
    #     self.assertEqual(result.status_code, 302)
    #     self.assertNotIn('Rebuilding all Stream records.', str(result.data))
    #     self.assertIn('You should be redirected automatically to target URL: <a href="/login?next=%2Fstreams%2Fdx-queue%2Frefresh">/login?next=%2Fstreams%2Fdx-queue%2Frefresh</a>', str(result.data))


# class AuthorizationCase(unittest.TestCase):
#     def setUp(self):

#         app.config['TESTING'] = True
#         app.config['WTF_CSRF_ENABLED'] = False

#         self.app = app
#         self.app.client = app.test_client()


#         with self.app.app_context():
#             db.session.remove()
#             db.drop_all()
#             db.create_all()

#         r1 = Role(role_id='Admin')
#         r2 = Role(role_id='ApiDxReviewer')
#         r3 = Role(role_id='StreamDxReviewer')
#         r4 = Role(role_id='ApiCoach')
#         r5 = Role(role_id='StreamCoach')

#         db.session.add_all([r1, r2, r3, r4, r5])

#         u1 = User(user_eid='abc001', first_name='AdminUser')
#         u1.set_password('abc001password')
#         u1.roles.append(r1)

#         u2 = User(user_eid='abc002', first_name='ApiDxReviewerUser')
#         u2.set_password('abc002password')
#         u2.roles.append(r2)

#         u3 = User(user_eid='abc003', first_name='StreamDxReviewerUser')
#         u3.set_password('abc003password')
#         u3.roles.append(r3)

#         u4 = User(user_eid='abc004', first_name='ApiCoachUser')
#         u4.set_password('abc004password')
#         u4.roles.append(r4)

#         u5 = User(user_eid='abc005', first_name='StreamCoachUser')
#         u5.set_password('abc005password')
#         u5.roles.append(r5)

#         u6 = User(user_eid='abc006', first_name='Nobody')
#         u6.set_password('abc006password')
#         u1.roles.append(r1)

#         db.session.add_all([u1, u2, u3, u4, u5, u6])

#         db.session.commit()

#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()

#     def test_admin_not_authorized(self):
#         result = UserTestCase.login(self, 'abc006','abc006password')

#         # is logged in
#         self.assertIn('Nobody', str(result.data))
#         self.assertIn('Logout', str(result.data))

#         # doesn't have rights to update dx queue
#         result = self.app.client.get('/apis/dx-queue/refresh', follow_redirects=True)
#         self.assertNotIn('Admin', str(result.data)) # not in menu
#         self.assertNotIn('/apis/dx-queue/refresh', str(result.data)) # not in menu
#         self.assertIn('Not authorized. You do not have a role that allows access to this feature.', str(result.data))
#         self.assertNotIn('Rebuilding all API records', str(result.data))

#         UserTestCase.logout(self)
        
#         # login as api dx reviewer
#         result = UserTestCase.login(self, 'abc002','abc002password')

#         # is logged in
#         self.assertIn('ApiDxReviewerUser', str(result.data))
#         self.assertIn('Logout', str(result.data))

#         # doesn't have rights to refresh api dx queue
#         result = self.app.client.get('/apis/dx-queue/refresh', follow_redirects=True)
#         self.assertNotIn('/apis/dx-queue/refresh', str(result.data)) # not in menu
#         self.assertIn('Not authorized. You do not have a role that allows access to this feature.', str(result.data))
#         self.assertNotIn('Rebuilding all API records', str(result.data))

#         # doesn't have rights to refresh stream dx queue
#         result = self.app.client.get('/streams/dx-queue/refresh', follow_redirects=True)
#         self.assertNotIn('/streams/dx-queue/refresh', str(result.data)) # not in menu
#         self.assertIn('Not authorized. You do not have a role that allows access to this feature.', str(result.data))
#         self.assertNotIn('Rebuilding all Stream records', str(result.data))

#     def test_admin_authorized(self):
#         UserTestCase.login(self, 'abc001','abc001password')

#         result = self.app.client.get('/apis/dx-queue/refresh', follow_redirects=True)
#         self.assertIn('Admin', str(result.data)) # in menu
#         self.assertIn('/apis/dx-queue/refresh', str(result.data)) # in menu
#         self.assertNotIn('Not authorized. You do not have a role that allows access to this feature.', str(result.data))
#         self.assertIn('Rebuilding all API records', str(result.data))

#     def test_api_update_not_authorized(self):
#         result = UserTestCase.login(self, 'abc006','abc006password')

#         # is logged in
#         self.assertIn('Nobody', str(result.data))
#         self.assertIn('Logout', str(result.data))

#         # doesn't have rights to update dx queue
#         result = self.app.client.get('/apis/dx-queue/update', follow_redirects=True)
#         self.assertNotIn('/apis/dx-queue/update', str(result.data)) # not in menu
#         self.assertIn('Not authorized. You do not have a role that allows access to this feature.', str(result.data))
#         self.assertNotIn('API incremental update started', str(result.data))

#         UserTestCase.logout(self)
        
#         # login as stream coach
#         result = UserTestCase.login(self, 'abc005','abc005password')

#         # is logged in
#         self.assertIn('StreamCoachUser', str(result.data))
#         self.assertIn('Logout', str(result.data))

#         # doesn't have rights to update dx queue
#         result = self.app.client.get('/apis/dx-queue/update', follow_redirects=True)
#         self.assertNotIn('/apis/dx-queue/update', str(result.data)) # not in menu
#         self.assertIn('Not authorized. You do not have a role that allows access to this feature.', str(result.data))
#         self.assertNotIn('API incremental update started', str(result.data))

#     def test_stream_update_not_authorized(self):
#         result = UserTestCase.login(self, 'abc006','abc006password')

#         # is logged in
#         self.assertIn('Nobody', str(result.data))
#         self.assertIn('Logout', str(result.data))

#         # doesn't have rights to update dx queue
#         result = self.app.client.get('/streams/dx-queue/update', follow_redirects=True)
#         self.assertNotIn('/streams/dx-queue/update', str(result.data)) # not in menu
#         self.assertIn('Not authorized. You do not have a role that allows access to this feature.', str(result.data))
#         self.assertNotIn('Stream incremental update started', str(result.data))

#         UserTestCase.logout(self)
        
#         # login as api coach
#         result = UserTestCase.login(self, 'abc004','abc004password')

#         # is logged in
#         self.assertIn('ApiCoachUser', str(result.data))
#         self.assertIn('Logout', str(result.data))

#         # doesn't have rights to update dx queue
#         result = self.app.client.get('/streams/dx-queue/update', follow_redirects=True)
#         self.assertNotIn('/streams/dx-queue/update', str(result.data)) # not in menu
#         self.assertIn('Not authorized. You do not have a role that allows access to this feature.', str(result.data))
#         self.assertNotIn('API incremental update started', str(result.data))

#     def test_api_update_authorized(self):

#         # abc001 AdminUser
#         # abc002 ApiDxReviewerUser
#         # abc003 StreamDxReviewerUser
#         # abc004 ApiCoachUser
#         # abc005 StreamCoachUser
#         # abc006 Nobody

#         UserTestCase.login(self, 'abc001','abc001password')

#         result = self.app.client.get('/apis/dx-queue/update', follow_redirects=True)
#         self.assertIn('/apis/dx-queue/update', str(result.data)) # in menu
#         self.assertIn('AdminUser', str(result.data))
#         self.assertIn('API incremental update started', str(result.data))

#         UserTestCase.logout(self)
        
#         # confirm logout
#         result = self.app.client.get('/apis/dx-queue/update', follow_redirects=True)
#         self.assertIn('Please log in to access this page.', str(result.data))


#         UserTestCase.login(self, 'abc002','abc002password')

#         result = self.app.client.get('/apis/dx-queue/update', follow_redirects=True)
#         self.assertIn('/apis/dx-queue/update', str(result.data)) # in menu
#         self.assertIn('ApiDxReviewerUser', str(result.data))
#         self.assertIn('API incremental update started', str(result.data))

#         UserTestCase.logout(self)

#         UserTestCase.login(self, 'abc004','abc004password')

#         result = self.app.client.get('/apis/dx-queue/update', follow_redirects=True)
#         self.assertIn('/apis/dx-queue/update', str(result.data)) # in menu
#         self.assertIn('ApiCoachUser', str(result.data))
#         self.assertIn('API incremental update started', str(result.data))

#         UserTestCase.logout(self)

#     def test_stream_update_authorized(self):

#         # abc001 AdminUser
#         # abc002 ApiDxReviewerUser
#         # abc003 StreamDxReviewerUser
#         # abc004 ApiCoachUser
#         # abc005 StreamCoachUser
#         # abc006 Nobody

#         UserTestCase.login(self, 'abc001','abc001password')

#         result = self.app.client.get('/streams/dx-queue/update', follow_redirects=True)
#         self.assertIn('/streams/dx-queue/update', str(result.data)) # in menu
#         self.assertIn('AdminUser', str(result.data))
#         self.assertIn('Stream incremental update started', str(result.data))

#         UserTestCase.logout(self)
        
#         # confirm logout
#         result = self.app.client.get('/streams/dx-queue/update', follow_redirects=True)
#         self.assertIn('Please log in to access this page.', str(result.data))


#         UserTestCase.login(self, 'abc003','abc003password')

#         result = self.app.client.get('/streams/dx-queue/update', follow_redirects=True)
#         self.assertIn('/streams/dx-queue/update', str(result.data)) # in menu
#         self.assertIn('StreamDxReviewerUser', str(result.data))
#         self.assertIn('Stream incremental update started', str(result.data))

#         UserTestCase.logout(self)

#         UserTestCase.login(self, 'abc005','abc005password')

#         result = self.app.client.get('/streams/dx-queue/update', follow_redirects=True)
#         self.assertIn('/streams/dx-queue/update', str(result.data)) # in menu
#         self.assertIn('StreamCoachUser', str(result.data))
#         self.assertIn('Stream incremental update started', str(result.data))

#         UserTestCase.logout(self)


class InitializeCase(unittest.TestCase):
    def setUp(self):

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        self.app = app
        self.app.client = app.test_client()


        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

        # admin user
        u1 = User(username='stevendoll', email='steven@example.com')
        u1.set_password('stevenpassword')
        db.session.add(u1)
        db.session.commit()


    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # setup roles and users
    def test_setup(self):
        result = self.app.client.get('/initialize', follow_redirects=True)
        self.assertEqual(result.status_code, 200) # redirect to api list
        self.assertIn('Dashboard initialized', str(result.data))        

        user = User.get_by_username('stevendoll')
        self.assertTrue(user.has_role('Admin'))

    def test_setup_only_runs_once(self):
        self.app.client.get('/initialize')
        result = self.app.client.get('/initialize', follow_redirects=True)
        self.assertEqual(result.status_code, 200) # redirect to api list
        self.assertIn('Already initialized', str(result.data))        


class PhraseCase(unittest.TestCase):
    def setUp(self):
        UserCase.setUp(self)

        # search phrase
        p1 = Phrase(phrase_text='project manager', slug='project-manager')
        db.session.add(p1)
        db.session.commit()

    def tearDown(self):
        UserCase.tearDown(self)

    def login(self, username, password):
        return UserCase.login(self, username, password)

    def logout(self):
        return UserCase.logout(self)

    def test_get_phrase(self):
        # search phrase
        phrase_text = 'project manager'
        phrase_in_db = db.session.query(Phrase).filter_by(phrase_text=phrase_text).first()
        self.assertEqual(phrase_in_db.phrase_text, phrase_text)

    def test_view_phrase(self):
        response = self.app.client.get('/phrases/project-manager', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('project manager', str(response.data))

    def test_create_phrase(self):
        # phrase not found, should create
        term = 'linux'

        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertIn(term, str(response.data))

        term = 'Accountant' # lowercase

        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertNotIn(term, str(response.data))
        self.assertIn(term.lower(), str(response.data))

        term = 'project management' # keep spaces

        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertIn(term, str(response.data))

        term = ' mechanical engineer ' # trim

        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertNotIn(' mechanical engineer ', str(response.data))


    def test_update_phrase(self):
        # if already exists, don't create a new one, instead update counter and date
        term = 'linux'

        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(term, str(response.data))

        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('searched 2 times.', str(response.data))
        self.assertIn(term, str(response.data))

        term_with_junk = ' LINUX$$ ' # trim

        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('searched 3 times.', str(response.data))
        self.assertIn(term, str(response.data))
        self.assertNotIn(term_with_junk, str(response.data))

    def test_generate_phrase_slug(self):

        slug = 'angularjs-node.js'
        term_with_junk = ' AngularJS Node.js'

        response = self.app.client.get('/phrases?term=' + term_with_junk, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertIn(slug, str(response.data))

        term_with_junk = '  AngularJS   Node.js'

        response = self.app.client.get('/phrases?term=' + term_with_junk, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('searched 2 times.', str(response.data))
        self.assertIn(slug, str(response.data))

        term_with_junk = '.  ..AngularJS ..Node.js.'

        response = self.app.client.get('/phrases?term=' + term_with_junk, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('searched 3 times.', str(response.data))
        self.assertIn(slug, str(response.data))

        response = self.app.client.get('/phrases/' + slug, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('angularjs node.js', str(response.data))

        slug = 'scikit-learn-python'
        term_with_junk = '  scikit-learn.. python.'

        response = self.app.client.get('/phrases?term=' + term_with_junk, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertIn(slug, str(response.data))

        response = self.app.client.get('/phrases/' + slug, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('scikit-learn python', str(response.data))


class UserPhraseCase(unittest.TestCase):
    def setUp(self):
        UserCase.setUp(self)

        # create users
        u1 = User(username='jack', email='jack@example.com')
        u2 = User(username='mary', email='mary@example.com')
        u2.set_password('marypassword')
        db.session.add_all([u1, u2])

        # create phrases
        p1 = Phrase(phrase_text='project manager', slug='project-manager')
        p2 = Phrase(phrase_text='nurse', slug='nurse')
        p3 = Phrase(phrase_text='engineer', slug='engineer')
        db.session.add_all([p1, p2, p3])

        # create user phrases
        up1 = UserPhrase(user=u1, phrase=p1) # jack is project manager
        up2 = UserPhrase(user=u2, phrase=p3) # mary is an engineer
        up3 = UserPhrase(user=u1, phrase=p3) # jack is an engineer
        up4 = UserPhrase(user=u1, phrase=p3) # jack searches again for engineer
        db.session.add_all([up1, up2, up3])
        db.session.commit()


    def tearDown(self):
        UserCase.tearDown(self)

    def login(self, username, password):
        return UserCase.login(self, username, password)

    def logout(self):
        return UserCase.logout(self)

    def test_get_user_phrase(self):
        # search phrase
        user_in_db = db.session.query(User).filter_by(username='jack').first()
        phrase_in_db = db.session.query(Phrase).filter_by(phrase_text='engineer').first()
        user_phrase_in_db = db.session.query(UserPhrase).filter_by(phrase_id=phrase_in_db.id, user_id=user_in_db.id).first()
        self.assertEqual(user_phrase_in_db.user_id, user_in_db.id)

    def test_view_user_phrase(self):
        # authenticated
        self.login('mary','marypassword')
        response = self.app.client.get('/users/mary/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('project manager', str(response.data))
        self.assertIn('engineer', str(response.data))

    def test_create_user_phrase(self):
        # not authenticated
        response = self.app.client.get('/users', content_type='teml/text')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('john', str(response.data))
        self.assertIn('You should be redirected automatically to target URL: <a href="/login?next=%2Fusers">/login?next=%2Fusers</a>', str(response.data))

        # authenticated
        self.login('john','johnpassword')
        response = self.app.client.get('/users',follow_redirects=True)
        
        self.assertIn('john', str(response.data))
        self.assertIn('susan@example.com', str(response.data))

        term = 'fortran'

        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertIn(term, str(response.data))

        response = self.app.client.get('/users/john/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(term, str(response.data))


class FindingCase(unittest.TestCase):
    def setUp(self):
        UserCase.setUp(self)

        # create phrases
        p1 = Phrase(phrase_text='project manager', slug='project-manager')
        p2 = Phrase(phrase_text='nurse', slug='nurse')
        p3 = Phrase(phrase_text='engineer', slug='engineer')
        p4 = Phrase(phrase_text='tiger trainer', slug='tiger-trainer')
        db.session.add_all([p1, p2, p3, p4])

        # create findings
        f1 = Finding(phrase=p1, created_date=dt.datetime(2018,4,1,0,0,0), mean_salary=110000, jobs_count=30000, jobs_above_100k_count=5000)
        f2 = Finding(phrase=p3, created_date=dt.datetime(2018,8,15,0,0,0), mean_salary=85000, jobs_count=50000, jobs_above_100k_count=6000)
        f3 = Finding(phrase=p3, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=95000, jobs_count=60000, jobs_above_100k_count=7000)
        f4 = Finding(phrase=p4, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=95000, jobs_count=5, jobs_above_100k_count=1)
        f5 = Finding(phrase=p3, created_date=dt.datetime(2019,2,10,0,0,0), mean_salary=92000, jobs_count=62000, jobs_above_100k_count=7000)
        db.session.add_all([f1, f2, f3, f4, f5])
        db.session.commit()


    def tearDown(self):
        UserCase.tearDown(self)

    def login(self, username, password):
        return UserCase.login(self, username, password)

    def logout(self):
        return UserCase.logout(self)

    def test_get_finding(self):
        # search phrase
        phrase_in_db = db.session.query(Phrase).filter_by(phrase_text='engineer').first()
        finding_in_db = db.session.query(Finding).filter_by(phrase_id=phrase_in_db.id).first()
        self.assertNotEqual(finding_in_db, None)

    def test_get_latest_finding(self):
        # search phrase
        phrase_in_db = db.session.query(Phrase).filter_by(phrase_text='engineer').first()
        self.assertEqual(phrase_in_db.mean_salary, 95000)

    def test_view_phrase_in_list(self):
        # not authenticated
        response = self.app.client.get('/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('project manager', str(response.data))

    def test_view_phrase_in_api(self):
        # phrase does not appear because no finding
        response = self.app.client.get('/api/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('"phraseText": "project manager"', str(response.data))
        self.assertIn('"phraseCount": 2', str(response.data))

    def test_phrase_not_in_list_if_no_findings(self):
        # no findings so not in list
        response = self.app.client.get('/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('nurse', str(response.data))

    def test_phrase_not_in_list_if_few_jobs(self):
        # too few jobs so not in list
        response = self.app.client.get('/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('nurse', str(response.data))

    def test_view_finding(self):
        response = self.app.client.get('/phrases/project-manager', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('$110,000', str(response.data))

    def test_view_finding_in_api(self):
        # check api
        response = self.app.client.get('/api/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('"jobsCount": null', str(response.data))
        self.assertIn('"jobsCount": 30000', str(response.data))
        
        # only most recent finding
        self.assertNotIn('"jobsCount": 50000', str(response.data))
        self.assertIn('"jobsCount": 60000', str(response.data))

    def test_no_findings(self):
        response = self.app.client.get('/phrases/nurse', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('indeed results for _project_manager_', str(response.data))
        self.assertIn('no search findings', str(response.data))

    def test_dont_search_indeed_if_recent_finding_exists(self):
        
        # count findings
        initial_finding_count = db.session.query(Finding).count()

        # search term already in db and count findings
        term = 'engineer'
        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        second_finding_count = db.session.query(Finding).count()
        self.assertEqual(initial_finding_count, second_finding_count)

        # search new term and count findings
        term = 'mechanic'
        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        third_finding_count = db.session.query(Finding).count()
        self.assertEqual(second_finding_count + 1, third_finding_count)

        # search term again and count findings
        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        fourth_finding_count = db.session.query(Finding).count()
        self.assertEqual(third_finding_count, fourth_finding_count)
        
        # search old term already in db and count findings
        term = 'project manager'
        phrase = db.session.query(Phrase).filter_by(phrase_text=term).first()
        fifth_finding_count = db.session.query(Finding).filter_by(phrase=phrase).count()
        self.assertEqual(fifth_finding_count, 1)
        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        sixth_finding_count = db.session.query(Finding).filter_by(phrase=phrase).count()
        self.assertEqual(sixth_finding_count, 2)

    def test_view_finding_analysis(self):
        term = 'excel'
        response = self.app.client.get('/phrases?term=' + term, content_type='html/text')
        response = self.app.client.get('/phrases/' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertIn('with an average salary of $', str(response.data))

 
class DocumentCase(unittest.TestCase):
    def setUp(self):
        UserCase.setUp(self)

        # create users
        u1 = User(username='jack', email='jack@example.com')
        u2 = User(username='mary', email='mary@example.com')
        u2.set_password('marypassword')
        db.session.add_all([u1, u2])

        # create phrases
        d1 = PhraseGroup(title='jack resume', slug='jack-resume', user=u1)
        d2 = PhraseGroup(title='mary linkedin', slug='mary-linkedin', user=u2)
        d3 = PhraseGroup(title='mary resume', slug='mary-resume', user=u2)
        db.session.add_all([d1, d2, d3])

        # create phrases
        p1 = Phrase(phrase_text='project manager', slug='project-manager')
        p2 = Phrase(phrase_text='nurse', slug='nurse')
        p3 = Phrase(phrase_text='engineer', slug='engineer')
        p4 = Phrase(phrase_text='mechanical engineer', slug='mechanical-engineer')
        p5 = Phrase(phrase_text='tiger trainer', slug='tiger-trainer')
        db.session.add_all([p1, p2, p3, p4, p5])

        # create findings
        f1 = Finding(phrase=p1, created_date=dt.datetime(2018,4,1,0,0,0), mean_salary=110000, jobs_count=30000, jobs_above_100k_count=5000)
        f2 = Finding(phrase=p3, created_date=dt.datetime(2018,8,15,0,0,0), mean_salary=85000, jobs_count=50000, jobs_above_100k_count=6000)
        f3 = Finding(phrase=p3, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=95000, jobs_count=60000, jobs_above_100k_count=7000)
        f4 = Finding(phrase=p4, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=100000, jobs_count=40000, jobs_above_100k_count=7000)
        f5 = Finding(phrase=p5, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=60000, jobs_count=5, jobs_above_100k_count=1)
        db.session.add_all([f1, f2, f3, f4, f5])

        # associate phrases with users and phrase_groups
        up1 = UserPhrase(user=u1, phrase=p1, phrase_group=d1) # jack resume has project manager
        up2 = UserPhrase(user=u2, phrase=p4, phrase_group=d2) # mary linkedin profile has mechanical engineer
        up3 = UserPhrase(user=u2, phrase=p3, phrase_group=d3) # mary resume has engineer
        up4 = UserPhrase(user=u1, phrase=p3, phrase_group=d1) # jack resume has engineer
        db.session.add_all([up1, up2, up3, up4])


        db.session.commit()

    def tearDown(self):
        UserCase.tearDown(self)

    def login(self, username, password):
        return UserCase.login(self, username, password)

    def logout(self):
        return UserCase.logout(self)

    def create_document(self, title, body, username, password):
        self.login(username, password)

        return self.app.client.post('/documents', data=dict(
            title=title,
            body=body
        ), follow_redirects=True)

    def test_get_document(self):
        # search phrase
        title = 'jack resume'
        phrase_group_in_db = db.session.query(PhraseGroup).filter_by(title=title).first()
        self.assertEqual(phrase_group_in_db.title, title)

    def test_view_document_in_list(self):
        # not authenticated
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('jack resume', str(response.data))

    def test_create_document(self):
        title = 'mary resume'
        body = 'pilot'
        username = 'mary'
        password = 'marypassword'
        self.create_phrase_group(title, body, username, password)
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary resume', str(response.data))

    def test_generate_document_slug(self):

        # create a new phrase_group with the same title
        title = 'mary resume'
        body = 'minister'
        username = 'mary'
        password = 'marypassword'
        self.create_phrase_group(title, body, username, password)
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary resume', str(response.data))
        
        # check if 2 phrase_groups in db
        phrase_groups_in_db = db.session.query(PhraseGroup).filter_by(title=title).all()
        self.assertEqual(len(phrase_groups_in_db), 2)

        # check that slugs are different
        phrase_groups_in_db = db.session.query(PhraseGroup).filter_by(slug='mary-resume').all()
        self.assertEqual(len(phrase_groups_in_db), 1)

    def test_get_latest_finding_in_document_phrases(self):
        # search phrase
        phrase_group_in_db = PhraseGroup.query.filter_by(slug='mary-resume').first()
        self.assertEqual(phrase_group_in_db.phrases[0].phrase.mean_salary, 95000)

    def test_analyze_document_phrases(self):
        title = 'mary new resume'
        body = 'A confident digital product manager, data scientist, MBA and entrepreneur, I deliver outcomes - not outputs.'
        username = 'mary'
        password = 'marypassword'
        self.create_phrase_group(title, body, username, password)
        response = self.app.client.get('/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mba', str(response.data))
        self.assertIn('data scientist', str(response.data))

    def test_get_user_document(self):
        # search phrase
        user_in_db = db.session.query(User).filter_by(username='jack').first()
        phrase_group_in_db = db.session.query(PhraseGroup).filter_by(title='jack resume').first()
        self.assertEqual(phrase_group_in_db.user_id, user_in_db.id)

    def test_view_user_documents(self):
        # authenticated
        self.login('mary','marypassword')
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('jack resume', str(response.data))
        self.assertIn('mary linkedin', str(response.data))
        self.assertIn('mary resume', str(response.data))

    def test_create_user_document(self):
        username = 'mary'
        password = 'marypassword'
        self.login(username, password)
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary resume', str(response.data))

        title = 'mary cv'
        body = 'mary new body'
        self.create_phrase_group(title, body, username, password)
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary cv', str(response.data))

    def test_view_user_document(self):
        # authenticated
        self.login('mary','marypassword')
        response = self.app.client.get('/documents/mary-resume', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('jack resume', str(response.data))
        self.assertNotIn('mary linkedin', str(response.data))
        self.assertIn('mary resume', str(response.data))

    # a different user can't see the phrase_group with the slug
    # def test_view_user_phrase_group_authorized(self):
    #     self.login('john','johnpassword')
    #     response = self.app.client.get('/documents/mary-resume', content_type='html/text')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertNotIn('mary resume', str(response.data))

    #     response = self.app.client.get('/documents/mary-resume', content_type='html/text')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertNotIn('mary resume', str(response.data))

    # the phrase_group shows the top 5 phrases by most recent finding value

    # /api/documents/{slug}/phrases loaded in background
    def test_view_phrase_document_in_api(self):
        # check api
        response = self.app.client.get('/api/documents/mary-resume/phrases', content_type='html/text')
        # response = self.app.client.get('/api/documents/jack-resume/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('"jobsCount": null', str(response.data))

        # engineer
        self.assertIn('"phraseText": "engineer"', str(response.data))
        
        # not mechanical-engineer, that is in her linkedin profile
        self.assertNotIn('"phraseText": "mechanical engineer"', str(response.data))

        # not project manager, that is in jack's resume
        self.assertNotIn('"phraseText": "project manager"', str(response.data))
        
        # only most recent finding for engineer
        self.assertNotIn('"meanSalary": 85000', str(response.data))
        self.assertIn('"meanSalary": 95000', str(response.data))

class ComparisonCase(unittest.TestCase):
    def setUp(self):
        UserCase.setUp(self)

        # create users
        u1 = User(username='jack', email='jack@example.com')
        u2 = User(username='mary', email='mary@example.com')
        u2.set_password('marypassword')
        db.session.add_all([u1, u2])

        # create phrases
        d1 = PhraseGroup(title='programming', slug='programming-languages', user=u1)
        d2 = PhraseGroup(title='pink collar', slug='pink-collar')
        d3 = PhraseGroup(title='gender words', slug='gender-words', user=u2)
        db.session.add_all([d1, d2, d3])

        # create phrases
        p1 = Phrase(phrase_text='java', slug='java')
        p2 = Phrase(phrase_text='python', slug='python')
        p3 = Phrase(phrase_text='nurse', slug='nurse')
        p4 = Phrase(phrase_text='elementary school', slug='elementary-school')
        p5 = Phrase(phrase_text='collaborate', slug='collaborate')
        p6 = Phrase(phrase_text='leader', slug='leader')
        db.session.add_all([p1, p2, p3, p4, p5, p6])

        # create findings
        f1 = Finding(phrase=p1, created_date=dt.datetime(2018,4,1,0,0,0), mean_salary=110000, jobs_count=30000, jobs_above_100k_count=5000)
        f2 = Finding(phrase=p2, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=105000, jobs_count=30000, jobs_above_100k_count=5000)
        f3 = Finding(phrase=p3, created_date=dt.datetime(2018,8,15,0,0,0), mean_salary=85000, jobs_count=50000, jobs_above_100k_count=6000)
        f4 = Finding(phrase=p3, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=95000, jobs_count=60000, jobs_above_100k_count=7000)
        f5 = Finding(phrase=p4, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=100000, jobs_count=40000, jobs_above_100k_count=7000)
        f6 = Finding(phrase=p5, created_date=dt.datetime(2019,2,15,0,0,0), mean_salary=60000, jobs_count=5, jobs_above_100k_count=1)
        db.session.add_all([f1, f2, f3, f4, f5, f6])

        # associate phrases with users and phrase_groups
        up1 = UserPhrase(user=u1, phrase=p1, phrase_group=d1) # jack resume has project manager
        up2 = UserPhrase(user=u2, phrase=p4, phrase_group=d2) # mary linkedin profile has mechanical engineer
        up3 = UserPhrase(user=u2, phrase=p3, phrase_group=d3) # mary resume has engineer
        up4 = UserPhrase(user=u1, phrase=p3, phrase_group=d1) # jack resume has engineer
        db.session.add_all([up1, up2, up3, up4])


        db.session.commit()

    def tearDown(self):
        UserCase.tearDown(self)

    def login(self, username, password):
        return UserCase.login(self, username, password)

    def logout(self):
        return UserCase.logout(self)

    def create_comparison(self, title, body, username, password):
        self.login(username, password)

        return self.app.client.post('/documents', data=dict(
            title=title,
            body=body
        ), follow_redirects=True)

    def test_get_phrase_group(self):
        # search phrase
        title = 'jack resume'
        phrase_group_in_db = db.session.query(PhraseGroup).filter_by(title=title).first()
        self.assertEqual(phrase_group_in_db.title, title)

    def test_view_phrase_group_in_list(self):
        # not authenticated
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('jack resume', str(response.data))

    def test_create_phrase_group(self):
        title = 'mary resume'
        body = 'pilot'
        username = 'mary'
        password = 'marypassword'
        self.create_phrase_group(title, body, username, password)
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary resume', str(response.data))

    def test_generate_phrase_group_slug(self):

        # create a new phrase_group with the same title
        title = 'mary resume'
        body = 'minister'
        username = 'mary'
        password = 'marypassword'
        self.create_phrase_group(title, body, username, password)
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary resume', str(response.data))
        
        # check if 2 phrase_groups in db
        phrase_groups_in_db = db.session.query(PhraseGroup).filter_by(title=title).all()
        self.assertEqual(len(phrase_groups_in_db), 2)

        # check that slugs are different
        phrase_groups_in_db = db.session.query(PhraseGroup).filter_by(slug='mary-resume').all()
        self.assertEqual(len(phrase_groups_in_db), 1)

    def test_get_latest_finding_in_phrase_group_phrases(self):
        # search phrase
        phrase_group_in_db = PhraseGroup.query.filter_by(slug='mary-resume').first()
        self.assertEqual(phrase_group_in_db.phrases[0].phrase.mean_salary, 95000)

    def test_analyze_phrase_group_phrases(self):
        title = 'mary new resume'
        body = 'A confident digital product manager, data scientist, MBA and entrepreneur, I deliver outcomes - not outputs.'
        username = 'mary'
        password = 'marypassword'
        self.create_phrase_group(title, body, username, password)
        response = self.app.client.get('/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mba', str(response.data))
        self.assertIn('data scientist', str(response.data))

    def test_get_user_phrase_group(self):
        # search phrase
        user_in_db = db.session.query(User).filter_by(username='jack').first()
        phrase_group_in_db = db.session.query(PhraseGroup).filter_by(title='jack resume').first()
        self.assertEqual(phrase_group_in_db.user_id, user_in_db.id)

    def test_view_user_phrase_groups(self):
        # authenticated
        self.login('mary','marypassword')
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('jack resume', str(response.data))
        self.assertIn('mary linkedin', str(response.data))
        self.assertIn('mary resume', str(response.data))

    def test_create_user_phrase_group(self):
        username = 'mary'
        password = 'marypassword'
        self.login(username, password)
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary resume', str(response.data))

        title = 'mary cv'
        body = 'mary new body'
        self.create_phrase_group(title, body, username, password)
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary cv', str(response.data))

    def test_view_user_phrase_group(self):
        # authenticated
        self.login('mary','marypassword')
        response = self.app.client.get('/documents/mary-resume', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('jack resume', str(response.data))
        self.assertNotIn('mary linkedin', str(response.data))
        self.assertIn('mary resume', str(response.data))

    # a different user can't see the phrase_group with the slug
    # def test_view_user_phrase_group_authorized(self):
    #     self.login('john','johnpassword')
    #     response = self.app.client.get('/documents/mary-resume', content_type='html/text')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertNotIn('mary resume', str(response.data))

    #     response = self.app.client.get('/documents/mary-resume', content_type='html/text')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertNotIn('mary resume', str(response.data))

    # the phrase_group shows the top 5 phrases by most recent finding value

    # /api/documents/{slug}/phrases loaded in background
    def test_view_phrase_group_phrases_in_api(self):
        # check api
        response = self.app.client.get('/api/documents/mary-resume/phrases', content_type='html/text')
        # response = self.app.client.get('/api/documents/jack-resume/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('"jobsCount": null', str(response.data))

        # engineer
        self.assertIn('"phraseText": "engineer"', str(response.data))
        
        # not mechanical-engineer, that is in her linkedin profile
        self.assertNotIn('"phraseText": "mechanical engineer"', str(response.data))

        # not project manager, that is in jack's resume
        self.assertNotIn('"phraseText": "project manager"', str(response.data))
        
        # only most recent finding for engineer
        self.assertNotIn('"meanSalary": 85000', str(response.data))
        self.assertIn('"meanSalary": 95000', str(response.data))


if __name__ == '__main__':
    unittest.main(verbosity=2)

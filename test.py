#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest
from app import app, db
from config import TestConfig

import os
from config import basedir

app.config.from_object(TestConfig)

from app.models import User, Phrase


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
 
        self.login('john','johnpassword')
        response = self.app.client.get('/',follow_redirects=True)

        self.assertIn('Logout', str(response.data))
        self.assertIn('Hi, john', str(response.data))

        response = self.logout()
        self.assertIn('Goodbye', str(response.data)) 
        self.assertIn('Login', str(response.data))
        self.assertNotIn('Hi, john', str(response.data))

        response = self.login('john','notpassword')
        self.assertIn('Invalid username or password', str(response.data))

        self.logout()
        response = self.login('susan','johnpassword')
        self.assertIn('Invalid username or password', str(response.data))


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
                                         '?d=identicon&s=128'))

    # def test_follow(self):
    #     u1 = User(username='john', email='john@example.com')
    #     u2 = User(username='susan', email='susan@example.com')
    #     db.session.add(u1)
    #     db.session.add(u2)
    #     db.session.commit()
    #     self.assertEqual(u1.followed.all(), [])
    #     self.assertEqual(u1.followers.all(), [])

    #     u1.follow(u2)
    #     db.session.commit()
    #     self.assertTrue(u1.is_following(u2))
    #     self.assertEqual(u1.followed.count(), 1)
    #     self.assertEqual(u1.followed.first().username, 'susan')
    #     self.assertEqual(u2.followers.count(), 1)
    #     self.assertEqual(u2.followers.first().username, 'john')

    #     u1.unfollow(u2)
    #     db.session.commit()
    #     self.assertFalse(u1.is_following(u2))
    #     self.assertEqual(u1.followed.count(), 0)
    #     self.assertEqual(u2.followers.count(), 0)

    # def test_follow_posts(self):
    #     # create four users
    #     u1 = User(username='john', email='john@example.com')
    #     u2 = User(username='susan', email='susan@example.com')
    #     u3 = User(username='mary', email='mary@example.com')
    #     u4 = User(username='david', email='david@example.com')
    #     db.session.add_all([u1, u2, u3, u4])

    #     # create four posts
    #     now = datetime.utcnow()
    #     p1 = Post(body="post from john", author=u1,
    #               timestamp=now + timedelta(seconds=1))
    #     p2 = Post(body="post from susan", author=u2,
    #               timestamp=now + timedelta(seconds=4))
    #     p3 = Post(body="post from mary", author=u3,
    #               timestamp=now + timedelta(seconds=3))
    #     p4 = Post(body="post from david", author=u4,
    #               timestamp=now + timedelta(seconds=2))
    #     db.session.add_all([p1, p2, p3, p4])
    #     db.session.commit()

    #     # setup the followers
    #     u1.follow(u2)  # john follows susan
    #     u1.follow(u4)  # john follows david
    #     u2.follow(u3)  # susan follows mary
    #     u3.follow(u4)  # mary follows david
    #     db.session.commit()

    #     # check the followed posts of each user
    #     f1 = u1.followed_posts().all()
    #     f2 = u2.followed_posts().all()
    #     f3 = u3.followed_posts().all()
    #     f4 = u4.followed_posts().all()
    #     self.assertEqual(f1, [p2, p4, p1])
    #     self.assertEqual(f2, [p2, p3])
    #     self.assertEqual(f3, [p3, p4])
    #     self.assertEqual(f4, [p4])

class PhraseCase(unittest.TestCase):
    def setUp(self):
        UserCase.setUp(self)

        # search phrase
        p1 = Phrase(phrase='project manager')
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
        phrase = 'project manager'
        phrase_in_db = db.session.query(Phrase).filter_by(phrase=phrase).first()
        self.assertEqual(phrase_in_db.phrase, phrase)

    def test_view_phrase(self):
        # not authenticated
        response = self.app.client.get('/search_phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('project manager', str(response.data))

    def test_create_phrase(self):
        # phrase not found, should create
        term = 'linux'

        response = self.app.client.get('/search_phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertIn(term, str(response.data))

        term = 'Accountant' # lowercase

        response = self.app.client.get('/search_phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertNotIn(term, str(response.data))
        self.assertIn(term.lower(), str(response.data))

        term = 'project management' # keep spaces

        response = self.app.client.get('/search_phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertIn(term, str(response.data))

        term = ' mechanical engineer ' # trim

        response = self.app.client.get('/search_phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('New search phrase!', str(response.data))
        self.assertNotIn(' mechanical engineer ', str(response.data))


    def test_update_phrase(self):
        # if already exists, don't create a new one, instead update counter and date
        term = 'linux'

        response = self.app.client.get('/search_phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn(term, str(response.data))

        response = self.app.client.get('/search_phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Searched 2 times!', str(response.data))
        self.assertIn(term, str(response.data))

        term_with_junk = ' LINUX$$ ' # trim

        response = self.app.client.get('/search_phrases?term=' + term, content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Searched 3 times!', str(response.data))
        self.assertIn(term, str(response.data))
        self.assertNotIn(term_with_junk, str(response.data))


    def test_protected_page(self):
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


if __name__ == '__main__':
    unittest.main(verbosity=2)

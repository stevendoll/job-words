#!/usr/bin/env python
import datetime as dt
from datetime import timedelta
import unittest
from app import app, db
from config import TestConfig

import os
from config import basedir

app.config.from_object(TestConfig)

from app.models import User, Phrase, UserPhrase, Finding, Document, UserDocument


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
                                         '?d=blank&s=128'))

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
        f3 = Finding(phrase=p3, created_date=dt.datetime(2018,8,15,0,0,0), mean_salary=95000, jobs_count=60000, jobs_above_100k_count=7000)
        f4 = Finding(phrase=p4, created_date=dt.datetime(2018,8,15,0,0,0), mean_salary=95000, jobs_count=5, jobs_above_100k_count=1)
        db.session.add_all([f1, f2, f3, f4])
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
        self.assertIn('Mean Salary', str(response.data))
        self.assertIn('Jobs above $100k', str(response.data))

 
class DocumentCase(unittest.TestCase):
    def setUp(self):
        UserCase.setUp(self)

        # search phrase
        d1 = Document(title='my resume', slug='my-resume')
        db.session.add(d1)
        db.session.commit()

    def tearDown(self):
        UserCase.tearDown(self)

    def login(self, username, password):
        return UserCase.login(self, username, password)

    def logout(self):
        return UserCase.logout(self)

    def create_document(self, title, body):
        return self.app.client.post('/documents', data=dict(
            title=title,
            body=body
        ), follow_redirects=True)

    def test_get_document(self):
        # search phrase
        title = 'my resume'
        document_in_db = db.session.query(Document).filter_by(title=title).first()
        self.assertEqual(document_in_db.title, title)

    def test_view_document_in_list(self):
        # not authenticated
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('my resume', str(response.data))

    def test_create_document(self):
        title = 'john resume'
        body = 'minister'
        self.create_document(title, body)
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('john resume', str(response.data))

    def test_generate_document_slug(self):

        # create a new document with the same title
        title = 'my resume'
        body = 'minister'
        self.create_document(title, body)
        response = self.app.client.get('/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('my resume', str(response.data))
        
        # check if 2 documents in db
        documents_in_db = db.session.query(Document).filter_by(title=title).all()
        self.assertEqual(len(documents_in_db), 2)

        # check that slugs are different
        documents_in_db = db.session.query(Document).filter_by(slug='my-resume').all()
        self.assertEqual(len(documents_in_db), 1)


    def test_analyze_document_phrases(self):
        title = 'steven resume'
        body = 'A confident digital product manager, data scientist, MBA and entrepreneur, I deliver outcomes - not outputs.'
        self.create_document(title, body)
        response = self.app.client.get('/phrases', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mba', str(response.data))
        self.assertIn('data scientist', str(response.data))



class UserDocumentCase(unittest.TestCase):
    def setUp(self):
        UserCase.setUp(self)

        # create users
        u1 = User(username='jack', email='jack@example.com')
        u2 = User(username='mary', email='mary@example.com')
        u2.set_password('marypassword')
        db.session.add_all([u1, u2])

        # create phrases
        d1 = Document(title='jack resume', slug='jack-resume')
        d2 = Document(title='mary linkedin', slug='mary-linkedin')
        d3 = Document(title='mary resume', slug='mary-resume')
        db.session.add_all([d1, d2, d3])

        # create user phrases
        ud1 = UserDocument(user=u1, document=d1)
        ud2 = UserDocument(user=u2, document=d2)
        ud3 = UserDocument(user=u2, document=d3)
        db.session.add_all([ud1, ud2, ud3])
        db.session.commit()


    def tearDown(self):
        UserCase.tearDown(self)

    def login(self, username, password):
        return UserCase.login(self, username, password)

    def logout(self):
        return UserCase.logout(self)

    def create_document(self, title, body):
        return DocumentCase.create_document(self, title, body)

    def test_get_user_document(self):
        # search phrase
        user_in_db = db.session.query(User).filter_by(username='jack').first()
        document_in_db = db.session.query(Document).filter_by(title='jack resume').first()
        user_document_in_db = db.session.query(UserDocument).filter_by(document_id=document_in_db.id, user_id=user_in_db.id).first()
        self.assertEqual(user_document_in_db.user_id, user_in_db.id)

    def test_view_user_document(self):
        # authenticated
        self.login('mary','marypassword')
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('jack resume', str(response.data))
        self.assertIn('mary linkedin', str(response.data))
        self.assertIn('mary resume', str(response.data))

    def test_create_user_document(self):
        self.login('mary','marypassword')
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary resume', str(response.data))

        title = 'mary cv'
        body = 'mary new body'
        self.create_document(title, body)
        response = self.app.client.get('/users/mary/documents', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mary cv', str(response.data))


if __name__ == '__main__':
    unittest.main(verbosity=2)

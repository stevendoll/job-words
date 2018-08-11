import lxml.html
import requests
from sqlalchemy.sql import func
from flask import flash
import datetime as dt
from datetime import timedelta
import re
import pandas as pd
import numpy as np


from app import db, login

INDEED_SEARCH_URL = 'http://www.indeed.com/jobs?q="'
INDEED_SEARCH_SUFFIX = '"&l=Washington%2C+DC'
INDEED_HEADERS = {'User-agent':'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'}

STALE_FINDINGS_DAYS = 30

class Finding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase_id = db.Column(db.Integer, db.ForeignKey('phrase.id'))
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    phrase = db.relationship('Phrase')
    indeed_content = db.Column(db.Text())

    def __repr__(self):
        return '<Finding {}>'.format(self.phrase.phrase)

    @staticmethod
    def get_all():
        return Finding.query.all()

    @staticmethod
    def analyze(phrase):

        # check if there is a recent finding for this phrase
        this_finding = db.session.query(Finding).filter_by(phrase=phrase).filter(Finding.created_date>(dt.datetime.utcnow() - timedelta(days=STALE_FINDINGS_DAYS))).first()       

        # if a recent one is not in the database, look it up
        if not this_finding:

            indeed_content = Finding.retrieve_indeed_search_result(phrase.phrase)

            this_finding = Finding(
                phrase=phrase,
                indeed_content=indeed_content)

            db.session.add(this_finding)
            db.session.commit()

        job_summary = Finding.calculate_jobs_at_salary_levels(this_finding.indeed_content)

        print(job_summary)

        return this_finding

    @staticmethod
    def retrieve_indeed_search_result(search_phrase):
        
        url = ''.join([INDEED_SEARCH_URL, str(search_phrase.replace(' ','+')), INDEED_SEARCH_SUFFIX])

        indeed_content = None

        try:

            r = requests.get(url, headers=INDEED_HEADERS)

            indeed_content = r.content

        except:
            print('Error in indeed search for term %s' % url)
            flash('Indeed search failed')

        return indeed_content


    @staticmethod
    def calculate_jobs_at_salary_levels(indeed_content):

        get_salary = re.compile(r'\$(\d+)')
        get_job = re.compile(r'\((\d+)\)')
 
        df = pd.DataFrame(columns=['min_salary', 'jobs'])

        doc = lxml.html.fromstring(indeed_content)

        if len(doc.cssselect('#SALARY_rbo ul li')) > 1:

            for i in range(0,len(doc.cssselect('#SALARY_rbo ul li'))):

                row = doc.cssselect('#SALARY_rbo ul li')[i].text_content().strip().replace(',','')
                df = df.append({'min_salary': int(get_salary.findall(row)[0]), 'jobs': int(get_job.findall(row)[0])}, ignore_index=True)

        # get salary as center of range, not floor
        df['salary'] = (df.min_salary + df.min_salary.shift(-1))/2
        df.loc[df.salary.isnull(), 'salary'] = df.min_salary * 1.15

        market = []

        for index, row in df.iterrows():
            market += [row['salary']] * row['jobs']

        market = pd.Series(market)

        print('market mean', market.mean())

        return df
 
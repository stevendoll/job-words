import lxml.html
import requests
from time import sleep
from random import randint

from sqlalchemy.sql import func
from flask import flash
import datetime as dt
from datetime import timedelta
import re
import pandas as pd
import numpy as np
import scipy.stats as stats

from app import app, db

INDEED_SEARCH_URL = "https://www.indeed.com/jobs?q="
INDEED_SEARCH_SUFFIX = "&l=Washington%2C+DC"
INDEED_HEADERS = {
    "User-agent": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1"
}

STALE_FINDINGS_DAYS = 30


class Finding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase_id = db.Column(db.Integer, db.ForeignKey("phrase.id"), nullable=False)
    created_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    phrase = db.relationship("Phrase")
    indeed_content = db.Column(db.Text())
    mean_salary = db.Column(db.Float)
    sigma_salary = db.Column(db.Float)
    jobs_count = db.Column(db.Float)
    # normality_p_value = db.Column(db.Float)
    jobs_above_50k_count = db.Column(db.Float)
    jobs_above_55k_count = db.Column(db.Float)
    jobs_above_60k_count = db.Column(db.Float)
    jobs_above_65k_count = db.Column(db.Float)
    jobs_above_70k_count = db.Column(db.Float)
    jobs_above_75k_count = db.Column(db.Float)
    jobs_above_80k_count = db.Column(db.Float)
    jobs_above_85k_count = db.Column(db.Float)
    jobs_above_90k_count = db.Column(db.Float)
    jobs_above_95k_count = db.Column(db.Float)
    jobs_above_100k_count = db.Column(db.Float)
    jobs_above_105k_count = db.Column(db.Float)
    jobs_above_110k_count = db.Column(db.Float)
    jobs_above_115k_count = db.Column(db.Float)
    jobs_above_120k_count = db.Column(db.Float)
    jobs_above_125k_count = db.Column(db.Float)
    jobs_above_130k_count = db.Column(db.Float)
    jobs_above_135k_count = db.Column(db.Float)
    jobs_above_140k_count = db.Column(db.Float)
    jobs_above_145k_count = db.Column(db.Float)
    jobs_above_150k_count = db.Column(db.Float)

    __mapper_args__ = {"order_by": created_date}

    def __repr__(self):
        return "<Finding {}>".format(self.phrase.phrase)

    @staticmethod
    def get_all():
        return Finding.query.all()

    @staticmethod
    def analyze(phrase):

        # check if there is a recent finding for this phrase
        this_finding = (
            Finding.query.filter_by(phrase=phrase)
            .filter(
                Finding.created_date
                > (dt.datetime.utcnow() - timedelta(days=STALE_FINDINGS_DAYS))
            )
            .first()
        )

        # if a recent one is not in the database, look it up
        if not this_finding:

            # wait and vary times
            sleep(randint(0, 3))

            indeed_content = Finding.retrieve_indeed_search_result(phrase.phrase_text)

            this_finding = Finding(phrase=phrase, indeed_content=indeed_content)

            if indeed_content:

                # perform analysis of indeed jobs histogram
                job_market = Finding.calculate_jobs_at_salary_levels(
                    this_finding.indeed_content
                )

                if job_market:

                    this_finding.mean_salary = job_market["mean_salary"]
                    this_finding.sigma_salary = job_market["sigma_salary"]
                    this_finding.jobs_count = job_market["jobs_count"]
                    this_finding.jobs_above_50k_count = job_market[
                        "jobs_above_50k_count"
                    ]
                    this_finding.jobs_above_55k_count = job_market[
                        "jobs_above_55k_count"
                    ]
                    this_finding.jobs_above_60k_count = job_market[
                        "jobs_above_60k_count"
                    ]
                    this_finding.jobs_above_65k_count = job_market[
                        "jobs_above_65k_count"
                    ]
                    this_finding.jobs_above_70k_count = job_market[
                        "jobs_above_70k_count"
                    ]
                    this_finding.jobs_above_75k_count = job_market[
                        "jobs_above_75k_count"
                    ]
                    this_finding.jobs_above_80k_count = job_market[
                        "jobs_above_80k_count"
                    ]
                    this_finding.jobs_above_85k_count = job_market[
                        "jobs_above_85k_count"
                    ]
                    this_finding.jobs_above_90k_count = job_market[
                        "jobs_above_90k_count"
                    ]
                    this_finding.jobs_above_95k_count = job_market[
                        "jobs_above_95k_count"
                    ]
                    this_finding.jobs_above_100k_count = job_market[
                        "jobs_above_100k_count"
                    ]
                    this_finding.jobs_above_105k_count = job_market[
                        "jobs_above_105k_count"
                    ]
                    this_finding.jobs_above_110k_count = job_market[
                        "jobs_above_110k_count"
                    ]
                    this_finding.jobs_above_115k_count = job_market[
                        "jobs_above_115k_count"
                    ]
                    this_finding.jobs_above_120k_count = job_market[
                        "jobs_above_120k_count"
                    ]
                    this_finding.jobs_above_125k_count = job_market[
                        "jobs_above_125k_count"
                    ]
                    this_finding.jobs_above_130k_count = job_market[
                        "jobs_above_130k_count"
                    ]
                    this_finding.jobs_above_135k_count = job_market[
                        "jobs_above_135k_count"
                    ]
                    this_finding.jobs_above_140k_count = job_market[
                        "jobs_above_140k_count"
                    ]
                    this_finding.jobs_above_145k_count = job_market[
                        "jobs_above_145k_count"
                    ]
                    this_finding.jobs_above_150k_count = job_market[
                        "jobs_above_150k_count"
                    ]

            db.session.add(this_finding)

            db.session.commit()

        else:

            app.logger.info(
                "The phrase %s was searched on: %s"
                % (phrase.phrase_text, this_finding.created_date)
            )

        return this_finding

    @staticmethod
    def retrieve_indeed_search_result(search_phrase):

        url = "".join([INDEED_SEARCH_URL, str(search_phrase.replace(" ", "+"))])

        indeed_content = None

        try:

            r = requests.get(url, headers=INDEED_HEADERS)

            indeed_content = r.content

        except:
            print("Error in indeed search for term %s" % url)
            flash("Indeed search failed")

        return indeed_content

    @staticmethod
    def calculate_jobs_at_salary_levels(indeed_content):

        get_salary = re.compile(r"\$(\d+)")
        get_job = re.compile(r"\((\d+)\)")

        df = pd.DataFrame(columns=["min_salary", "jobs"])

        doc = lxml.html.fromstring(indeed_content)

        result = None

        if len(doc.cssselect("#SALARY_rbo ul li")) > 1:

            for i in range(0, len(doc.cssselect("#SALARY_rbo ul li"))):

                row = (
                    doc.cssselect("#SALARY_rbo ul li")[i]
                    .text_content()
                    .strip()
                    .replace(",", "")
                )
                df = df.append(
                    {
                        "min_salary": int(get_salary.findall(row)[0]),
                        "jobs": int(get_job.findall(row)[0]),
                    },
                    ignore_index=True,
                )

            # get salary as center of range, not floor
            df["salary"] = (df.min_salary + df.min_salary.shift(-1)) / 2
            df.loc[df.salary.isnull(), "salary"] = df.min_salary * 1.15

            market = []

            # generate the job market with a row for each job at each salary
            for index, row in df.iterrows():
                market += [row["salary"]] * row["jobs"]

            market = pd.Series(market)

            result = {}
            result["mean_salary"] = market.mean()
            result["sigma_salary"] = market.std()
            result["jobs_count"] = market.count()
            # result['chi_squared'], result['normality_p_value'] = stats.normaltest(market)

            for i in range(50, 155, 5):
                result["jobs_above_" + str(i) + "k_count"] = (
                    1 - stats.norm.cdf(i * 1000, loc=market.mean(), scale=market.std())
                ) * market.count()

            # print(result)

            # alpha = 1e-3
            # print("p = {:g}".format(result['normality_p_value']))
            # if result['normality_p_value'] < alpha:  # null hypothesis: x comes from a normal distribution
            #     print("The null hypothesis can be rejected")
            # else:
            #     print("The null hypothesis cannot be rejected")

        else:
            app.logger.warning("No salary lines found in indeed text")

        return result

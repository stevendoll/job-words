from marshmallow import fields, post_load, pre_load, post_dump, pre_dump
from marshmallow_sqlalchemy import ModelSchema

class PhraseSchema(ModelSchema):
    phraseText = fields.String(attribute="phrase_text")
    searchCount = fields.Integer(attribute="search_count")
    createdDate = fields.DateTime(attribute="created_date")
    updatedDate = fields.DateTime(attribute="updated_date")
    meanSalary = fields.Float(attribute="mean_salary")
    jobsCount = fields.Float(attribute="jobs_count")
    marketSize = fields.Float(attribute="market_size")
    jobsOver100kCount = fields.Float(attribute="jobs_above_100k_count")

    class Meta:
        dateformat = "%Y-%m-%dT%H:%M:%S.000Z"


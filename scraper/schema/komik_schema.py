from marshmallow import Schema, fields, EXCLUDE

class KomikDetailSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(required=True)
    title = fields.String(required=True)
    image = fields.String(required=True)
    description = fields.String(required=True)
    synopsis = fields.String(required=True)
    type = fields.String(required=True)
    status = fields.String(required=True)
    year = fields.Integer(required=True)
    genre = fields.List(fields.String, required=True)
    chapter = fields.Integer(required=True)
    chapter_list = fields.List(fields.String, required=True)
    author = fields.String(required=True)
    rating = fields.String(required=True)
    views = fields.Integer(required=True)
    
class KomikSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(required=True)
    title = fields.String(required=True)
    image = fields.String(required=True)
    total_chapter = fields.Integer(required=True)
    rating = fields.Float(required=True)
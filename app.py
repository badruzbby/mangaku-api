from flask import Flask
from flask_cors import CORS
from flask_restx import Api, Resource, fields, reqparse
from scraper.mangaku import Mangaku

app = Flask(__name__)
CORS(app)

api = Api(
    app,
    version='1.0',
    title='Mangaku API',
    description='A REST API for scraping manga data from Mangaaku.com',
    doc='/docs/',
    contact_email='badzzhaxor@gmail.com',
    license='MIT'
)

manga_ns = api.namespace('manga', description='Manga operations')
read_ns = api.namespace('read', description='Chapter reading operations')

manga_model = api.model('Manga', {
    'id': fields.String(required=True, description='Unique manga identifier'),
    'title': fields.String(required=True, description='Manga title'),
    'image': fields.String(required=True, description='Manga cover image URL'),
    'total_chapter': fields.Integer(required=True, description='Total number of chapters'),
    'rating': fields.Float(required=True, description='Manga rating')
})

manga_detail_model = api.model('MangaDetail', {
    'id': fields.String(required=True, description='Unique manga identifier'),
    'title': fields.String(required=True, description='Manga title'),
    'image': fields.String(required=True, description='Manga cover image URL'),
    'description': fields.String(required=True, description='Short description'),
    'synopsis': fields.String(required=True, description='Full synopsis'),
    'type': fields.String(required=True, description='Manga type (e.g., Manga, Manhwa)'),
    'status': fields.String(required=True, description='Publication status'),
    'year': fields.Integer(required=True, description='Publication year'),
    'genre': fields.List(fields.String, required=True, description='List of genres'),
    'chapter': fields.Integer(required=True, description='Total chapters'),
    'chapter_list': fields.List(fields.String, required=True, description='List of chapter URLs'),
    'author': fields.String(required=True, description='Manga author'),
    'rating': fields.String(required=True, description='Manga rating'),
    'views': fields.Integer(required=True, description='Total views')
})

chapter_images_model = api.model('ChapterImages', {
    'title': fields.String(required=True, description='Chapter title'),
    'chapter': fields.Raw(required=True, description='Chapter images organized by servers')
})

error_model = api.model('Error', {
    'error': fields.String(required=True, description='Error message')
})

manga_list_parser = reqparse.RequestParser()
manga_list_parser.add_argument('page', type=int, default=1, help='Page number for pagination')

@manga_ns.route('')
class MangaList(Resource):
    @api.doc('get_manga_list')
    @api.expect(manga_list_parser)
    @api.marshal_list_with(manga_model)
    @api.response(200, 'Success')
    @api.response(500, 'Internal Server Error')
    def get(self):
        """Get list of manga with pagination"""
        args = manga_list_parser.parse_args()
        page = args['page']
        
        try:
            mangaku = Mangaku()
            manga_list = mangaku.get_manga_list(page)
            
            if manga_list is None:
                api.abort(500, "Failed to fetch manga list")
            
            return manga_list
        except Exception as e:
            api.abort(500, f"Internal server error: {str(e)}")

@manga_ns.route('/<string:manga_url>')
class MangaDetail(Resource):
    @api.doc('get_manga_detail')
    @api.marshal_with(manga_detail_model)
    @api.response(200, 'Success')
    @api.response(404, 'Manga not found', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def get(self, manga_url):
        """Get detailed information about a specific manga"""
        try:
            mangaku = Mangaku()
            manga_detail = mangaku.get_manga_detail(manga_url)
            
            if manga_detail is None:
                api.abort(404, "Manga not found")
            
            return manga_detail
        except Exception as e:
            api.abort(500, f"Internal server error: {str(e)}")

@read_ns.route('/<path:manga_url>')
class ChapterImages(Resource):
    @api.doc('get_chapter_images')
    @api.marshal_with(chapter_images_model)
    @api.response(200, 'Success')
    @api.response(404, 'Chapter not found', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def get(self, manga_url):
        """Get chapter images from multiple servers"""
        try:
            mangaku = Mangaku()
            chapter_data = mangaku.read_manga(manga_url)
            
            if chapter_data is None:
                api.abort(404, "Chapter not found")
            
            return chapter_data
        except Exception as e:
            api.abort(500, f"Internal server error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
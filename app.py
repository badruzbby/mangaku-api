import os
import time
import logging
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_restx import Api, Resource, fields, reqparse
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from scraper.mangaku import Mangaku
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
        
        # Initialize extensions
    CORS(app)

        # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[app.config['RATELIMIT_DEFAULT']],
        storage_uri=app.config['RATELIMIT_STORAGE_URL'],
        headers_enabled=app.config['RATELIMIT_HEADERS_ENABLED']
    )
    
    # Initialize cache
    cache = Cache(app)
    
    # Initialize Flask-RESTX
    api = Api(
        app,
        version='1.0',
        title='Mangaku API',
        description='A high-performance REST API for scraping manga data from Mangaaku.com with rate limiting and caching',
        doc='/docs/',
        contact_email='badzzhaxor@gmail.com',
        license='MIT'
    )
    
    # Create namespaces
    manga_ns = api.namespace('manga', description='Manga operations')
    search_ns = api.namespace('search', description='Search operations')
    read_ns = api.namespace('read', description='Chapter reading operations')
    health_ns = api.namespace('health', description='Health check and monitoring')
    
    # Define response models
    manga_search_model = api.model('MangaSearch', {
        'id': fields.String(required=True, description='Unique manga identifier'),
        'title': fields.String(required=True, description='Manga title'),
        'image': fields.String(required=True, description='Manga cover image URL'),
        'total_chapter': fields.Integer(required=True, description='Total number of chapters'),
        'rating': fields.Float(required=True, description='Manga rating')
    })
    
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
        'error': fields.String(required=True, description='Error message'),
        'code': fields.Integer(description='Error code'),
        'timestamp': fields.DateTime(description='Error timestamp')
    })
    
    health_model = api.model('Health', {
        'status': fields.String(required=True, description='API status'),
        'timestamp': fields.DateTime(required=True, description='Check timestamp'),
        'version': fields.String(required=True, description='API version'),
        'cache_status': fields.String(description='Cache system status'),
        'rate_limit_status': fields.String(description='Rate limiting status')
    })
    
    # Parser for query parameters
    manga_list_parser = reqparse.RequestParser()
    manga_list_parser.add_argument('page', type=int, default=1, help='Page number for pagination')
    manga_list_parser.add_argument('limit', type=int, default=app.config['DEFAULT_PAGE_SIZE'], 
                                 help=f'Items per page (max {app.config["MAX_PAGE_SIZE"]})')
    
    search_parser = reqparse.RequestParser()
    search_parser.add_argument('query', type=str, required=True, help='Search query')
    search_parser.add_argument('page', type=int, default=1, help='Page number for pagination')
    search_parser.add_argument('limit', type=int, default=app.config['DEFAULT_PAGE_SIZE'], 
                              help=f'Items per page (max {app.config["MAX_PAGE_SIZE"]})')
    
    # Performance monitoring decorator
    def monitor_performance(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            g.start_time = start_time
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{request.endpoint} - {request.method} - Duration: {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{request.endpoint} - {request.method} - Error: {str(e)} - Duration: {duration:.3f}s")
                raise
        return decorated_function
    
    # Cache key generators
    def make_cache_key(*args, **kwargs):
        """Generate cache key for requests."""
        path = request.path
        args_str = str(sorted(request.args.items()))
        return f"request:{path}:{hash(args_str)}"
    
    # Create optimized mangaku instance with config settings
    def get_mangaku_instance():
        """Create Mangaku instance with configuration settings."""
        return Mangaku(
            max_retries=app.config.get('MAX_RETRIES', 3),
            timeout=app.config.get('REQUEST_TIMEOUT', 120),
            pool_connections=app.config.get('CONNECTION_POOL_SIZE', 20),
            pool_maxsize=app.config.get('CONNECTION_POOL_MAXSIZE', 50)
        )
    
    # Routes
    @manga_ns.route('')
    class MangaList(Resource):
        @api.doc('get_manga_list')
        @api.expect(manga_list_parser)
        @api.marshal_list_with(manga_model)
        @api.response(200, 'Success')
        @api.response(429, 'Rate limit exceeded')
        @api.response(500, 'Internal Server Error')
        @limiter.limit("50 per minute")
        @cache.cached(timeout=300, key_prefix=make_cache_key)
        @monitor_performance
        def get(self):
            """Get list of manga with pagination and caching"""
            args = manga_list_parser.parse_args()
            page = args['page']
            limit = min(args['limit'], app.config['MAX_PAGE_SIZE'])  # Enforce max limit
            
            try:
                mangaku = get_mangaku_instance()
                manga_list = mangaku.get_manga_list(page, limit)
                
                if manga_list is None:
                    api.abort(500, "Failed to fetch manga list")
                
                return manga_list
            except Exception as e:
                logger.error(f"Error in get_manga_list: {str(e)}")
                api.abort(500, f"Internal server error: {str(e)}")
    
    @manga_ns.route('/<string:manga_url>')
    class MangaDetail(Resource):
        @api.doc('get_manga_detail')
        @api.marshal_with(manga_detail_model)
        @api.response(200, 'Success')
        @api.response(404, 'Manga not found', error_model)
        @api.response(429, 'Rate limit exceeded')
        @api.response(500, 'Internal Server Error', error_model)
        @limiter.limit("30 per minute")
        @cache.cached(timeout=600, key_prefix=make_cache_key)  # Longer cache for details
        @monitor_performance
        def get(self, manga_url):
            """Get detailed information about a specific manga with caching"""
            try:
                mangaku = get_mangaku_instance()
                manga_detail = mangaku.get_manga_detail(manga_url)
                if manga_detail is None:
                    api.abort(404, "Manga not found")  
                return manga_detail
            except Exception as e:
                logger.error(f"Error in get_manga_detail for {manga_url}: {str(e)}")
                api.abort(500, f"Internal server error: {str(e)}")
    
    @read_ns.route('/<path:manga_url>')
    class ChapterImages(Resource):
        @api.doc('get_chapter_images')
        @api.marshal_with(chapter_images_model)
        @api.response(200, 'Success')
        @api.response(404, 'Chapter not found', error_model)
        @api.response(429, 'Rate limit exceeded')
        @api.response(500, 'Internal Server Error', error_model)
        @limiter.limit("20 per minute")  # More restrictive for image-heavy endpoints
        @cache.cached(timeout=1800, key_prefix=make_cache_key)  # Longer cache for images
        @monitor_performance
        def get(self, manga_url):
            """Get chapter images from multiple servers with caching"""
            try:
                mangaku = get_mangaku_instance()
                chapter_data = mangaku.read_manga(manga_url)
                
                if chapter_data is None:
                    api.abort(404, "Chapter not found")
                
                return chapter_data
            except Exception as e:
                logger.error(f"Error in get_chapter_images for {manga_url}: {str(e)}")
                api.abort(500, f"Internal server error: {str(e)}")
    
    @health_ns.route('')
    class HealthCheck(Resource):
        @api.doc('health_check')
        @api.marshal_with(health_model)
        @api.response(200, 'API is healthy')
        @api.response(503, 'API is unhealthy')
        @limiter.exempt  # Exempt health checks from rate limiting
        def get(self):
            """Health check endpoint for monitoring"""
            from datetime import datetime
            
            try:
                # Check cache status
                cache_status = "healthy"
                try:
                    cache.set("health_check", "ok", timeout=10)
                    cache.get("health_check")
                except:
                    cache_status = "unhealthy"

                # Check rate limiter status
                rate_limit_status = "healthy"
                try:
                    limiter.check()
                except:
                    rate_limit_status = "unhealthy"
                
                health_data = {
                    'status': 'healthy' if cache_status == 'healthy' and rate_limit_status == 'healthy' else 'degraded',
                    'timestamp': datetime.utcnow(),
                    'version': '1.0',
                    'cache_status': cache_status,
                    'rate_limit_status': rate_limit_status
                }
                
                return health_data
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                api.abort(503, f"Health check failed: {str(e)}")
    
    @search_ns.route('')
    class SearchManga(Resource):
        @api.doc('search_manga')
        @api.expect(search_parser)
        @api.marshal_list_with(manga_model)
        @api.response(200, 'Success')
        @api.response(429, 'Rate limit exceeded')
        @api.response(500, 'Internal Server Error')
        @limiter.limit("30 per minute")
        @cache.cached(timeout=300, key_prefix=make_cache_key)
        @monitor_performance
        def get(self):
            """Search manga with pagination and caching"""
            args = search_parser.parse_args()
            query = args['query']
            page = args['page']
            limit = min(args['limit'], app.config['MAX_PAGE_SIZE'])
            
            try:
                mangaku = get_mangaku_instance()
                manga_list = mangaku.search_manga(query, page, limit)
                
                if manga_list is None:
                    api.abort(500, "Failed to fetch manga list")
                
                return manga_list
            except Exception as e:
                logger.error(f"Error in search_manga: {str(e)}")
                api.abort(500, f"Internal server error: {str(e)}")
    
    @health_ns.route('/cache/clear')
    class CacheClear(Resource):
        @api.doc('clear_cache')
        @api.response(200, 'Cache cleared successfully')
        @api.response(500, 'Failed to clear cache')
        @limiter.limit("5 per hour")  # Very restrictive for cache clearing
        def post(self):
            """Clear all cached data (admin endpoint)"""
            try:
                cache.clear()
                logger.info("Cache cleared successfully")
                return {'message': 'Cache cleared successfully', 'timestamp': time.time()}
            except Exception as e:
                logger.error(f"Failed to clear cache: {str(e)}")
                api.abort(500, f"Failed to clear cache: {str(e)}")
    
    # Error handlers
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': str(e.description),
            'code': 429,
            'timestamp': time.time()
        }), 429
    
    @app.errorhandler(500)
    def internal_error_handler(e):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'code': 500,
            'timestamp': time.time()
        }), 500
    
    @app.errorhandler(504)
    def timeout_handler(e):
        return jsonify({
            'error': 'Request timeout',
            'message': 'The request took too long to process',
            'code': 504,
            'timestamp': time.time()
        }), 504
    
    # Performance headers middleware
    @app.after_request
    def after_request(response):
        # Add performance headers
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        # Add cache headers
        if request.endpoint and 'get' in request.endpoint.lower():
            response.headers['Cache-Control'] = 'public, max-age=300'
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 
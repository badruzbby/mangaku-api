from .schema.komik_schema import KomikDetailSchema, KomikSchema
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import urllib3
from .utils.request_attr import headers
from .utils.parsing_comic import parse_comic
import re
import time
import logging
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class OptimizedMangaku:
    """Optimized Mangaku scraper with performance enhancements."""
    
    def __init__(self, max_retries=3, timeout=120, pool_connections=20, pool_maxsize=50):
        self.base_url = 'https://mangaaku.com'
        self.headers = headers
        self.komik_schema = KomikSchema()
        self.komik_detail_schema = KomikDetailSchema()
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.session = self._create_session(pool_connections, pool_maxsize)
        
        self._lock = threading.Lock()
        
        self.request_count = 0
        self.cache_hits = 0
    
    def _create_session(self, pool_connections, pool_maxsize):
        """Create optimized requests session with connection pooling and retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 523, 524],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=2,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.headers)
        
        return session
    
    def _make_request(self, url, **kwargs):
        """Make optimized HTTP request with error handling and metrics."""
        with self._lock:
            self.request_count += 1
        
        start_time = time.time()
        
        timeout_settings = (30, self.timeout)
        
        try:
            response = self.session.get(
                url,
                timeout=timeout_settings,
                verify=False,
                stream=False,
                allow_redirects=True,
                **kwargs
            )
            
            if response.status_code == 200:
                duration = time.time() - start_time
                logger.debug(f"Request to {url} completed in {duration:.3f}s")
                return response
            else:
                logger.warning(f"Request to {url} returned status {response.status_code}")
                return response
        
        except requests.exceptions.ReadTimeout as e:
            duration = time.time() - start_time
            logger.warning(f"Read timeout for {url} after {duration:.3f}s, retrying with longer timeout")
            
            try:
                response = self.session.get(
                    url,
                    timeout=(60, 180),
                verify=False,
                    stream=False,
                    allow_redirects=True,
                    **kwargs
                )
                duration = time.time() - start_time
                logger.info(f"Retry successful for {url} after {duration:.3f}s")
                return response
            except Exception as retry_e:
                logger.error(f"Final retry failed for {url}: {str(retry_e)}")
                raise
        
        except requests.exceptions.ConnectTimeout as e:
            duration = time.time() - start_time
            logger.error(f"Connection timeout for {url} after {duration:.3f}s: {str(e)}")
            raise
            
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            logger.error(f"Request to {url} failed after {duration:.3f}s: {str(e)}")
            raise
    
    @lru_cache(maxsize=128)
    def _parse_manga_info(self, manga_type_text):
        """Parse manga info with caching for repeated patterns."""
        patterns = {
            "status": r"Status\s+(\w+)",
            "type": r"Type\s+(\w+)",
            "author": r"Author\s+([^P]+?)\s+Posted By",
            "posted_by": r"Posted By\s+(\w+)",
            "posted_on": r"Posted On\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            "updated_on": r"Updated On\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            "views": r"Views\s+(\S+)"
        }
        
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, manga_type_text)
            if match:
                result[key] = match.group(1).strip()
        return result
    
    def get_manga_list(self, page: int = 1, limit: int = None):
        """Get manga list with performance optimizations."""
        url = f'{self.base_url}/manga/?page={page}&order=update'
        
        try:
            response = self._make_request(url)
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            manga_elements = soup.find_all('div', class_="bsx")
            
            if limit:
                manga_elements = manga_elements[:limit]
            
            manga_list_data = []
            
            for element in manga_elements:
                try:
                    manga_data = self._parse_manga_element(element)
                    if manga_data:
                        serialized_manga = self.komik_schema.dump(manga_data)
                        manga_list_data.append(serialized_manga)
                except Exception as e:
                    logger.warning(f"Failed to parse manga element: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(manga_list_data)} manga items from page {page}")
            return manga_list_data
            
        except Exception as e:
            logger.error(f"Error fetching manga list for page {page}: {str(e)}")
            return None
    
    def _parse_manga_element(self, element):
        """Parse individual manga element with error handling."""
        try:
            title_elem = element.find('a')
            manga_title = title_elem.get('title', '') if title_elem else ''
            manga_url = title_elem.get('href', '') if title_elem else ''
            
            img_elem = element.find('img')
            manga_image = img_elem.get('src', '') if img_elem else ''
            
            rating_element = element.find('div', class_="numscore")
            manga_rating = rating_element.text.strip() if rating_element else "0"
            
            chapter_element = element.find('div', class_="epxs")
            manga_chapter = chapter_element.text.strip() if chapter_element else "0"
            
            chapter_num = re.findall(r'\d+', manga_chapter)
            total_chapter = int(chapter_num[0]) if chapter_num else 0
            
            try:
                rating_float = float(manga_rating) if manga_rating and manga_rating not in ['-', '', '0'] else 0.0
            except (ValueError, TypeError):
                rating_float = 0.0
            
            return {
                'id': manga_url.replace(self.base_url, '').strip('/'),
                'title': manga_title,
                'image': manga_image,
                'total_chapter': total_chapter,
                'rating': rating_float
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse manga element: {str(e)}")
            return None
    
    def get_manga_detail(self, manga_url: str):
        """Get manga detail with performance optimizations."""
        url = f'{self.base_url}/manga/{manga_url}'
        
        try:
            logger.info(f"Fetching manga detail for: {manga_url}")
            response = self._make_request(url)
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            title_elem = soup.find('h1', class_="entry-title")
            manga_title = title_elem.text.strip() if title_elem else "Unknown Title"
            
            img_element = soup.find('img', class_="attachment- size- wp-post-image")
            manga_image = img_element.get('src', '') if img_element else ""
            
            rating_element = soup.find('div', class_="num")
            manga_rating = rating_element.text.strip() if rating_element else "0"
            
            genre_elements = soup.find_all('span', class_="mgen")
            genre = []
            for elem in genre_elements:
                try:
                    link = elem.find_all('a')
                    for link in link:
                        if link and link.text:
                            genre.append(link.text.strip())
                except:
                    continue
            
            synopsis_element = soup.find('div', class_="entry-content entry-content-single")
            manga_synopsis = ""
            if synopsis_element:
                for script in synopsis_element(["script", "style"]):
                    script.decompose()
                manga_synopsis = synopsis_element.get_text().strip()
            
            chapter_elements = soup.findAll('div', class_="eph-num")
            chapter_list = []
            
            for elem in chapter_elements[1:] if len(chapter_elements) > 1 else chapter_elements:
                try:
                    link = elem.find('a')
                    if link and link.get('href'):
                        chapter_url = link['href'].replace(self.base_url, 'read')
                        if chapter_url:
                            chapter_list.append(chapter_url)
                except:
                    continue
            
            total_chapters = len(chapter_list)
            
            manga_type_elements = soup.find_all('div', class_="tsinfo bixbox")
            manga_type_text = ""
            if manga_type_elements:
                try:
                    manga_type_text = re.sub(r'\s+', ' ', manga_type_elements[0].get_text().strip())
                except:
                    manga_type_text = ""
            
            result = self._parse_manga_info(manga_type_text) if manga_type_text else {}
            
            views_str = result.get('views', '0')
            views_num = self._parse_views(views_str)
            
            year = self._extract_year(result)
            
            manga_detail_data = {
                'id': manga_url.strip('/'),
                'title': manga_title,
                'image': manga_image,
                'description': manga_synopsis[:100] + "..." if len(manga_synopsis) > 100 else manga_synopsis,
                'synopsis': manga_synopsis,
                'type': result.get('type', 'Manga'),
                'status': result.get('status', 'Unknown'),
                'year': year,
                'genre': genre,
                'chapter': total_chapters,
                'chapter_list': chapter_list,
                'author': result.get('author', 'Unknown'),
                'rating': manga_rating,
                'views': views_num
            }
            
            serialized_manga = self.komik_detail_schema.dump(manga_detail_data)
            logger.info(f"Successfully parsed manga detail for {manga_url}")
            return serialized_manga
            
        except Exception as e:
            logger.error(f"Error fetching manga detail for {manga_url}: {str(e)}")
            return None
        
    def _safe_get_text(self, element):
        """Safely get text from BeautifulSoup element."""
        return element.text.strip() if element else ""
    
    def _parse_views(self, views_str):
        """Parse view count with K/M suffix handling."""
        try:
            views_clean = views_str.replace(',', '')
            
            if 'K' in views_clean:
                return int(float(views_clean.replace('K', '')) * 1000)
            elif 'M' in views_clean:
                return int(float(views_clean.replace('M', '')) * 1000000)
            else:
                numbers = re.findall(r'\d+', views_clean)
                return int(numbers[0]) if numbers else 0
        except:
            return 0
    
    def _extract_year(self, result):
        """Extract year from date strings."""
        year = 2025  # default
        
        for date_key in ['posted_on', 'updated_on']:
            if result.get(date_key):
                year_match = re.search(r'\d{4}', result[date_key])
                if year_match:
                    return int(year_match.group())
        
        return year
    
    def search_manga(self, query: str, page: int = 1, limit: int = None):
        """Search manga with performance optimizations."""
        url = f'{self.base_url}/page/{page}/?s={query}'
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'lxml')
            all_data = soup.find_all('div', class_="bs")
            manga_list = []
            try:
                for element in all_data:
                    manga_data = self._parse_manga_element(element)
                    if manga_data:
                        manga_list.append(manga_data)
            except:
                logger.error(f"Failed to parse manga element: {str(e)}")
                return []
            logger.info(f"Successfully parsed {len(manga_list)} manga items")
            return manga_list
        except:
            return []
        
    def read_manga(self, manga_url: str):
        """Get chapter images with performance optimizations."""
        url = f'{self.base_url}/{manga_url}'
        
        try:
            logger.info(f"Fetching chapter images for: {manga_url}")
            response = self._make_request(url)
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            title_elem = soup.find('h1', class_="entry-title")
            manga_title = title_elem.text.strip() if title_elem else "Unknown Chapter"

            try:
                comic_data = parse_comic(response.text)
                sources = comic_data.get('sources', []) if comic_data else []
            except Exception as e:
                logger.error(f"Failed to parse comic data: {str(e)}")
                sources = []
            
            server_list = {}
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_server = {}
                
                for i, source in enumerate(sources[:3]):  # Limit to 3 servers
                    server_name = f'Server {i + 1}'
                    future = executor.submit(self._extract_images_from_source, source)
                    future_to_server[future] = server_name
                
                for future in as_completed(future_to_server, timeout=30):
                    server_name = future_to_server[future]
                    try:
                        images = future.result(timeout=10)
                        server_list[server_name] = images
                    except Exception as e:
                        logger.warning(f"Failed to extract images for {server_name}: {str(e)}")
                        server_list[server_name] = []
            
            for i in range(1, 4):
                server_name = f'Server {i}'
                if server_name not in server_list:
                    server_list[server_name] = []
            
            result = {
                'title': manga_title,
                'chapter': server_list
            }
        
            logger.info(f"Successfully parsed chapter images for {manga_url}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching chapter images for {manga_url}: {str(e)}")
            return None
    
    def _extract_images_from_source(self, source):
        """Extract images from a single source."""
        try:
            if isinstance(source, dict) and 'images' in source:
                images = []
                for img in source['images']:
                    if img and img.strip():
                        images.append(img.strip())
                return images
            return []
        except Exception as e:
            logger.warning(f"Failed to extract images from source: {str(e)}")
            return []
        
    def get_performance_stats(self):
        """Get performance statistics."""
        return {
            'request_count': self.request_count,
            'cache_hits': self.cache_hits,
            'cache_info': self._parse_manga_info.cache_info()._asdict()
        }
    
    def clear_cache(self):
        """Clear internal caches."""
        self._parse_manga_info.cache_clear()
        logger.info("Internal caches cleared")
    
    def close(self):
        """Close the session and cleanup resources."""
        if hasattr(self, 'session'):
            self.session.close()

class Mangaku(OptimizedMangaku):
    """Backward compatible Mangaku class."""
    pass
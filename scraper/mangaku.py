from .schema.komik_schema import KomikDetailSchema, KomikSchema
import requests
from bs4 import BeautifulSoup
import urllib3
from .utils.request_attr import headers
from .utils.parsing_comic import parse_comic
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Mangaku:
    def __init__(self):        
        self.base_url = 'https://mangaaku.com'
        self.headers = headers
        self.komik_schema = KomikSchema()
        self.komik_detail_schema = KomikDetailSchema()

    def get_manga_list(self, page: int = 1,):
        url = f'{self.base_url}/manga/?page={page}&order=update'
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=False,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            manga_list = soup.find_all('div', class_="bsx")
            manga_list_data = []
            for i in manga_list:
                manga_title = i.find('a')['title']
                manga_url = i.find('a')['href']
                manga_image = i.find('img')['src']
                manga_rating = i.find('div', class_="numscore").text
                manga_chapter = i.find('div', class_="epxs").text
                
                chapter_num = re.findall(r'\d+', manga_chapter)
                total_chapter = int(chapter_num[0]) if chapter_num else 0
                
                rating_float = float(manga_rating) if manga_rating and manga_rating != '-' else 0.0
                
                manga_data = {
                    'id': manga_url.replace(self.base_url, '').strip('/'),
                    'title': manga_title,
                    'image': manga_image,
                    'total_chapter': total_chapter,
                    'rating': rating_float
                }
                
                
                serialized_manga = self.komik_schema.dump(manga_data)
                manga_list_data.append(serialized_manga)
                
            return manga_list_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching manga list: {e}")
            return None
        
    def get_manga_detail(self, manga_url: str):
        url = f'{self.base_url}/manga/{manga_url}'
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=False,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            manga_title = soup.find('h1', class_="entry-title").text
            manga_image = soup.find('img', class_="attachment- size- wp-post-image")['src']
            manga_rating = soup.find('div', class_="num").text
            genre = [x.find('a').text.strip() for x in soup.find_all('span', class_="mgen")]
            synopsis_element = soup.find('div', class_="entry-content entry-content-single")
            manga_synopsis = synopsis_element.text.strip() if synopsis_element else ""
            
            chapter_list = [x.find('a')['href'].replace(self.base_url, '') for x in soup.findAll('div', class_="eph-num")]
            del chapter_list[0]
            
            manga_type_element = soup.find_all('div', class_="tsinfo bixbox")
            manga_type = re.sub(r'\s+', ' ', manga_type_element[0].text.strip()) if manga_type_element else ""
            
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
                match = re.search(pattern, manga_type)
                if match:
                    result[key] = match.group(1).strip()
            
           
            total_chapters = len(chapter_list)
            
            views_str = result.get('views', '0').replace(',', '').replace('K', '000').replace('M', '000000')
            views_num = int(re.findall(r'\d+', views_str)[0]) if re.findall(r'\d+', views_str) else 0
            
            year = 2025  
            if result.get('posted_on'):
                year_match = re.search(r'\d{4}', result['posted_on'])
                if year_match:
                    year = int(year_match.group())
            
            
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
            return serialized_manga
            
        except Exception as e:
            print(f"Error fetching manga detail: {e}")
            return None
        
    def read_manga(self, manga_url: str):
        url = f'{self.base_url}/{manga_url}'
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=False,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            manga_title = soup.find('h1', class_="entry-title").text
            manga_detail = [x.strip() for x in parse_comic(response.text)['sources'][0]['images']]
            try:
                manga_detail2 = [x.strip() for x in parse_comic(response.text)['sources'][1]['images']]
            except:
                manga_detail2 = []
            try:
                manga_detail3 = [x.strip() for x in parse_comic(response.text)['sources'][2]['images']]
            except:
                manga_detail3 = []
            server_list = {
                'Server 1': manga_detail,
                'Server 2': manga_detail2,
                'Server 3': manga_detail3
            }
            return {
                'title': manga_title,
                'chapter': server_list
            }
        
        except Exception as e:
            print(f"Error fetching manga detail: {e}")
            return None, 404
import re
import json

def parse_comic(html: str):
    match = re.search(r'ts_reader\.run\((\{.*?\})\);', html, re.S)
    if match:
        load_js = match.group(1)
        js_object = load_js.replace('\\/', '/')
        data = json.loads(js_object)
        return data
    return None
import requests
import xml.etree.ElementTree as ET

MAX_URLS = 100

def fetch_sitemap(sitemap_url):
    urls = []
    visited = set()

    def parse_sitemap(url):
        if url in visited or len(urls) >= MAX_URLS:
            return
        visited.add(url)

        try:
            resp = requests.get(url.strip(), timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            })
            if resp.status_code != 200:
                return
        except Exception:
            return

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError:
            return

        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        for sitemap in root.findall('sm:sitemap', ns):
            loc = sitemap.find('sm:loc', ns)
            if loc is not None and loc.text:
                parse_sitemap(loc.text.strip())

        for url_tag in root.findall('sm:url', ns):
            if len(urls) >= MAX_URLS:
                break
            loc = url_tag.find('sm:loc', ns)
            if loc is not None and loc.text:
                urls.append(loc.text.strip())

    parse_sitemap(sitemap_url.strip())
    return list(set(urls))[:MAX_URLS]

import json
import os
from datetime import datetime, timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests as http_requests

from .utils.sitemap import fetch_sitemap
from .utils.categorizer import categorize_urls
from .utils.extractor import extract_all_links
from .utils.graph_builder import build_graph_data
from .utils.html_generator import generate_html


def log_to_sheet(sitemap_url, pages, links):
    webhook = os.environ.get('SHEETS_WEBHOOK_URL')
    if not webhook:
        return
    try:
        http_requests.post(webhook, json={
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'sitemap_url': sitemap_url,
            'pages': pages,
            'links': links,
        }, timeout=5)
    except Exception:
        pass


def cors_response(response):
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@csrf_exempt
def generate_view(request):
    if request.method == 'OPTIONS':
        return cors_response(HttpResponse())
    try:
        body = json.loads(request.body)
        sitemap_url = body.get('sitemap_url', '').strip()
    except Exception:
        return cors_response(JsonResponse({'error': 'Invalid request body.'}, status=400))

    if not sitemap_url:
        return cors_response(JsonResponse({'error': 'sitemap_url is required.'}, status=400))

    if not sitemap_url.startswith('http'):
        return cors_response(JsonResponse({'error': 'sitemap_url must start with http or https.'}, status=400))

    try:
        urls = fetch_sitemap(sitemap_url)
        if not urls:
            return cors_response(JsonResponse({'error': 'No URLs found in sitemap. Check the URL and try again.'}, status=400))

        categorized = categorize_urls(urls)
        links  = extract_all_links(categorized)
        graph  = build_graph_data(categorized, links)
        html   = generate_html(graph, sitemap_url)

        stats = {
            'total_pages': len(graph['nodes']),
            'total_links': len(graph['links']),
        }

        log_to_sheet(sitemap_url, stats['total_pages'], stats['total_links'])
        return cors_response(JsonResponse({'html': html, 'stats': stats}))

    except Exception as e:
        return cors_response(JsonResponse({'error': f'Something went wrong: {str(e)}'}, status=500))


def health_view(request):
    return cors_response(JsonResponse({'status': 'ok'}))

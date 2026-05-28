from urllib.parse import urlparse


def build_graph_data(categorized_urls, links):
    def make_label(url):
        path = urlparse(url).path.rstrip('/')
        slug = path.split('/')[-1]
        return slug.replace('-', ' ').title()

    nodes = []
    seen_ids = set()

    for pages in categorized_urls.values():
        for url in pages:
            node_id = url.rstrip('/')
            if node_id in seen_ids:
                continue
            seen_ids.add(node_id)
            nodes.append({
                'id':    node_id,
                'label': make_label(url),
            })

    filtered_links = [
        l for l in links
        if l['source'] in seen_ids and l['target'] in seen_ids
    ]

    return {'nodes': nodes, 'links': filtered_links}

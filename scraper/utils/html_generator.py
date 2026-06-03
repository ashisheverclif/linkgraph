import json


def generate_html(graph_data, domain):
    nodes_json = json.dumps(graph_data['nodes'])
    links_json = json.dumps(graph_data['links'])

    total_nodes = len(graph_data['nodes'])
    total_links = len(graph_data['links'])

    in_deg  = {}
    out_deg = {}
    for node in graph_data['nodes']:
        in_deg[node['id']]  = 0
        out_deg[node['id']] = 0
    for l in graph_data['links']:
        in_deg[l['target']]  = in_deg.get(l['target'], 0) + 1
        out_deg[l['source']] = out_deg.get(l['source'], 0) + 1

    orphan_count      = sum(1 for n in graph_data['nodes'] if in_deg[n['id']] == 0 and out_deg[n['id']] == 0)
    no_inbound_count  = sum(1 for n in graph_data['nodes'] if in_deg[n['id']] == 0 and out_deg[n['id']] > 0)
    no_outbound_count = sum(1 for n in graph_data['nodes'] if out_deg[n['id']] == 0 and in_deg[n['id']] > 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{domain} — Internal Link Graph</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 16px 20px 24px; background: #f9f9f7; color: #1a1a18; }}
  h1 {{ font-size: 26px; font-weight: 500; margin: 0 0 3px; }}
  .subtitle {{ font-size: 12px; color: #73726c; margin: 0 0 12px; }}
  .controls {{ display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; align-items: center; }}
  .controls button {{ font-size: 11px; padding: 4px 10px; border: 0.5px solid #d3d1c7; border-radius: 6px; background: #fff; cursor: pointer; color: #444; }}
  .controls button:hover {{ background: #f1efe8; }}
  .fstat {{ background: #f1efe8; border-radius: 8px; padding: 5px 16px; font-size: 11px; color: #5f5e5a; text-align: center; cursor: pointer; border: 0.5px solid transparent; user-select: none; }}
  .fstat:hover {{ background: #e8e6df; }}
  .fstat.active {{ border-color: #1a1a18; }}
  .fstat b {{ font-size: 20px; font-weight: 600; display: block; }}
  #wrapper {{ position: relative; background: #fff; border: 0.5px solid #d3d1c7; border-radius: 10px; overflow: hidden; }}
  .watermark {{
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%) rotate(-35deg);
    font-size: 96px; font-weight: 800; white-space: nowrap;
    pointer-events: none; user-select: none; z-index: 1; line-height: 1;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }}
  #tt {{
    position: absolute; pointer-events: none; display: none;
    background: #fff; border: 0.5px solid #d3d1c7; border-radius: 8px;
    padding: 9px 11px; font-size: 11px; color: #1a1a18;
    max-width: 260px; z-index: 30; line-height: 1.6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  svg {{ display: block; background: transparent; position: relative; z-index: 2; }}
  .hint {{ font-size: 10px; color: #888780; margin: 6px 0 0; }}
</style>
</head>
<body>

<h1>{domain} — Internal Link Graph</h1>
<p class="subtitle">{total_nodes} pages · {total_links} internal links · node size = inbound links</p>

<div class="controls">
  <div class="fstat" id="btn-orphan" onclick="filterNodes('orphan')">
    <b style="color:#D85A30">{orphan_count}</b>Orphans
  </div>
  <div class="fstat" id="btn-no-inbound" onclick="filterNodes('no-inbound')">
    <b style="color:#378ADD">{no_inbound_count}</b>No Inbound
  </div>
  <div class="fstat" id="btn-no-outbound" onclick="filterNodes('no-outbound')">
    <b style="color:#9B59B6">{no_outbound_count}</b>No Outbound
  </div>
</div>
<div class="controls" style="margin-top:0">
  <button onclick="resetZoom()">Reset zoom</button>
  <button onclick="reheat()">Reorganise</button>
</div>

<div id="wrapper">
  <div class="watermark">
    <span style="color:rgba(180,210,240,0.18)">Ever</span><span style="color:rgba(185,182,220,0.18)">Clif↗</span>
  </div>
  <div id="tt"></div>
  <svg id="g" width="100%" height="720"></svg>
</div>
<p class="hint">Scroll to zoom · Drag canvas to pan · Drag nodes to reposition · Hover for details</p>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script>
const NODE_COLOR = '#378ADD';

const nodesData = {nodes_json};
const linksData = {links_json};

const nodeMap = new Map(nodesData.map(n => [n.id, n]));
const inDeg = {{}}, outDeg = {{}};
nodesData.forEach(n => {{ inDeg[n.id] = 0; outDeg[n.id] = 0; }});
linksData.forEach(l => {{
  inDeg[l.target]  = (inDeg[l.target]  || 0) + 1;
  outDeg[l.source] = (outDeg[l.source] || 0) + 1;
}});

const nodeRadius = d => Math.min(32, 6 + (inDeg[d.id] || 0) * 3.5);

const W = 960, H = 720;
const svg  = d3.select('#g');
const defs = svg.append('defs');

defs.append('marker')
  .attr('id','arr').attr('viewBox','0 0 10 10').attr('refX',9).attr('refY',5)
  .attr('markerWidth',5).attr('markerHeight',5).attr('orient','auto-start-reverse')
  .append('path').attr('d','M2 1L8 5L2 9')
  .attr('fill','none').attr('stroke',NODE_COLOR)
  .attr('stroke-width',1.5).attr('stroke-linecap','round').attr('stroke-linejoin','round');

const zoom = d3.zoom().scaleExtent([0.2,4]).on('zoom', e => g.attr('transform', e.transform));
svg.call(zoom);
const g = svg.append('g');

function resetZoom() {{ svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity.translate(W/2,H/2).scale(0.7).translate(-W/2,-H/2)); }}
function reheat()     {{ sim.alpha(0.5).restart(); }}
window.resetZoom = resetZoom;
window.reheat    = reheat;

const sim = d3.forceSimulation(nodesData)
  .force('link',    d3.forceLink(linksData).id(d=>d.id).distance(160).strength(0.4))
  .force('charge',  d3.forceManyBody().strength(-600))
  .force('center',  d3.forceCenter(W/2, H/2))
  .force('x',       d3.forceX(W/2).strength(0.08))
  .force('y',       d3.forceY(H/2).strength(0.08))
  .force('collide', d3.forceCollide().radius(d => nodeRadius(d)+40).strength(0.9))
  .alphaDecay(0.03)
  .alphaMin(0.001);

const link = g.append('g').selectAll('line').data(linksData).join('line')
  .attr('fill','none')
  .attr('stroke', NODE_COLOR)
  .attr('stroke-width', 1)
  .attr('stroke-opacity', 0.45)
  .attr('marker-end','url(#arr)');

const node = g.append('g').selectAll('g').data(nodesData).join('g').style('cursor','pointer')
  .call(d3.drag()
    .on('start',(e,d)=>{{ if(!e.active) sim.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }})
    .on('drag', (e,d)=>{{ d.fx=e.x; d.fy=e.y; }})
    .on('end',  (e,d)=>{{ if(!e.active) sim.alphaTarget(0); d.fx=null; d.fy=null; }}));

node.append('circle')
  .attr('r', d => nodeRadius(d))
  .attr('fill', NODE_COLOR)
  .attr('stroke','#fff')
  .attr('stroke-width',2);

node.append('text')
  .attr('text-anchor','middle').attr('dominant-baseline','hanging')
  .attr('font-size','10px').attr('font-family','sans-serif')
  .attr('fill','#444441').attr('pointer-events','none')
  .attr('dy', d => nodeRadius(d) + 4)
  .text(d => d.label);

const tt      = document.getElementById('tt');
const wrapper = document.getElementById('wrapper');

node.on('mouseenter', (e, d) => {{
  const isOrphan = inDeg[d.id] === 0 && outDeg[d.id] === 0;
  tt.innerHTML = `
    <span style="font-weight:500;font-size:12px">${{d.label}}</span>
    ${{isOrphan ? '<br><span style="color:#D85A30;font-size:10px">⚠ No internal links</span>' : ''}}
    <br><span style="color:#888;font-size:10px;word-break:break-all">${{d.id}}</span>
    <br><span style="font-size:10px;color:#5f5e5a">← in: <b>${{inDeg[d.id]||0}}</b> &nbsp; out: <b>${{outDeg[d.id]||0}}</b> →</span>
  `;
  tt.style.display = 'block';
}})
.on('mousemove', e => {{
  const wr = wrapper.getBoundingClientRect();
  let x = e.clientX - wr.left + 14;
  let y = e.clientY - wr.top  - 55;
  if (x + 270 > wr.width) x = e.clientX - wr.left - 280;
  if (y < 0)              y = 4;
  tt.style.left = x + 'px';
  tt.style.top  = y + 'px';
}})
.on('mouseleave', () => {{ tt.style.display = 'none'; }});

sim.on('tick', () => {{
  link
    .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
    .attr('x2', d => {{
      const r = nodeRadius(d.target);
      const dx = d.target.x - d.source.x, dy = d.target.y - d.source.y;
      const dist = Math.sqrt(dx*dx+dy*dy)||1;
      return d.target.x - (dx/dist)*(r+8);
    }})
    .attr('y2', d => {{
      const r = nodeRadius(d.target);
      const dx = d.target.x - d.source.x, dy = d.target.y - d.source.y;
      const dist = Math.sqrt(dx*dx+dy*dy)||1;
      return d.target.y - (dy/dist)*(r+8);
    }});
  node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
}});

const FILTER_COLORS = {{
  'orphan':      '#D85A30',
  'no-inbound':  '#378ADD',
  'no-outbound': '#9B59B6',
}};

let activeFilter = null;

function applyVisibility() {{
  if (activeFilter) {{
    const highlighted = new Set(nodesData.filter(d => {{
      if (activeFilter === 'orphan')      return inDeg[d.id] === 0 && outDeg[d.id] === 0;
      if (activeFilter === 'no-inbound')  return inDeg[d.id] === 0 && outDeg[d.id] > 0;
      if (activeFilter === 'no-outbound') return outDeg[d.id] === 0 && inDeg[d.id] > 0;
    }}).map(d => d.id));
    node.attr('opacity', d => highlighted.has(d.id) ? 1 : 0.08);
    node.select('circle').attr('fill', d => highlighted.has(d.id) ? FILTER_COLORS[activeFilter] : NODE_COLOR);
    link.attr('opacity', 0.04);
  }} else {{
    node.attr('opacity', 1);
    node.select('circle').attr('fill', NODE_COLOR);
    link.attr('opacity', 0.45);
  }}
}}

function filterNodes(type) {{
  if (activeFilter === type) {{
    activeFilter = null;
    document.querySelectorAll('#btn-orphan,#btn-no-inbound,#btn-no-outbound').forEach(b => b.classList.remove('active'));
  }} else {{
    activeFilter = type;
    document.querySelectorAll('#btn-orphan,#btn-no-inbound,#btn-no-outbound').forEach(b => b.classList.remove('active'));
    document.getElementById('btn-' + type).classList.add('active');
  }}
  applyVisibility();
}}
window.filterNodes = filterNodes;
</script>
</body>
</html>"""

    return html

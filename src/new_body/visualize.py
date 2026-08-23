"""Generate an interactive HTML explorer from the live control-plane model.

``render_explorer`` turns a :class:`Surrogate` (and optional :class:`HumanTwin`)
into a self-contained, dependency-free HTML page with a clickable topology,
live Cat-8 / PoE++ calculators, and the full subsystem + twin tables. The
``new-body explore`` CLI command writes this to disk, so the *same* code that
validates the rig also produces the most intuitive view of it.

No external assets, no build step — the page runs from ``file://``.
"""

from __future__ import annotations

from .body import HumanTwin
from .surrogate import Surrogate

_CSS = """
:root{--bg:#0b0f17;--panel:#121a28;--panel2:#0f1623;--border:#22304a;
--ink:#e6edf3;--dim:#90a0b6;--faint:#61708a;--accent:#4cc2ff;--good:#4cff9d;
--bad:#ff6b6b;--gold:#ffcf4c;--mono:"SFMono-Regular",Consolas,Menlo,monospace;
--sans:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 var(--sans)}a{color:var(--accent)}.wrap{max-width:980px;margin:0 auto;padding:30px}
header.hero{padding:40px 0 24px;border-bottom:1px solid var(--border)}
.eyebrow{color:var(--accent);font-weight:700;letter-spacing:1.4px;text-transform:uppercase;font-size:12px}
h1{font-size:34px;color:#fff;margin:8px 0}
.lede{color:var(--dim);max-width:720px}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-top:22px}
.fact{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:13px}
.fact .k{font-size:11px;text-transform:uppercase;color:var(--faint)}
.fact .v{font-size:15px;font-weight:700;margin-top:4px;color:var(--accent)}
section{padding:34px 0;border-bottom:1px solid var(--border)}
h2{font-size:24px;color:#fff;margin:0 0 12px}
h3{font-size:17px;color:var(--accent);margin:24px 0 8px}
table.t{width:100%;border-collapse:collapse;margin:12px 0;font-size:13.5px}
table.t th,table.t td{border:1px solid var(--border);padding:9px 11px;text-align:left}
table.t th{background:#13202f;color:#fff}table.t tr:nth-child(even) td{background:rgba(255,255,255,.02)}
.mono{font-family:var(--mono);color:var(--accent)}
.tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;background:#13283c;color:var(--accent);border:1px solid #2c3e5c}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:18px;margin:16px 0;box-shadow:0 10px 40px rgba(0,0,0,.4)}
.diagram{background:#070b12;border:1px solid var(--border);border-radius:10px;padding:16px;font-family:var(--mono);font-size:12px;color:var(--accent);overflow-x:auto;white-space:pre}
.topo{width:100%;height:auto;display:block;background:radial-gradient(800px 300px at 50% 0%,rgba(76,194,255,.06),transparent)}
.topo .node{cursor:pointer}.topo .node rect{fill:#0f1a28;stroke:#2c3e5c;stroke-width:1.5;transition:.15s}
.topo .node:hover rect,.topo .node.sel rect{stroke:var(--accent);fill:#173a55}
.topo .node text{fill:var(--ink);font:600 12px var(--sans);pointer-events:none}
.topo .node .sub{fill:var(--faint);font:500 10px var(--mono);pointer-events:none}
.topo .link{stroke:#2a3b57;stroke-width:1.5;fill:none}.topo .pwr{stroke:#4cff9d;stroke-width:2;fill:none;stroke-dasharray:5 4}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.calc{display:grid;grid-template-columns:300px 1fr;gap:18px}
.field{margin-bottom:12px}.field label{display:block;font-size:12.5px;color:var(--dim);margin-bottom:5px;display:flex;justify-content:space-between}
.field label b{color:var(--accent);font-family:var(--mono)}
input[type=range]{width:100%;accent-color:var(--accent)}
.readout{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.metric{background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:11px}
.metric .mk{font-size:11px;text-transform:uppercase;color:var(--faint)}
.metric .mv{font-size:21px;font-weight:800;color:#fff;margin-top:3px}
.metric .mv.accent{color:var(--accent)}.metric .mv.good{color:var(--good)}.metric .mv.bad{color:var(--bad)}
.gauge{height:12px;border-radius:8px;background:#0a111c;border:1px solid var(--border);overflow:hidden;margin-top:8px}
.gauge>span{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--good))}
.note{font-size:12.5px;margin-top:10px;padding:10px 12px;border-radius:10px;border:1px solid var(--border)}
.note.ok{border-color:#1c5436;background:#0d2418;color:var(--good)}
.note.warn{border-color:#5c4a16;background:#241c0d;color:var(--gold)}
.card{background:var(--panel2);border:1px solid var(--border);border-radius:12px;padding:14px}
.organs,.mind{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px;margin-top:8px}
.organ,.mcard{background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:10px 12px}
.organ .on,.mcard .mn{font-weight:600;color:#fff}.organ .ov{font-family:var(--mono);font-size:11.5px;color:var(--dim);margin-top:4px}
.organ .ov .in{color:var(--good)}
#detail{position:sticky;top:14px}.dsub{color:var(--accent);font-family:var(--mono);font-size:12px}
.dh{color:#fff;margin:0 0 6px;font-size:18px}
footer{color:var(--faint);font-size:12px;text-align:center;padding:26px}
@media(max-width:760px){.grid2,.calc{grid-template-columns:1fr}}
"""


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cat8_calc_js() -> str:
    return """
const MAX_T=40,MAX_D=30;
function catCalc(){
  const len=parseFloat(len_.value),pay=parseInt(pay_.value),shd=parseInt(shd_.value)===1;
  lenVal.textContent=len;payVal.textContent=pay;shdVal.textContent=shd?'YES':'NO';
  const over=len>MAX_D,rate=over?10:MAX_T,lat=(pay*8)/(rate*1000);
  rate_.textContent=rate+' Gb/s';lat_.textContent=lat.toFixed(3)+' µs';
  geo_.textContent=over?'OVER':'OK';geo_.className='mv '+(over?'bad':'good');
  emi_.textContent=shd?'OK':'RISK';emi_.className='mv '+(shd?'good':'bad');
  rateBar.style.width=(rate/MAX_T*100)+'%';
  let n=document.getElementById('catNote');
  if(over){n.className='note warn';n.textContent='Down-negotiated to 10 Gbps — link exceeds the 30 m geometric limit.';}
  else if(!shd){n.className='note warn';n.textContent='Unshielded pair: exposed to EMI. Use S/FTP.';}
  else{n.className='note ok';n.textContent='Full 40 Gbps operation — within 30 m, shielded.';}
}
"""


def render_explorer(surrogate: Surrogate, twin: HumanTwin | None = None) -> str:
    """Return a self-contained HTML string describing the live model."""
    t = surrogate.telemetry()
    ports_html = "".join(
        f"<tr><td class='mono'>{p.port_id:02d}</td><td>{_esc(p.subsystem)}</td>"
        f"<td>{_esc(p.interface_type)}</td><td class='mono'>{_esc(p.protocol)}</td>"
        f"<td><span class='tag'>{_esc(p.poe_class or 'Unpowered')}</span></td>"
        f"<td>{p.link.effective_throughput_gbps():.0f} Gb/s</td></tr>"
        for p in surrogate.patch_panel.ports
    )

    poe_html = ""
    for sub, delivery in surrogate.poe.items():
        poe_html += (
            f"<h3 style='margin-top:14px'>{_esc(sub)}</h3>"
            f"<div class='diagram'>{_esc(delivery.diagram())}</div>"
        )

    twin_html = ""
    if twin is not None:
        tt = twin.telemetry()
        sys_blocks = ""
        for s in twin.systems:
            organs = "".join(
                f"<div class='organ'><div class='on'>{_esc(o.name)}</div>"
                f"<div class='ov'>port {o.port} · "
                + " · ".join(
                    f"{_esc(v.name)} {v.value}{_esc(v.unit)} "
                    f"<span class='{'in' if v.in_range() else ''}'>"
                    f"{'✓' if v.in_range() else '✗'}</span>"
                    for v in o.vitals
                )
                + "</div></div>"
                for o in s.organs
            )
            sys_blocks += (
                f"<div class='card' style='margin-top:10px'><div class='on' "
                f"style='font-weight:700;color:#fff'>{_esc(s.name)}</div>"
                f"<div class='organs'>{organs}</div></div>"
            )
        mind_blocks = "".join(
            f"<div class='mcard'><div class='mn'>{_esc(m.name)}</div>"
            f"<div class='ov' style='font-family:inherit;color:var(--faint);font-size:11.5px'>"
            f"linked: {_esc(m.linked_system)} · {m.activation:.0%}</div></div>"
            for m in twin.mind
        )

        # Human nature layer (instinct emphasized as the encoded substrate).
        _order = [
            "Instinct",
            "Temperament (Big Five)",
            "Value Orientation",
            "Moral Foundations",
            "Higher Nature",
        ]
        _groups: dict[str, list] = {}
        for c in twin.nature.constructs:
            _groups.setdefault(c.group, []).append(c)
        nature_blocks = ""
        for gname in _order:
            if gname not in _groups:
                continue
            chips = "".join(
                f"<div class='mcard'><div class='mn'>{_esc(c.name)}</div>"
                f"<div class='ma'><span style='width:{c.value*100:.0f}%'></span></div>"
                f"<div class='ov' style='font-family:inherit;color:var(--faint);"
                f"font-size:11px;margin-top:4px'>{c.value:.0%}</div></div>"
                for c in _groups[gname]
            )
            emphasis = (
                " <span class='tag gold'>encoded substrate</span>"
                if gname == "Instinct"
                else ""
            )
            nature_blocks += (
                f"<h3 style='margin-top:18px'>{_esc(gname)}{emphasis}</h3>"
                f"<div class='mind'>{chips}</div>"
            )

        twin_html = f"""
        <section id="twin">
          <h2>Human Body, Mind &amp; Nature Twin — {_esc(twin.name)}</h2>
          <p class='lede'>{tt['body_systems']} body systems ({tt['organs']} organs),
          {tt['mind_modules']} cognitive modules, and {tt['nature_constructs']} human-nature
          constructs across {tt['nature_groups']} groups on {tt['surrogate_ports']} Cat-8
          ports. Overall status: <b style='color:var(--good)'>{tt['overall_status']}</b>.</p>
          {sys_blocks}
          <h3>Cognitive Mind Modules</h3>
          <div class='mind'>{mind_blocks}</div>
          <h3>Human Nature <span class='tag gold'>PROTO_NATURE</span></h3>
          <p style='color:var(--dim)'>Instinct is the survival/reflexive bedrock encoded
          directly into the artificial nervous system; the remaining groups layer
          temperament, values, moral foundations, and higher nature on top.</p>
          {nature_blocks}
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>New Body Explorer — {_esc(t['name'])}</title><style>{_CSS}</style></head>
<body><div class="wrap">
<header class="hero">
  <div class="eyebrow">New Body · live control-plane explorer</div>
  <h1>{_esc(t['name'])}</h1>
  <div class="lede">Interactive topology generated directly from the running
  <code>Surrogate</code> model. Click nodes, tune the link calculator, inspect
  every subsystem and (optionally) the human digital twin.</div>
  <div class="facts">
    <div class="fact"><div class="k">Core Platform</div><div class="v">{_esc(t['core_platform'])}</div></div>
    <div class="fact"><div class="k">VR Integration</div><div class="v">{_esc(t['vr_integration'])}</div></div>
    <div class="fact"><div class="k">Ports</div><div class="v">{t['ports']}</div></div>
    <div class="fact"><div class="k">Subsystems</div><div class="v">{len(t['subsystems'])}</div></div>
    <div class="fact"><div class="k">PoE Draw</div><div class="v">{t['total_poe_watts']:.0f} W</div></div>
  </div>
</header>

<section>
  <h2>Interactive Topology</h2>
  <div class="grid2">
    <div class="panel" style="padding:14px">
      <svg class="topo" viewBox="0 0 620 470" role="img" aria-label="Topology">
        <path class="link" d="M300,40 L300,92"/>
        <path class="link" d="M150,150 L150,210"/><path class="link" d="M300,150 L300,210"/>
        <path class="link" d="M450,150 L450,210"/><path class="pwr" d="M560,250 L470,250"/>
        <path class="link" d="M150,262 L150,330"/><path class="link" d="M300,262 L300,330"/>
        <path class="link" d="M450,262 L450,330"/><path class="link" d="M300,360 L300,410"/>
        <g class="node" data-node="hub"><rect x="225" y="10" width="150" height="44" rx="9"/>
          <text x="300" y="31" text-anchor="middle">Workstation Hub</text>
          <text x="300" y="46" text-anchor="middle" class="sub">remote uplink</text></g>
        <g class="node" data-node="panel"><rect x="215" y="98" width="190" height="46" rx="9"/>
          <text x="310" y="119" text-anchor="middle">12-Port Patch Panel</text>
          <text x="310" y="134" text-anchor="middle" class="sub">grounded mini-panel</text></g>
        <g class="node" data-node="head"><rect x="92" y="210" width="116" height="52" rx="9"/>
          <text x="150" y="232" text-anchor="middle">Head &amp; Sensory</text>
          <text x="150" y="247" text-anchor="middle" class="sub">ports 01–02</text></g>
        <g class="node" data-node="torso"><rect x="242" y="210" width="116" height="52" rx="9"/>
          <text x="300" y="232" text-anchor="middle">Upper Torso</text>
          <text x="300" y="247" text-anchor="middle" class="sub">ports 03–06</text></g>
        <g class="node" data-node="rig"><rect x="392" y="210" width="116" height="52" rx="9"/>
          <text x="450" y="232" text-anchor="middle">Lower Base &amp; Rig</text>
          <text x="450" y="247" text-anchor="middle" class="sub">ports 07–08</text></g>
        <g class="node" data-node="env"><rect x="470" y="98" width="120" height="46" rx="9"/>
          <text x="530" y="119" text-anchor="middle">PoE++ Injector</text>
          <text x="530" y="134" text-anchor="middle" class="sub">90 W per line</text></g>
        <g class="node" data-node="chassis"><rect x="92" y="330" width="116" height="60" rx="9"/>
          <text x="150" y="354" text-anchor="middle">Mini-Chassis</text>
          <text x="150" y="370" text-anchor="middle" class="sub">slide rail · hex · ESD</text></g>
        <g class="node" data-node="twin"><rect x="242" y="330" width="116" height="60" rx="9"/>
          <text x="300" y="354" text-anchor="middle">Human Twin</text>
          <text x="300" y="370" text-anchor="middle" class="sub">ports 13+</text></g>
        <g class="node" data-node="umbilical"><rect x="392" y="330" width="116" height="60" rx="9"/>
          <text x="450" y="354" text-anchor="middle">External Umbilical</text>
          <text x="450" y="370" text-anchor="middle" class="sub">ports 11–12</text></g>
      </svg>
    </div>
    <div class="panel" id="detail">
      <p class="dsub">// select a node</p>
      <h3 class="dh">New Body Topology</h3>
      <p style="color:var(--dim)">Click any node in the schematic to load its
      specification. Green dashed lines are the PoE++ power plane.</p>
    </div>
  </div>
</section>

<section>
  <h2>Patch Panel — Live Layout</h2>
  <table class="t"><thead><tr><th>Port</th><th>Subsystem</th><th>Interface</th>
  <th>Protocol</th><th>Power</th><th>Rate</th></tr></thead>
  <tbody>{ports_html}</tbody></table>
</section>

<section>
  <h2>PoE++ Delivery Paths</h2>
  {poe_html}
</section>

<section>
  <h2>Cat-8 Link Calculator</h2>
  <div class="panel"><div class="calc">
    <div>
      <div class="field"><label>Link length <b><span id="lenVal">4.5</span> m</b></label>
        <input type="range" id="len" min="0.5" max="60" step="0.5" value="4.5"></div>
      <div class="field"><label>Payload size <b><span id="payVal">64</span> B</b></label>
        <input type="range" id="pay" min="8" max="1500" step="8" value="64"></div>
      <div class="field"><label>Shielded (S/FTP) <b id="shdVal">YES</b></label>
        <input type="range" id="shd" min="0" max="1" step="1" value="1"></div>
    </div>
    <div>
      <div class="readout">
        <div class="metric"><div class="mk">Negotiated Rate</div><div class="mv accent" id="rate">40 Gb/s</div></div>
        <div class="metric"><div class="mk">Latency</div><div class="mv" id="lat">0.013 µs</div></div>
        <div class="metric"><div class="mk">Geometric Limit</div><div class="mv good" id="geo">OK</div></div>
        <div class="metric"><div class="mk">EMI Isolation</div><div class="mv good" id="emi">OK</div></div>
      </div>
      <div class="gauge"><span id="rateBar" style="width:100%"></span></div>
      <div class="note ok" id="catNote">Full 40 Gbps operation — within 30 m, shielded.</div>
    </div>
  </div></div>
</section>

{twin_html}

<footer>New Body Explorer · generated from the live control-plane model
(<code>new_body.visualize</code>).</footer>
</div>
<script>
const NODES={{
  hub:{{t:"Workstation Hub",b:"Drives the surrogate via the unpowered External Umbilical (ports 11–12). All rig power is injected locally."}},
  panel:{{t:"12-Port Patch Panel",b:"Grounded mini-panel in the lower base frame marshaling every subsystem link over 40GBASE-T."}},
  head:{{t:"Head & Sensory",b:"Face-tracking cameras + spatial mics (ports 01–02), PoE++ ≤30W, lowest-latency path."}},
  torso:{{t:"Upper Torso & Kinetic",b:"Haptic arrays + expression servos (ports 03–06), PoE++ ≤90W, isolated from main PSU."}},
  rig:{{t:"Lower Base & Rig",b:"Alignment encoders + security interlocks (ports 07–08), PoE++ ≤15W, safety-critical."}},
  env:{{t:"Environmental Matrix",b:"Cooling pumps + intake fans (ports 09–10), PoE++ ≤90W, decoupled thermal loop."}},
  injector:{{t:"PoE++ Injector",b:"IEEE 802.3bt Type 4 source — 90 W per line, split into 5V/12V rails at the node."}},
  chassis:{{t:"Mini-Chassis",b:"10-inch 3D-printed enclosure: slide-out rail, hex ventilation, ESD drain to earth."}},
  twin:{{t:"Human Twin",b:"11 body systems + 10 mind modules on ports 13+, serialized as PROTO_BIOMETRIC/COGNITIVE frames."}},
  umbilical:{{t:"External Umbilical",b:"Ports 11–12, data-only (unpowered) uplink to the workstation hub."}}
}};
function showNode(id){{const n=NODES[id];if(!n)return;
  document.querySelectorAll('.topo .node').forEach(g=>g.classList.toggle('sel',g.dataset.node===id));
  document.getElementById('detail').innerHTML=
    '<p class="dsub">// node</p><h3 class="dh">'+n.t+'</h3><p style="color:var(--dim)">'+n.b+'</p>';}}
document.querySelectorAll('.topo .node').forEach(g=>g.addEventListener('click',()=>showNode(g.dataset.node)));
{_cat8_calc_js()}
const len_=document.getElementById('len'),pay_=document.getElementById('pay'),shd_=document.getElementById('shd');
const lenVal=document.getElementById('lenVal'),payVal=document.getElementById('payVal'),shdVal=document.getElementById('shdVal');
const rate_=document.getElementById('rate'),lat_=document.getElementById('lat'),geo_=document.getElementById('geo'),emi_=document.getElementById('emi'),rateBar=document.getElementById('rateBar');
[len_,pay_,shd_].forEach(el=>el.addEventListener('input',catCalc));
catCalc();
</script></body></html>"""


def write_explorer(
    path: str,
    surrogate: Surrogate | None = None,
    twin: HumanTwin | None = None,
) -> str:
    """Render the explorer for ``surrogate``/``twin`` and write it to ``path``.

    Returns the output path. Defaults to a factory-default surrogate (+ twin).
    """
    if surrogate is None:
        surrogate = Surrogate.factory_default()
    if twin is None:
        twin = HumanTwin.factory_default()
    html = render_explorer(surrogate, twin)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return path

"""Barakaly admin dashboard markup. Same control-room structure as the provided
design template, but re-skinned to the app's own light gold theme (cream/white
surfaces, gold accents, Fraunces display + Inter body) so it matches the rest of
the platform. `render(d, user, _html, json)` returns a self-contained HTML
document — CSS + Chart.js + the marketplace's real data injected — dropped into
an iframe via st.components.v1.html. Kept separate from _analytics.py so the
data layer stays readable.
"""

from __future__ import annotations

from app import shared

# Warm gold gradient for the conversion funnel bars.
_FUNNEL_COLORS = ["#B8862A", "#C9A24E", "#D7B772", "#E3CB9B", "#EFDFC2"]
_BADGE_ICON = {"success": "ti-check", "warning": "ti-clock",
               "danger": "ti-x", "info": "ti-mail"}


def _initials(user) -> str:
    name = (user.get("display_name") or user.get("name") or user.get("email") or "Admin").strip()
    parts = [p for p in name.replace("@", " ").split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return (parts[0][:2] if parts else "AD").upper()


def render(d: dict, user: dict, _html, json) -> str:
    esc = _html.escape

    # Inline the Barakaly bloom mark (same logo as the rest of the app).
    from pathlib import Path
    try:
        mark_svg = (Path(__file__).resolve().parents[1] / "assets" / "logo_icon.svg").read_text()
    except Exception:
        mark_svg = "B"

    # ---- ticker (real metrics, no fabricated trend arrows) ----
    tick = [
        f"GMV TODAY <strong class='mono'>{shared.money(d['gmv_today'])}</strong>",
        f"ORDERS TODAY <strong class='mono'>{d['orders_today']:,}</strong>",
        f"NEW SIGNUPS (30D) <strong class='mono'>{d['new_30']:,}</strong>",
        f"TOTAL GMV <strong class='mono'>{shared.money(d['gmv'])}</strong>",
        f"REPEAT RATE <strong class='mono'>{d['repeat_rate']:.1f}%</strong>",
        f"CART ABANDON <strong class='mono'>{d['cart_abandon']:.1f}%</strong>",
        f"AVG RATING <strong class='mono'>{d['avg_rating']:.1f}/5</strong>",
    ]
    ticker_inner = "".join(f"<span>{t}</span>" for t in tick)
    ticker_inner = ticker_inner + ticker_inner  # duplicate for seamless scroll

    # ---- dashboard metric deltas ----
    def delta(pair):
        cls, txt = pair
        icon = {"up": "ti-arrow-up", "down": "ti-arrow-down"}.get(cls, "ti-minus")
        return cls, icon, esc(txt)

    gmv_c, gmv_i, gmv_t = delta(d["gmv_delta"])
    ord_c, ord_i, ord_t = delta(d["ord_delta"])
    buy_c, buy_i, buy_t = delta(d["buyers_delta"])
    aov_c, aov_i, aov_t = delta(d["aov_delta"])

    # ---- order status doughnut ----
    status_labels = ["Paid online", "Pay at store"]
    status_data = [d["paid"], d["offline"]]
    status_colors = ["#C19A3E", "#D9BE84"]
    status_total = max(1, sum(status_data))
    status_legend = "".join(
        f"<span><span class='dot' style='background:{c};'></span>{lbl} "
        f"{round(100*v/status_total)}%</span>"
        for lbl, v, c in zip(status_labels, status_data, status_colors)
    )

    # ---- conversion funnel ----
    base = d["funnel"][0][1] or 1
    funnel_rows = ""
    for i, (label, val) in enumerate(d["funnel"]):
        w = max(2.0, 100 * val / base)
        pct = 100 * val / base
        color = _FUNNEL_COLORS[i % len(_FUNNEL_COLORS)]
        funnel_rows += (
            f"<div class='funnel-row'><div class='funnel-label'>{esc(label)}</div>"
            f"<div class='funnel-bar-track'><div class='funnel-bar' "
            f"style='width:{w:.1f}%; background:{color};'><span>{val:,}</span></div></div>"
            f"<div class='funnel-pct'>{pct:.1f}%</div></div>"
        )

    # ---- activity log rows ----
    log_rows = ""
    for created, email, action, details, ip, status, badge in d["logs"]:
        t = (created or "")[11:19] or (created or "")[:10]
        icon = _BADGE_ICON.get(badge, "ti-check")
        log_rows += (
            f"<tr><td class='time'>{esc(t)}</td>"
            f"<td class='primary'>{esc(str(email))}</td>"
            f"<td>{esc(action)}</td><td>{esc(details)}</td>"
            f"<td class='mono'>{esc(str(ip))}</td>"
            f"<td><span class='badge {badge}'><i class='ti {icon}' aria-hidden='true'></i> "
            f"{esc(status)}</span></td></tr>"
        )
    if not log_rows:
        log_rows = ("<tr><td colspan='6' style='text-align:center;color:var(--text-dim);"
                    "padding:28px;'>No activity recorded yet.</td></tr>")

    repl = {
        "__BRAND__": "Barakaly",
        "__MARK_SVG__": mark_svg,
        "__ADMIN_INITIALS__": _initials(user),
        "__ADMIN_NAME__": esc(user.get("display_name") or user.get("name") or "Administrator"),
        "__TICKER__": ticker_inner,
        "__GMV__": shared.money(d['gmv']),
        "__GMV_C__": gmv_c, "__GMV_I__": gmv_i, "__GMV_T__": gmv_t,
        "__ORDERS__": f"{d['n_orders']:,}",
        "__ORD_C__": ord_c, "__ORD_I__": ord_i, "__ORD_T__": ord_t,
        "__BUYERS__": f"{d['buyers']:,}",
        "__BUY_C__": buy_c, "__BUY_I__": buy_i, "__BUY_T__": buy_t,
        "__AOV__": shared.money(d['aov']),
        "__AOV_C__": aov_c, "__AOV_I__": aov_i, "__AOV_T__": aov_t,
        "__ABANDON__": f"{d['cart_abandon']:.1f}%",
        "__REPEAT__": f"{d['repeat_rate']:.1f}%",
        "__CLV__": shared.money(d['clv']),
        "__REVIEWS__": f"{d['reviews']:,}",
        "__AVG_RATING__": f"{d['avg_rating']:.1f}",
        "__STATUS_LEGEND__": status_legend,
        "__FUNNEL_ROWS__": funnel_rows,
        "__LOG_ROWS__": log_rows,
        "__LOG_COUNT__": f"{d['total_events']:,}",
        # ---- chart data (JSON) ----
        "__REV_LABELS__": json.dumps(d["rev_labels"]),
        "__REV_DATA__": json.dumps([round(x * shared.UZS_PER_USD) for x in d["rev_data"]]),
        "__STATUS_LABELS__": json.dumps(status_labels),
        "__STATUS_DATA__": json.dumps(status_data),
        "__STATUS_COLORS__": json.dumps(status_colors),
        "__TOP_LABELS__": json.dumps(d["top_labels"]),
        "__TOP_DATA__": json.dumps(d["top_data"]),
        "__ORDM_LABELS__": json.dumps(d["rev_labels"]),
        "__ORDM_DATA__": json.dumps(d["ord_by_month"]),
        "__CAT_LABELS__": json.dumps(d["cat_labels"]),
        "__CAT_DATA__": json.dumps(d["cat_data"]),
    }

    html = _TEMPLATE
    for k, v in repl.items():
        html = html.replace(k, str(v))
    return html


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__BRAND__ control room</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/tabler-icons/3.35.0/tabler-icons.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  :root{
    --bg:#FBF9F3; --surface:#FFFFFF; --surface-2:#FAF6EC; --border:#ECE7DA;
    --text:#1A1714; --text-muted:#6F675A; --text-dim:#9A9080;
    --accent:#C19A3E; --accent-soft:#F5EEDC; --accent-dim:#A07E2C;
    --teal:#A07E2C; --teal-soft:#F1E8D2;
    --success:#2F7D52; --success-soft:#E6F3EB; --danger:#B23A22; --danger-soft:#F7E7E2;
    --warning:#9A6B16; --warning-soft:#F6EDD8;
    --shadow:0 1px 3px rgba(26,23,20,.05), 0 8px 24px rgba(26,23,20,.04);
    --radius:14px;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  html,body{background:var(--bg);}
  body{font-family:'Inter', sans-serif; color:var(--text); display:flex; min-height:100vh;}
  h1,h2,h3{font-family:'Fraunces', Georgia, serif; font-weight:600; letter-spacing:-0.01em;}
  .mono{font-family:'Inter', sans-serif; font-variant-numeric:tabular-nums;}

  .sidebar{width:230px; background:var(--surface); border-right:1px solid var(--border);
    padding:24px 16px; display:flex; flex-direction:column; gap:4px; flex-shrink:0;}
  .brand{display:flex; align-items:center; gap:10px; padding:0 8px 26px;}
  .brand .mark{width:40px; height:40px; display:flex; align-items:center; justify-content:center; flex-shrink:0;}
  .brand .mark svg{width:40px; height:40px;}
  .brand .name{font-size:18px; font-weight:700; font-family:'Fraunces', serif;}
  .brand .sub{font-size:10.5px; color:var(--text-dim); letter-spacing:0.14em; font-weight:600;}
  .nav-section-label{font-size:10.5px; text-transform:uppercase; letter-spacing:0.12em; color:var(--text-dim);
    padding:18px 12px 6px; font-weight:600;}
  .nav-item{display:flex; align-items:center; gap:12px; padding:10px 12px; border-radius:10px;
    color:var(--text-muted); font-size:14px; font-weight:500; cursor:pointer; border:none;
    background:transparent; width:100%; text-align:left; transition:background 0.15s, color 0.15s;}
  .nav-item i{font-size:18px; width:18px; text-align:center;}
  .nav-item:hover{background:var(--surface-2); color:var(--text);}
  .nav-item.active{background:var(--accent-soft); color:var(--accent-dim);}
  .nav-item.active i{color:var(--accent);}
  .sidebar-footer{margin-top:auto; padding:14px 12px 4px; border-top:1px solid var(--border);
    display:flex; align-items:center; gap:10px;}
  .avatar{width:34px; height:34px; border-radius:50%; background:var(--accent-soft); color:var(--accent-dim);
    display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700;
    font-family:'Fraunces', serif;}
  .sidebar-footer .who{font-size:13px; font-weight:600;}
  .sidebar-footer .role{font-size:11px; color:var(--text-dim);}

  .main{flex:1; display:flex; flex-direction:column; min-width:0;}
  .ticker-wrap{background:var(--surface-2); border-bottom:1px solid var(--border);
    overflow:hidden; white-space:nowrap; padding:9px 0; position:relative;}
  /* fade the scrolling text out on the right so it never collides with the
     floating account avatar that sits over the top-right corner */
  .ticker-wrap::after{content:''; position:absolute; top:0; right:0; height:100%; width:96px;
    background:linear-gradient(90deg, rgba(250,246,236,0), var(--surface-2) 62%); pointer-events:none;}
  .ticker{display:inline-flex; gap:34px; animation:scroll 40s linear infinite;
    font-size:12px; color:var(--text-muted); padding-left:34px; font-variant-numeric:tabular-nums;}
  .ticker strong{color:var(--accent-dim);}
  .ticker-wrap:hover .ticker{animation-play-state:paused;}
  @keyframes scroll{from{transform:translateX(0);} to{transform:translateX(-50%);}}

  .topbar{display:flex; align-items:center; justify-content:space-between; padding:24px 32px 8px;}
  .topbar h1{font-size:26px;}
  .topbar .desc{font-size:13px; color:var(--text-muted); margin-top:4px;}
  .range-select{display:flex; gap:8px; align-items:center;}
  .pill-btn{font-size:12px; font-weight:600; color:var(--text-muted);
    background:var(--surface); border:1px solid var(--border); border-radius:999px; padding:7px 14px; cursor:pointer;}
  .pill-btn.active{color:var(--accent-dim); border-color:var(--accent); background:var(--accent-soft);}

  .page{padding:20px 32px 40px; display:none;}
  .page.active{display:block;}

  .metrics-grid{display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; margin-bottom:22px;}
  .metric-card{background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
    padding:18px 20px; box-shadow:var(--shadow);}
  .metric-card .label{font-size:12px; color:var(--text-muted); display:flex; align-items:center; gap:6px; margin-bottom:10px;}
  .metric-card .label i{font-size:15px; color:var(--accent);}
  .metric-card .value{font-family:'Fraunces', serif; font-size:30px; font-weight:600; color:var(--text);}
  .metric-card .delta{font-size:12px; margin-top:6px; display:flex; align-items:center; gap:4px; font-weight:500;}
  .delta.up{color:var(--success);} .delta.down{color:var(--danger);} .delta.flat{color:var(--text-dim);}

  .grid-2{display:grid; grid-template-columns:1.5fr 1fr; gap:14px; margin-bottom:22px;}
  .grid-3{display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-bottom:22px;}
  .panel{background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
    padding:20px 22px; box-shadow:var(--shadow);}
  .panel h3{font-size:16px; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between;}
  .panel h3 .tag{font-size:11px; color:var(--text-dim); font-weight:500; font-family:'Inter', sans-serif;}
  .legend{display:flex; flex-wrap:wrap; gap:14px; margin-top:12px; font-size:12px; color:var(--text-muted);}
  .legend span{display:flex; align-items:center; gap:6px;}
  .legend .dot{width:9px; height:9px; border-radius:3px; display:inline-block;}

  .funnel-row{display:flex; align-items:center; gap:14px; margin-bottom:12px;}
  .funnel-label{width:140px; font-size:13px; color:var(--text-muted);}
  .funnel-bar-track{flex:1; background:var(--surface-2); border-radius:8px; height:28px; overflow:hidden;}
  .funnel-bar{height:100%; border-radius:8px; display:flex; align-items:center; justify-content:flex-end; padding-right:10px;}
  .funnel-bar span{font-size:12px; font-weight:600; color:#FFF; font-variant-numeric:tabular-nums;}
  .funnel-pct{width:54px; text-align:right; font-size:12px; color:var(--text-muted); font-variant-numeric:tabular-nums;}

  .cohort-table{width:100%; border-collapse:collapse; font-size:13px;}
  .cohort-table th, .cohort-table td{padding:11px 12px; text-align:right; border-bottom:1px solid var(--border);}
  .cohort-table th{color:var(--text-dim); font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.05em;}
  .cohort-table td:first-child, .cohort-table th:first-child{text-align:left; color:var(--text-muted); font-weight:500;}
  .cohort-table td:last-child{font-family:'Fraunces', serif; font-weight:600; color:var(--text);}

  .logs-toolbar{display:flex; gap:10px; margin-bottom:18px; flex-wrap:wrap;}
  .logs-toolbar input, .logs-toolbar select{background:var(--surface); border:1px solid var(--border);
    color:var(--text); border-radius:10px; padding:9px 13px; font-size:13px; font-family:'Inter', sans-serif;}
  .logs-toolbar input{flex:1; min-width:180px;}
  .logs-toolbar input::placeholder{color:var(--text-dim);}
  table.logs{width:100%; border-collapse:collapse; font-size:13px;}
  table.logs th{text-align:left; padding:10px 14px; font-size:11px; text-transform:uppercase;
    letter-spacing:0.06em; color:var(--text-dim); font-weight:600; border-bottom:1px solid var(--border);}
  table.logs td{padding:13px 14px; border-bottom:1px solid var(--border); color:var(--text-muted);}
  table.logs td.primary{color:var(--text); font-weight:500;}
  table.logs tr:hover td{background:var(--surface-2);}
  table.logs td.time{font-size:12px; white-space:nowrap; font-variant-numeric:tabular-nums;}
  .badge{display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:600;
    padding:4px 10px; border-radius:999px; text-transform:uppercase; letter-spacing:0.04em;}
  .badge.success{color:var(--success); background:var(--success-soft);}
  .badge.warning{color:var(--warning); background:var(--warning-soft);}
  .badge.danger{color:var(--danger); background:var(--danger-soft);}
  .badge.info{color:var(--accent-dim); background:var(--accent-soft);}
  .pagination{display:flex; justify-content:space-between; align-items:center; margin-top:16px;
    font-size:12px; color:var(--text-dim);}

  @media (max-width: 1100px){.metrics-grid{grid-template-columns:repeat(2, 1fr);} .grid-2,.grid-3{grid-template-columns:1fr;}}
  @media (max-width: 720px){.sidebar{display:none;} .metrics-grid{grid-template-columns:1fr;}}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="brand">
    <div class="mark">__MARK_SVG__</div>
    <div>
      <div class="name">__BRAND__</div>
      <div class="sub">ADMIN CONSOLE</div>
    </div>
  </div>

  <div class="nav-section-label">Overview</div>
  <button class="nav-item active" data-page="dashboard"><i class="ti ti-layout-dashboard"></i> Dashboard</button>
  <button class="nav-item" data-page="analytics"><i class="ti ti-chart-bar"></i> Analytics</button>

  <div class="nav-section-label">Operations</div>
  <button class="nav-item" data-page="logs"><i class="ti ti-list-details"></i> Activity logs</button>

  <div class="sidebar-footer">
    <div class="avatar">__ADMIN_INITIALS__</div>
    <div>
      <div class="who">__ADMIN_NAME__</div>
      <div class="role">Marketplace ops</div>
    </div>
  </div>
</aside>

<div class="main">

  <div class="ticker-wrap"><div class="ticker">__TICKER__</div></div>

  <!-- ================= DASHBOARD ================= -->
  <div class="page active" id="page-dashboard">
    <div class="topbar">
      <div><h1>Dashboard</h1><div class="desc">Barakaly marketplace performance overview</div></div>
    </div>

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="label"><i class="ti ti-currency-dollar"></i> Gross merchandise value</div>
        <div class="value">__GMV__</div>
        <div class="delta __GMV_C__"><i class="ti __GMV_I__" aria-hidden="true"></i> __GMV_T__</div>
      </div>
      <div class="metric-card">
        <div class="label"><i class="ti ti-receipt"></i> Orders placed</div>
        <div class="value">__ORDERS__</div>
        <div class="delta __ORD_C__"><i class="ti __ORD_I__" aria-hidden="true"></i> __ORD_T__</div>
      </div>
      <div class="metric-card">
        <div class="label"><i class="ti ti-users"></i> Customers</div>
        <div class="value">__BUYERS__</div>
        <div class="delta __BUY_C__"><i class="ti __BUY_I__" aria-hidden="true"></i> __BUY_T__</div>
      </div>
      <div class="metric-card">
        <div class="label"><i class="ti ti-tag"></i> Average order value</div>
        <div class="value">__AOV__</div>
        <div class="delta __AOV_C__"><i class="ti __AOV_I__" aria-hidden="true"></i> __AOV_T__</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h3>Revenue trend <span class="tag">by month</span></h3>
        <div style="position:relative; height:240px;"><canvas id="revenueChart"></canvas></div>
      </div>
      <div class="panel">
        <h3>Order status <span class="tag">all orders</span></h3>
        <div style="position:relative; height:200px;"><canvas id="orderStatusChart"></canvas></div>
        <div class="legend">__STATUS_LEGEND__</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h3>Top selling products <span class="tag">units sold</span></h3>
        <div style="position:relative; height:240px;"><canvas id="topProductsChart"></canvas></div>
      </div>
      <div class="panel">
        <h3>Orders by month <span class="tag">count</span></h3>
        <div style="position:relative; height:240px;"><canvas id="ordersMonthChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- ================= ANALYTICS ================= -->
  <div class="page" id="page-analytics">
    <div class="topbar">
      <div><h1>Analytics</h1><div class="desc">Behavioural and operational metrics</div></div>
    </div>

    <div class="grid-3">
      <div class="metric-card">
        <div class="label"><i class="ti ti-shopping-cart-x"></i> Cart abandonment</div>
        <div class="value">__ABANDON__</div>
        <div class="delta flat"><i class="ti ti-minus" aria-hidden="true"></i> of items added to a cart</div>
      </div>
      <div class="metric-card">
        <div class="label"><i class="ti ti-repeat"></i> Repeat purchase rate</div>
        <div class="value">__REPEAT__</div>
        <div class="delta flat"><i class="ti ti-minus" aria-hidden="true"></i> buyers with 2+ orders</div>
      </div>
      <div class="metric-card">
        <div class="label"><i class="ti ti-heart-handshake"></i> Avg revenue / buyer</div>
        <div class="value">__CLV__</div>
        <div class="delta flat"><i class="ti ti-minus" aria-hidden="true"></i> lifetime to date</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h3>Conversion funnel <span class="tag">view → order</span></h3>
        __FUNNEL_ROWS__
      </div>
      <div class="panel">
        <h3>Platform snapshot <span class="tag">live data</span></h3>
        <table class="cohort-table">
          <tr><th>Metric</th><th>Value</th></tr>
          <tr><td>Reviews collected</td><td>__REVIEWS__</td></tr>
          <tr><td>Average rating</td><td>__AVG_RATING__ / 5</td></tr>
          <tr><td>Total customers</td><td>__BUYERS__</td></tr>
          <tr><td>Orders placed</td><td>__ORDERS__</td></tr>
        </table>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h3>Sales by category <span class="tag">share of GMV</span></h3>
        <div style="position:relative; height:240px;"><canvas id="categoryChart"></canvas></div>
      </div>
      <div class="panel">
        <h3>Revenue by month <span class="tag">$ collected</span></h3>
        <div style="position:relative; height:240px;"><canvas id="revenueChart2"></canvas></div>
      </div>
    </div>
  </div>

  <!-- ================= LOGS ================= -->
  <div class="page" id="page-logs">
    <div class="topbar">
      <div><h1>Activity logs</h1><div class="desc">Recent orders and sign-in events</div></div>
    </div>
    <div class="panel">
      <div class="logs-toolbar">
        <input type="text" placeholder="Search by user, email, or order ID...">
        <select><option>All actions</option><option>Sign-in</option><option>Purchase</option></select>
        <select><option>All statuses</option><option>Success</option><option>Failed</option></select>
      </div>
      <table class="logs">
        <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Details</th><th>IP address</th><th>Status</th></tr></thead>
        <tbody>__LOG_ROWS__</tbody>
      </table>
      <div class="pagination"><div>Showing latest events of __LOG_COUNT__ total</div></div>
    </div>
  </div>

</div>

<script>
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const target = btn.dataset.page;
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.getElementById('page-' + target).classList.add('active');
    });
  });

  const GRID = '#ECE7DA', MUT = '#9A9080';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.color = MUT;
  const somAxis = (v) => (v >= 1e6 ? (v/1e6).toFixed(1)+'M' : v >= 1e3 ? (v/1e3).toFixed(0)+'K' : ''+v) + " so'm";
  const somFull = (v) => v.toLocaleString().replace(/,/g, ' ') + " so'm";

  new Chart(document.getElementById('revenueChart'), {
    type: 'line',
    data: { labels: __REV_LABELS__, datasets: [{ label: 'Revenue', data: __REV_DATA__,
      borderColor: '#C19A3E', backgroundColor: 'rgba(193,154,62,0.10)', fill: true,
      tension: 0.35, pointRadius: 3, pointBackgroundColor: '#C19A3E' }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => somFull(ctx.parsed.y) } } },
      scales: { y: { ticks: { color: MUT, callback: somAxis }, grid: { color: GRID } },
                x: { ticks: { color: MUT }, grid: { display: false } } } }
  });

  new Chart(document.getElementById('orderStatusChart'), {
    type: 'doughnut',
    data: { labels: __STATUS_LABELS__, datasets: [{ data: __STATUS_DATA__,
      backgroundColor: __STATUS_COLORS__, borderWidth: 2, borderColor: '#FFFFFF' }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
  });

  new Chart(document.getElementById('topProductsChart'), {
    type: 'bar',
    data: { labels: __TOP_LABELS__, datasets: [{ label: 'Units sold', data: __TOP_DATA__,
      backgroundColor: '#C19A3E', borderRadius: 6 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: MUT }, grid: { color: GRID } },
                y: { ticks: { color: MUT }, grid: { display: false } } } }
  });

  new Chart(document.getElementById('ordersMonthChart'), {
    type: 'bar',
    data: { labels: __ORDM_LABELS__, datasets: [{ label: 'Orders', data: __ORDM_DATA__,
      backgroundColor: '#A07E2C', borderRadius: 6 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: MUT }, grid: { display: false } },
                y: { ticks: { color: MUT }, grid: { color: GRID } } } }
  });

  new Chart(document.getElementById('categoryChart'), {
    type: 'bar',
    data: { labels: __CAT_LABELS__, datasets: [{ label: 'Share of GMV', data: __CAT_DATA__,
      backgroundColor: '#C9A24E', borderRadius: 6 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ctx.parsed.x + '%' } } },
      scales: { x: { ticks: { color: MUT, callback: (v) => v + '%' }, grid: { color: GRID } },
                y: { ticks: { color: MUT }, grid: { display: false } } } }
  });

  new Chart(document.getElementById('revenueChart2'), {
    type: 'line',
    data: { labels: __REV_LABELS__, datasets: [{ label: 'Revenue', data: __REV_DATA__,
      borderColor: '#A07E2C', backgroundColor: 'rgba(160,126,44,0.10)', fill: true,
      tension: 0.35, pointRadius: 3, pointBackgroundColor: '#A07E2C' }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => somFull(ctx.parsed.y) } } },
      scales: { y: { ticks: { color: MUT, callback: somAxis }, grid: { color: GRID } },
                x: { ticks: { color: MUT }, grid: { display: false } } } }
  });
</script>
</body>
</html>
"""

"""Dark 'control-room' admin dashboard markup (adapted from the provided design
template). `render(d, user, _html, json)` returns a self-contained HTML document
— CSS + Chart.js + the marketplace's real data injected — to be dropped into an
iframe via st.components.v1.html. Kept separate from _analytics.py so the data
layer stays readable.
"""

from __future__ import annotations

_FUNNEL_COLORS = ["#85B7EB", "#5DCAA5", "#AFA9EC", "#FAC775", "#F0997B"]
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

    # ---- ticker (real metrics, no fabricated trend arrows) ----
    tick = [
        f"GMV TODAY <strong class='mono'>${d['gmv_today']:,.0f}</strong>",
        f"ORDERS TODAY <strong class='mono'>{d['orders_today']:,}</strong>",
        f"NEW SIGNUPS (30D) <strong class='mono'>{d['new_30']:,}</strong>",
        f"TOTAL GMV <strong class='mono'>${d['gmv']:,.0f}</strong>",
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
    status_colors = ["#1D9E75", "#FAC775"]
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
        "__MARK__": "B",
        "__ADMIN_INITIALS__": _initials(user),
        "__ADMIN_NAME__": esc(user.get("display_name") or user.get("name") or "Administrator"),
        "__TICKER__": ticker_inner,
        "__GMV__": f"${d['gmv']:,.0f}",
        "__GMV_C__": gmv_c, "__GMV_I__": gmv_i, "__GMV_T__": gmv_t,
        "__ORDERS__": f"{d['n_orders']:,}",
        "__ORD_C__": ord_c, "__ORD_I__": ord_i, "__ORD_T__": ord_t,
        "__BUYERS__": f"{d['buyers']:,}",
        "__BUY_C__": buy_c, "__BUY_I__": buy_i, "__BUY_T__": buy_t,
        "__AOV__": f"${d['aov']:,.2f}",
        "__AOV_C__": aov_c, "__AOV_I__": aov_i, "__AOV_T__": aov_t,
        "__ABANDON__": f"{d['cart_abandon']:.1f}%",
        "__REPEAT__": f"{d['repeat_rate']:.1f}%",
        "__CLV__": f"${d['clv']:,.0f}",
        "__REVIEWS__": f"{d['reviews']:,}",
        "__AVG_RATING__": f"{d['avg_rating']:.1f}",
        "__STATUS_LEGEND__": status_legend,
        "__FUNNEL_ROWS__": funnel_rows,
        "__LOG_ROWS__": log_rows,
        "__LOG_COUNT__": f"{d['total_events']:,}",
        # ---- chart data (JSON) ----
        "__REV_LABELS__": json.dumps(d["rev_labels"]),
        "__REV_DATA__": json.dumps(d["rev_data"]),
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
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/tabler-icons/3.35.0/tabler-icons.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  :root{
    --bg:#0E1318; --surface:#161D26; --surface-2:#1E2733; --border:#2A3543;
    --text:#E8ECF1; --text-muted:#8B98AA; --text-dim:#5C6B7E;
    --accent:#F5A623; --accent-dim:#5C4A24; --teal:#2DD4BF; --teal-dim:#1C4A45;
    --success:#4ADE80; --success-dim:#1F3B2C; --danger:#F87171; --danger-dim:#3F2424;
    --warning:#FBBF24; --warning-dim:#3F351A; --radius:10px;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  html,body{background:var(--bg);}
  body{font-family:'Inter', sans-serif; color:var(--text); display:flex; min-height:100vh;}
  h1,h2,h3{font-family:'Space Grotesk', sans-serif; font-weight:700; letter-spacing:-0.01em;}
  .mono{font-family:'JetBrains Mono', monospace;}

  .sidebar{width:220px; background:var(--surface); border-right:1px solid var(--border);
    padding:24px 16px; display:flex; flex-direction:column; gap:4px; flex-shrink:0;}
  .brand{display:flex; align-items:center; gap:10px; padding:0 8px 28px;}
  .brand .mark{width:34px; height:34px; background:var(--accent); color:#1A1303; border-radius:8px;
    display:flex; align-items:center; justify-content:center;
    font-family:'Space Grotesk', sans-serif; font-weight:700; font-size:16px;}
  .brand .name{font-size:16px; font-weight:700; font-family:'Space Grotesk', sans-serif;}
  .brand .sub{font-size:11px; color:var(--text-dim); font-family:'JetBrains Mono', monospace; letter-spacing:0.05em;}
  .nav-section-label{font-size:11px; text-transform:uppercase; letter-spacing:0.1em; color:var(--text-dim);
    padding:16px 12px 6px; font-family:'JetBrains Mono', monospace;}
  .nav-item{display:flex; align-items:center; gap:12px; padding:10px 12px; border-radius:8px;
    color:var(--text-muted); font-size:14px; font-weight:500; cursor:pointer; border:none;
    background:transparent; width:100%; text-align:left; transition:background 0.15s, color 0.15s;}
  .nav-item i{font-size:18px; width:18px; text-align:center;}
  .nav-item:hover{background:var(--surface-2); color:var(--text);}
  .nav-item.active{background:var(--surface-2); color:var(--accent);}
  .nav-item.active i{color:var(--accent);}
  .sidebar-footer{margin-top:auto; padding:12px; border-top:1px solid var(--border);
    display:flex; align-items:center; gap:10px;}
  .avatar{width:32px; height:32px; border-radius:50%; background:var(--teal-dim); color:var(--teal);
    display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:600;
    font-family:'Space Grotesk', sans-serif;}
  .sidebar-footer .who{font-size:13px; font-weight:500;}
  .sidebar-footer .role{font-size:11px; color:var(--text-dim);}

  .main{flex:1; display:flex; flex-direction:column; min-width:0;}
  .ticker-wrap{background:var(--surface-2); border-bottom:1px solid var(--border);
    overflow:hidden; white-space:nowrap; padding:8px 0;}
  .ticker{display:inline-flex; gap:32px; animation:scroll 38s linear infinite;
    font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--text-muted); padding-left:32px;}
  .ticker-wrap:hover .ticker{animation-play-state:paused;}
  @keyframes scroll{from{transform:translateX(0);} to{transform:translateX(-50%);}}

  .topbar{display:flex; align-items:center; justify-content:space-between; padding:20px 32px 8px;}
  .topbar h1{font-size:22px;}
  .topbar .desc{font-size:13px; color:var(--text-muted); margin-top:4px;}
  .range-select{display:flex; gap:8px; align-items:center;}
  .pill-btn{font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--text-muted);
    background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:6px 12px; cursor:pointer;}
  .pill-btn.active{color:var(--accent); border-color:var(--accent-dim); background:var(--accent-dim);}

  .page{padding:20px 32px 40px; display:none;}
  .page.active{display:block;}

  .metrics-grid{display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; margin-bottom:24px;}
  .metric-card{background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:16px 18px;}
  .metric-card .label{font-size:12px; color:var(--text-muted); display:flex; align-items:center; gap:6px; margin-bottom:10px;}
  .metric-card .label i{font-size:15px; color:var(--text-dim);}
  .metric-card .value{font-family:'Space Grotesk', sans-serif; font-size:26px; font-weight:700;}
  .metric-card .delta{font-family:'JetBrains Mono', monospace; font-size:12px; margin-top:6px;
    display:flex; align-items:center; gap:4px;}
  .delta.up{color:var(--success);} .delta.down{color:var(--danger);} .delta.flat{color:var(--text-dim);}

  .grid-2{display:grid; grid-template-columns:1.5fr 1fr; gap:14px; margin-bottom:24px;}
  .grid-3{display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-bottom:24px;}
  .panel{background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:18px 20px;}
  .panel h3{font-size:14px; margin-bottom:14px; display:flex; align-items:center; justify-content:space-between;}
  .panel h3 .tag{font-family:'JetBrains Mono', monospace; font-size:11px; color:var(--text-dim); font-weight:400;}
  .legend{display:flex; flex-wrap:wrap; gap:14px; margin-top:10px; font-size:12px; color:var(--text-muted);}
  .legend span{display:flex; align-items:center; gap:6px;}
  .legend .dot{width:9px; height:9px; border-radius:2px; display:inline-block;}

  .funnel-row{display:flex; align-items:center; gap:14px; margin-bottom:12px;}
  .funnel-label{width:130px; font-size:13px; color:var(--text-muted);}
  .funnel-bar-track{flex:1; background:var(--surface-2); border-radius:6px; height:26px; overflow:hidden;}
  .funnel-bar{height:100%; border-radius:6px; display:flex; align-items:center; justify-content:flex-end; padding-right:10px;}
  .funnel-bar span{font-family:'JetBrains Mono', monospace; font-size:12px; font-weight:500; color:#0E1318;}
  .funnel-pct{width:54px; text-align:right; font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--text-muted);}

  .cohort-table{width:100%; border-collapse:collapse; font-size:12px; font-family:'JetBrains Mono', monospace;}
  .cohort-table th, .cohort-table td{padding:8px 10px; text-align:center; border:1px solid var(--border);}
  .cohort-table th{color:var(--text-muted); font-weight:500; background:var(--surface-2);}
  .cohort-table td:first-child, .cohort-table th:first-child{text-align:left; color:var(--text-muted); font-weight:500;}

  .logs-toolbar{display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap;}
  .logs-toolbar input, .logs-toolbar select{background:var(--surface); border:1px solid var(--border);
    color:var(--text); border-radius:6px; padding:8px 12px; font-size:13px; font-family:'Inter', sans-serif;}
  .logs-toolbar input{flex:1; min-width:180px;}
  .logs-toolbar input::placeholder{color:var(--text-dim);}
  table.logs{width:100%; border-collapse:collapse; font-size:13px;}
  table.logs th{text-align:left; padding:10px 14px; font-size:11px; text-transform:uppercase;
    letter-spacing:0.06em; color:var(--text-dim); font-weight:600; border-bottom:1px solid var(--border);
    font-family:'JetBrains Mono', monospace;}
  table.logs td{padding:12px 14px; border-bottom:1px solid var(--border); color:var(--text-muted);}
  table.logs td.primary{color:var(--text); font-weight:500;}
  table.logs tr:hover td{background:var(--surface-2);}
  table.logs td.time{font-family:'JetBrains Mono', monospace; font-size:12px; white-space:nowrap;}
  .badge{display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:600;
    font-family:'JetBrains Mono', monospace; padding:3px 9px; border-radius:5px;
    text-transform:uppercase; letter-spacing:0.04em;}
  .badge.success{color:var(--success); background:var(--success-dim);}
  .badge.warning{color:var(--warning); background:var(--warning-dim);}
  .badge.danger{color:var(--danger); background:var(--danger-dim);}
  .badge.info{color:var(--teal); background:var(--teal-dim);}
  .pagination{display:flex; justify-content:space-between; align-items:center; margin-top:14px;
    font-size:12px; color:var(--text-dim); font-family:'JetBrains Mono', monospace;}

  @media (max-width: 1100px){.metrics-grid{grid-template-columns:repeat(2, 1fr);} .grid-2,.grid-3{grid-template-columns:1fr;}}
  @media (max-width: 720px){.sidebar{display:none;} .metrics-grid{grid-template-columns:1fr;}}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="brand">
    <div class="mark">__MARK__</div>
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
      <div class="range-select"><button class="pill-btn active">ALL TIME</button></div>
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
        <h3>Catalogue snapshot <span class="tag">platform</span></h3>
        <table class="cohort-table">
          <tr><th>Metric</th><th>Value</th></tr>
          <tr><td>Reviews collected</td><td>__REVIEWS__</td></tr>
          <tr><td>Average rating</td><td>__AVG_RATING__ / 5</td></tr>
          <tr><td>New signups (30 days)</td><td>__BUYERS__ total</td></tr>
          <tr><td>Orders placed</td><td>__ORDERS__</td></tr>
        </table>
        <div class="legend">
          <span><span class="dot" style="background:var(--teal);"></span>Figures reflect live platform data</span>
        </div>
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

  const GRID = '#2A3543', MUT = '#8B98AA';

  new Chart(document.getElementById('revenueChart'), {
    type: 'line',
    data: { labels: __REV_LABELS__, datasets: [{ label: 'Revenue', data: __REV_DATA__,
      borderColor: '#F5A623', backgroundColor: 'rgba(245,166,35,0.08)', fill: true,
      tension: 0.35, pointRadius: 3, pointBackgroundColor: '#F5A623' }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { y: { ticks: { color: MUT, callback: (v) => '$' + v.toLocaleString() }, grid: { color: GRID } },
                x: { ticks: { color: MUT }, grid: { display: false } } } }
  });

  new Chart(document.getElementById('orderStatusChart'), {
    type: 'doughnut',
    data: { labels: __STATUS_LABELS__, datasets: [{ data: __STATUS_DATA__,
      backgroundColor: __STATUS_COLORS__, borderWidth: 0 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
  });

  new Chart(document.getElementById('topProductsChart'), {
    type: 'bar',
    data: { labels: __TOP_LABELS__, datasets: [{ label: 'Units sold', data: __TOP_DATA__,
      backgroundColor: '#7F77DD', borderRadius: 4 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: MUT }, grid: { color: GRID } },
                y: { ticks: { color: MUT }, grid: { display: false } } } }
  });

  new Chart(document.getElementById('ordersMonthChart'), {
    type: 'bar',
    data: { labels: __ORDM_LABELS__, datasets: [{ label: 'Orders', data: __ORDM_DATA__,
      backgroundColor: '#5DCAA5', borderRadius: 4 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: MUT }, grid: { display: false } },
                y: { ticks: { color: MUT }, grid: { color: GRID } } } }
  });

  new Chart(document.getElementById('categoryChart'), {
    type: 'bar',
    data: { labels: __CAT_LABELS__, datasets: [{ label: 'Share of GMV', data: __CAT_DATA__,
      backgroundColor: '#2DD4BF', borderRadius: 4 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ctx.parsed.x + '%' } } },
      scales: { x: { ticks: { color: MUT, callback: (v) => v + '%' }, grid: { color: GRID } },
                y: { ticks: { color: MUT }, grid: { display: false } } } }
  });

  new Chart(document.getElementById('revenueChart2'), {
    type: 'line',
    data: { labels: __REV_LABELS__, datasets: [{ label: 'Revenue', data: __REV_DATA__,
      borderColor: '#2DD4BF', backgroundColor: 'rgba(45,212,191,0.08)', fill: true,
      tension: 0.35, pointRadius: 3, pointBackgroundColor: '#2DD4BF' }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { y: { ticks: { color: MUT, callback: (v) => '$' + v.toLocaleString() }, grid: { color: GRID } },
                x: { ticks: { color: MUT }, grid: { display: false } } } }
  });
</script>
</body>
</html>
"""

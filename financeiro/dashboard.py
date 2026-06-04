#!/usr/bin/env python3
"""
Dashboard PowerMind — gera dashboard.html dinâmico.
O HTML gerado busca dados de http://localhost:8080/api/data automaticamente a cada 60s.
Uso: python3 financeiro/dashboard.py  (só precisa rodar UMA vez para gerar o arquivo)
"""
import json, os
from datetime import datetime

OUT_FILE = os.path.join(os.path.dirname(__file__), "dashboard.html")

PREC_KITS = [
    {"id": "k1", "nome": "1 Pacote",              "preco": 157.00, "cmv": 37.00,  "mixer":  0.00, "frete": 20.00, "imposto": 10.0, "gateway": 4.99, "yampi": 2.5},
    {"id": "k2", "nome": "2 Pacotes (Power Duo)", "preco": 274.00, "cmv": 74.00,  "mixer": 12.00, "frete": 20.00, "imposto": 10.0, "gateway": 4.99, "yampi": 2.5},
    {"id": "k3", "nome": "3 Pacotes",             "preco": 381.00, "cmv": 111.00, "mixer": 12.00, "frete": 20.00, "imposto": 10.0, "gateway": 4.99, "yampi": 2.5},
]

prec_cards_html = ""
for k in PREC_KITS:
    prec_cards_html += f"""
    <div class="prec-card">
      <div class="prec-header">{k["nome"]} — <span id="{k["id"]}_preco_label">R${k["preco"]:.2f}</span></div>
      <div class="prec-row"><span class="prec-label">Preço de venda</span>
        <div><input type="number" id="{k["id"]}_preco" value="{k["preco"]:.2f}" step="1" onchange="calc()"> <span class="prec-pct"></span></div></div>
      <div class="prec-row"><span class="prec-label">CMV produto</span>
        <div><input type="number" id="{k["id"]}_cmv" value="{k["cmv"]:.2f}" step="0.5" onchange="calc()"> <span class="prec-pct" id="{k["id"]}_cmv_pct"></span></div></div>
      <div class="prec-row"><span class="prec-label">Brinde / Mixer</span>
        <div><input type="number" id="{k["id"]}_mixer" value="{k["mixer"]:.2f}" step="0.5" onchange="calc()"> <span class="prec-pct" id="{k["id"]}_mixer_pct"></span></div></div>
      <div class="prec-row"><span class="prec-label">Frete médio</span>
        <div><input type="number" id="{k["id"]}_frete" value="{k["frete"]:.2f}" step="1" onchange="calc()"> <span class="prec-pct" id="{k["id"]}_frete_pct"></span></div></div>
      <div class="prec-row"><span class="prec-label">Imposto (%)</span>
        <div><input type="number" id="{k["id"]}_imposto" value="{k["imposto"]:.1f}" step="0.5" onchange="calc()"> <span class="prec-pct">% receita</span></div></div>
      <div class="prec-row"><span class="prec-label">Gateway / Appmax (%)</span>
        <div><input type="number" id="{k["id"]}_gateway" value="{k["gateway"]:.2f}" step="0.1" onchange="calc()"> <span class="prec-pct">% receita</span></div></div>
      <div class="prec-row"><span class="prec-label">Yampi (%)</span>
        <div><input type="number" id="{k["id"]}_yampi" value="{k["yampi"]:.1f}" step="0.1" onchange="calc()"> <span class="prec-pct">% receita</span></div></div>
      <div class="prec-total">
        <div class="t-row"><span class="t-label">Total custos variáveis</span><span class="t-val neg" id="{k["id"]}_var_total">—</span></div>
        <div class="t-row"><span class="t-label">% do preço</span><span class="t-val" id="{k["id"]}_var_pct" style="color:#e67e22">—</span></div>
        <div class="t-row" style="margin-top:6px"><span class="t-label">Margem contribuição</span><span class="t-val pos" id="{k["id"]}_mc">—</span></div>
        <div class="t-row"><span class="t-label">% do preço</span><span class="t-val pos" id="{k["id"]}_mc_pct">—</span></div>
        <div class="t-row"><span class="t-label">ROAS ideal (13% lucro)</span><span class="t-val" id="{k["id"]}_roas13" style="color:#6c63ff">—</span></div>
        <div class="t-row"><span class="t-label">CPA alvo (13% lucro)</span><span class="t-val" id="{k["id"]}_cpa13" style="color:#3498db">—</span></div>
      </div>
    </div>"""

kit_ids = json.dumps([k["id"] for k in PREC_KITS])

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard PowerMind</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#0f1117;color:#e0e0e0;min-height:100vh}}
  .header{{background:linear-gradient(135deg,#1a1d2e,#252836);padding:24px 32px;border-bottom:1px solid #2d3047;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100}}
  .header h1{{font-size:1.6rem;font-weight:700;color:#fff}}
  .header h1 span{{color:#6c63ff}}
  .logo-img{{height:36px;width:auto;display:block}}
  .header .ts{{font-size:.82rem;color:#888;margin-top:4px}}
  .live-bar{{display:flex;align-items:center;gap:12px}}
  .dot{{width:8px;height:8px;border-radius:50%;background:#27ae60;animation:pulse 2s infinite}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
  .container{{padding:24px 32px;max-width:1600px;margin:0 auto}}
  .section-title{{font-size:1rem;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:1px;margin:28px 0 14px;border-bottom:1px solid #2d3047;padding-bottom:8px}}
  .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:8px}}
  .kpi{{background:#1a1d2e;border:1px solid #2d3047;border-radius:12px;padding:20px;position:relative;overflow:hidden}}
  .kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--accent,#6c63ff)}}
  .kpi .label{{font-size:.78rem;color:#888;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px}}
  .kpi .value{{font-size:1.7rem;font-weight:700;color:#fff}}
  .kpi .sub{{font-size:.78rem;color:#888;margin-top:4px}}
  .kpi.green{{--accent:#27ae60}}.kpi.red{{--accent:#e74c3c}}.kpi.blue{{--accent:#3498db}}
  .kpi.purple{{--accent:#9b59b6}}.kpi.orange{{--accent:#e67e22}}.kpi.teal{{--accent:#1abc9c}}
  .charts-grid{{display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-bottom:8px}}
  .chart-box{{background:#1a1d2e;border:1px solid #2d3047;border-radius:12px;padding:20px}}
  .chart-box h3{{font-size:.9rem;color:#aaa;margin-bottom:16px;text-transform:uppercase;letter-spacing:.5px}}
  table{{width:100%;border-collapse:collapse;font-size:.85rem}}
  th{{background:#252836;color:#aaa;text-align:left;padding:10px 12px;font-size:.75rem;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #2d3047}}
  td{{padding:10px 12px;border-bottom:1px solid #1e2130;vertical-align:middle}}
  tr:hover td{{background:#1e2130}}
  .table-box{{background:#1a1d2e;border:1px solid #2d3047;border-radius:12px;overflow:hidden;margin-bottom:20px}}
  .badge{{padding:3px 8px;border-radius:4px;font-size:.7rem;font-weight:700;margin-right:6px}}
  .badge.active{{background:#1a4731;color:#27ae60}}.badge.paused{{background:#3d2b1f;color:#e67e22}}
  .two-col{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
  .periodo-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:8px}}
  .periodo-block{{background:#1a1d2e;border:1px solid #2d3047;border-radius:12px;padding:16px}}
  .periodo-block .periodo-header{{font-size:.8rem;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid #2d3047}}
  .periodo-block .p-row{{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #1e2130}}
  .periodo-block .p-row:last-child{{border-bottom:none}}
  .periodo-block .p-label{{font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.4px}}
  .periodo-block .p-val{{font-size:1rem;font-weight:700;color:#fff}}
  .pos{{color:#27ae60!important}}.neg{{color:#e74c3c!important}}
  .prec-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:24px}}
  .prec-card{{background:#1a1d2e;border:1px solid #2d3047;border-radius:12px;overflow:hidden}}
  .prec-card .prec-header{{background:#252836;padding:14px 18px;font-size:.9rem;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:.5px}}
  .prec-row{{display:flex;justify-content:space-between;align-items:center;padding:10px 18px;border-bottom:1px solid #1e2130}}
  .prec-row:last-child{{border-bottom:none}}
  .prec-row .prec-label{{font-size:.78rem;color:#888;text-transform:uppercase;letter-spacing:.4px}}
  .prec-row input{{background:#0f1117;border:1px solid #3d4060;border-radius:6px;color:#fff;font-size:.9rem;font-weight:600;width:100px;padding:4px 8px;text-align:right}}
  .prec-row input:focus{{outline:none;border-color:#6c63ff}}
  .prec-row .prec-pct{{font-size:.75rem;color:#555;margin-left:6px;min-width:40px}}
  .prec-total{{background:#252836;padding:14px 18px;border-top:2px solid #3d4060}}
  .prec-total .t-row{{display:flex;justify-content:space-between;align-items:center;padding:4px 0}}
  .prec-total .t-label{{font-size:.78rem;color:#aaa;text-transform:uppercase}}
  .prec-total .t-val{{font-size:1rem;font-weight:700}}
  .prec-total .t-val.pos{{color:#27ae60}}.prec-total .t-val.neg{{color:#e74c3c}}
  .roas-box{{background:#1a1d2e;border:1px solid #2d3047;border-radius:12px;padding:20px;margin-bottom:24px}}
  .roas-box h3{{font-size:.85rem;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #2d3047}}
  .roas-table{{width:100%;border-collapse:collapse;font-size:.85rem}}
  .roas-table th{{background:#252836;color:#aaa;padding:8px 12px;text-align:center;font-size:.75rem;text-transform:uppercase}}
  .roas-table td{{padding:8px 12px;text-align:center;border-bottom:1px solid #1e2130;font-weight:600}}
  .roas-table td:first-child{{text-align:left;color:#888}}
  .fixos-card{{background:#1a1d2e;border:1px solid #2d3047;border-radius:12px;overflow:hidden;margin-bottom:24px}}
  .fixos-card .prec-header{{background:#252836;padding:14px 18px;font-size:.9rem;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:.5px}}
  .loading{{text-align:center;color:#555;padding:24px;font-size:.9rem}}
  @media(max-width:900px){{.charts-grid,.two-col,.periodo-grid,.prec-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<div class="header">
  <div>
    <img src="/logo.png?v=1779617456" alt="PowerMind" class="logo-img">
    <div class="ts" id="ts">Conectando ao servidor...</div>
  </div>
  <div class="live-bar">
    <div class="dot"></div>
    <span style="color:#aaa;font-size:.82rem">Ao vivo · atualiza em <span id="countdown">60</span>s</span>
    <div id="status-hoje" style="text-align:right;margin-left:16px"></div>
  </div>
</div>

<div class="container">

  <div class="section-title">Hoje — <span id="hoje-label">...</span></div>
  <div class="kpi-grid" id="kpi-hoje"><div class="loading">Carregando...</div></div>

  <div class="section-title" id="periodo-title">Histórico — Ontem · Última Semana · Últimos 30 dias</div>
  <div class="periodo-grid" id="periodo-grid"><div class="loading">Carregando...</div></div>

  <div class="section-title" id="acum-title">Acumulado Quinzenal</div>
  <div class="kpi-grid" id="kpi-acum"><div class="loading">Carregando...</div></div>

  <div class="section-title">Evolução diária</div>
  <div class="charts-grid">
    <div class="chart-box"><h3>Receita vs Gasto Ads (R$)</h3><canvas id="chartBar" height="110"></canvas></div>
    <div class="chart-box"><h3>Resultado líquido diário (R$)</h3><canvas id="chartResult" height="110"></canvas></div>
  </div>

  <div class="section-title">Campanhas Meta Ads — Ativas</div>
  <div class="table-box">
    <table><thead><tr>
      <th>Campanha</th><th>Gasto</th><th>Impressões</th><th>Cliques</th>
      <th>CTR</th><th>CPM</th><th>Compras</th><th>CPA</th>
    </tr></thead><tbody id="camp-body"><tr><td colspan="8" class="loading">Carregando...</td></tr></tbody></table>
  </div>

  <div class="section-title">DRE — Resumo por Período</div>
  <div class="table-box">
    <table><thead><tr>
      <th>Período</th><th>Pedidos</th><th>Receita</th><th>Margem</th>
      <th>Ads</th><th>Fixos</th><th>Resultado</th><th>ROAS</th>
    </tr></thead><tbody id="dre-body"><tr><td colspan="8" class="loading">Carregando...</td></tr></tbody></table>
  </div>

  <div class="section-title">Lançamentos</div>
  <div class="table-box" style="padding:20px 20px 10px">
    <!-- Linha 1: Quem lança + Data (destaque) -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
      <div style="background:#252836;border:2px solid #6c63ff;border-radius:8px;padding:12px 16px;display:flex;align-items:center;gap:14px">
        <span style="font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.5px;white-space:nowrap">Quem está lançando?</span>
        <div style="display:flex;gap:8px;flex:1">
          <button type="button" id="btn-caio" onclick="selecionarPor('Caio')" style="flex:1;padding:7px;border-radius:6px;border:2px solid #6c63ff;background:#6c63ff;color:#fff;font-weight:700;cursor:pointer;font-size:.9rem">Caio</button>
          <button type="button" id="btn-felipe" onclick="selecionarPor('Felipe')" style="flex:1;padding:7px;border-radius:6px;border:2px solid #3d4060;background:transparent;color:#aaa;font-weight:600;cursor:pointer;font-size:.9rem">Felipe</button>
        </div>
      </div>
      <div style="background:#252836;border:2px solid #3d4060;border-radius:8px;padding:12px 16px;display:flex;align-items:center;gap:14px">
        <span style="font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.5px;white-space:nowrap">Data do lançamento</span>
        <input type="date" id="l-data" style="flex:1;background:transparent;border:none;color:#e0e0e0;font-size:1rem;font-weight:600;outline:none">
      </div>
    </div>
    <!-- Linha 2: demais campos -->
    <form id="lanc-form" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:18px">
      <input type="hidden" id="l-por" value="Caio">
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Categoria</label>
        <select id="l-cat" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
          <option>Tráfego Pago</option>
          <option>Logística</option>
          <option>Despesas Operacionais</option>
          <option>Marketing (Conteúdo)</option>
          <option>Produto</option>
          <option>Eventos</option>
          <option>Ferramenta</option>
        </select>
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Descrição</label>
        <input type="text" id="l-desc" placeholder="Ex: Compra de embalagens" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Valor (R$)</label>
        <input type="number" id="l-valor" step="0.01" min="0" placeholder="0,00" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
      </div>
      <div>
        <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Tipo</label>
        <select id="l-tipo" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
          <option value="Despesa">Despesa</option><option value="Entrada">Entrada</option><option value="Receita">Receita</option>
        </select>
      </div>
      <div style="display:flex;align-items:flex-end">
        <button type="submit" id="lanc-btn" style="width:100%;background:#6c63ff;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:.85rem;font-weight:600;cursor:pointer">+ Lançar</button>
      </div>
    </form>
    <table><thead><tr>
      <th>Data</th><th>Por</th><th>Categoria</th><th>Descrição</th><th>Tipo</th><th>Valor</th><th>Lançado em</th><th></th>
    </tr></thead><tbody id="lanc-body"><tr><td colspan="8" class="loading">Carregando...</td></tr></tbody>
    <tfoot id="lanc-foot"></tfoot></table>

  <!-- Modal exclusão -->
  <div id="modal-excluir" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:9999;align-items:center;justify-content:center">
    <div style="background:#1e2030;border:1px solid #3d4060;border-radius:12px;padding:28px 32px;max-width:420px;width:90%">
      <div style="font-size:1.1rem;font-weight:700;margin-bottom:6px">🗑️ Excluir lançamento</div>
      <div id="modal-desc" style="color:#aaa;font-size:.88rem;margin-bottom:18px"></div>
      <div style="margin-bottom:16px">
        <label style="font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.5px;display:block;margin-bottom:6px">Quem está excluindo?</label>
        <select id="modal-por" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:8px 10px;font-size:.9rem">
          <option>Caio</option><option>Felipe</option>
        </select>
      </div>
      <div style="display:flex;gap:10px;justify-content:flex-end">
        <button onclick="fecharModal()" style="background:#2a2d3e;color:#ccc;border:1px solid #3d4060;border-radius:6px;padding:8px 18px;cursor:pointer">Cancelar</button>
        <button onclick="confirmarExclusao()" style="background:#ef4444;color:#fff;border:none;border-radius:6px;padding:8px 18px;font-weight:600;cursor:pointer">Excluir</button>
      </div>
    </div>
  </div>
  </div>

  <div class="section-title">Estrutura de Custos</div>
  <div class="two-col">
    <div class="table-box" style="padding:20px 20px 10px">
      <form id="fixos-form" style="display:grid;grid-template-columns:1fr 200px 160px 140px 110px;gap:10px;margin-bottom:18px;align-items:end">
        <div>
          <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Nome do custo</label>
          <input type="text" id="f-nome" placeholder="Ex: Contador, Embalagens..." style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
        </div>
        <div>
          <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Categoria DRE</label>
          <select id="f-cat" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
            <option>Pessoal</option>
            <option>Infraestrutura</option>
            <option>Plataforma</option>
            <option>Marketing</option>
            <option>Logística</option>
            <option>Administrativo</option>
            <option>Tecnologia</option>
            <option>Outros</option>
          </select>
        </div>
        <div>
          <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Valor mensal (R$)</label>
          <input type="number" id="f-valor" step="0.01" min="0" placeholder="0,00" style="width:100%;background:#252836;border:1px solid #3d4060;border-radius:6px;color:#e0e0e0;padding:7px 10px;font-size:.85rem">
        </div>
        <div>
          <label style="font-size:.72rem;color:#888;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Rateio</label>
          <div id="f-rateio" style="color:#aaa;font-size:.85rem;padding:8px 10px;background:#1a1d2e;border-radius:6px;border:1px solid #2d3047">—/dia</div>
        </div>
        <div style="display:flex;align-items:flex-end">
          <button type="submit" id="fixos-btn" style="width:100%;background:#27ae60;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:.85rem;font-weight:600;cursor:pointer">+ Adicionar</button>
        </div>
      </form>
      <table>
        <thead><tr>
          <th>Item</th>
          <th>Categoria DRE</th>
          <th>Valor/mês</th>
          <th>Rateio diário</th>
          <th style="width:60px"></th>
        </tr></thead>
        <tbody id="fixos-body"></tbody>
      </table>
    </div>
    <div class="table-box">
      <table>
        <thead><tr><th>Kit</th><th>Preço</th><th>CMV+Mixer</th><th>Margem contrib.</th><th>%</th></tr></thead>
        <tbody id="kits-resumo-body"></tbody>
      </table>
    </div>
  </div>

  <div class="section-title" style="margin-top:28px">Custo por Kit — editável em tempo real</div>
  <p style="color:#888;font-size:.82rem;margin-bottom:20px">Altere qualquer valor. A margem e o ROAS ideal são recalculados automaticamente.</p>
  <div class="prec-grid" id="prec-grid">
    {prec_cards_html}
  </div>

  <div class="fixos-card">
    <div class="prec-header">Fixos — editável</div>
    <div id="fixos-prec-rows"></div>
    <div class="prec-total">
      <div class="t-row"><span class="t-label">Total fixos/mês</span><span class="t-val" id="fixos_mes" style="color:#e67e22">—</span></div>
      <div class="t-row"><span class="t-label">Rateio diário</span><span class="t-val" id="fixos_dia" style="color:#888">—</span></div>
    </div>
  </div>

  <div class="section-title">ROAS Ideal por Kit e Meta de Lucro</div>
  <div class="roas-box">
    <h3>Pedidos por dia: <select id="peds_dia" onchange="calc()" style="background:#0f1117;color:#fff;border:1px solid #3d4060;border-radius:4px;padding:3px 8px">
      <option value="1">1 pedido/dia</option>
      <option value="2">2 pedidos/dia</option>
      <option value="3" selected>3 pedidos/dia</option>
      <option value="5">5 pedidos/dia</option>
      <option value="7">7 pedidos/dia</option>
    </select></h3>
    <table class="roas-table" style="margin-top:12px">
      <thead><tr>
        <th style="text-align:left">Kit</th>
        <th>Meta 10%</th><th>Meta 13%</th><th>Meta 15%</th><th>CPA máx. (13%)</th>
      </tr></thead>
      <tbody id="roas-tbody"></tbody>
    </table>
  </div>

</div>

<script>
const API = '/api/data';
const KIT_IDS = {kit_ids};
const BRL = v => 'R$ ' + Number(v).toLocaleString('pt-BR',{{minimumFractionDigits:2,maximumFractionDigits:2}});
const PCT = v => Number(v).toFixed(1) + '%';
const fmt = BRL;
const pct = v => PCT(v);

let chartBar = null, chartResult = null;
let _fixedCostsFromAPI = {{}};

// ── Helpers ───────────────────────────────────────────────────────────────
const DIAS_PT = ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'];
function dow(dateStr) {{
  // dateStr = 'YYYY-MM-DD' — adiciona T12:00 para evitar drift de fuso
  const d = new Date(dateStr + 'T12:00:00');
  return DIAS_PT[d.getDay()];
}}
function fmtData(dateStr) {{
  // Retorna "Sex 23/05" a partir de "2026-05-23"
  if(!dateStr || dateStr.length < 10) return dateStr||'—';
  return dow(dateStr) + ' ' + dateStr.slice(8,10) + '/' + dateStr.slice(5,7);
}}
function sumPeriod(hist, field) {{ return hist.reduce((a,r) => a + (r[field]||0), 0); }}
function periodoBlock(title, recs) {{
  const res  = sumPeriod(recs,'resultado');
  const rec  = sumPeriod(recs,'receita_bruta');
  const ads  = sumPeriod(recs,'gasto_ads');
  const roas = ads > 0 ? rec/ads : 0;
  const ped  = sumPeriod(recs,'pedidos');
  const rc   = res >= 0 ? 'pos' : 'neg';
  const rrc  = roas >= 3.5 ? 'pos' : 'neg';
  return `<div class="periodo-block">
    <div class="periodo-header">${{title}}</div>
    <div class="p-row"><span class="p-label">Resultado</span><span class="p-val ${{rc}}">${{BRL(res)}}</span></div>
    <div class="p-row"><span class="p-label">Receita bruta</span><span class="p-val">${{BRL(rec)}}</span></div>
    <div class="p-row"><span class="p-label">Gasto Ads</span><span class="p-val">${{BRL(ads)}}</span></div>
    <div class="p-row"><span class="p-label">ROAS</span><span class="p-val ${{rrc}}">${{roas.toFixed(2)}}x</span></div>
    <div class="p-row"><span class="p-label">Pedidos</span><span class="p-val">${{ped}}</span></div>
  </div>`;
}}

function kpiCard(label, value, sub, cls) {{
  return `<div class="kpi ${{cls}}"><div class="label">${{label}}</div><div class="value">${{value}}</div><div class="sub">${{sub}}</div></div>`;
}}

// ── Render ────────────────────────────────────────────────────────────────
function render(d) {{
  const today = d.today;
  const now   = d.updated_at;

  // Header
  document.getElementById('ts').textContent = 'Ao vivo · ' + now;
  document.getElementById('hoje-label').textContent = today;
  const rh = d.hoje.resultado;
  document.getElementById('status-hoje').innerHTML =
    `<div style="font-size:.8rem;color:#aaa">Resultado hoje</div>
     <div style="font-size:1.3rem;font-weight:700;color:${{rh>=0?'#27ae60':'#e74c3c'}}">${{rh>=0?'🟢 POSITIVO':'🔴 NEGATIVO'}}</div>`;

  // KPIs hoje
  const h = d.hoje;
  document.getElementById('kpi-hoje').innerHTML =
    kpiCard('Resultado do dia', BRL(h.resultado), h.pedidos+' pedido(s)', h.resultado>=0?'green':'red') +
    kpiCard('Receita', BRL(h.receita), 'Bruta', 'blue') +
    kpiCard('Gasto Ads', BRL(h.ads), 'Meta Ads', 'orange') +
    kpiCard('ROAS', h.roas.toFixed(2)+'x', 'Meta: >3,5x', h.roas>=3.5?'green':'red') +
    kpiCard('Impressões', h.impressions.toLocaleString('pt-BR'), 'Meta Ads hoje', 'teal') +
    kpiCard('CTR', PCT(h.ctr), 'Meta: >2%', h.ctr>=2?'green':'red') +
    kpiCard('CPM', BRL(h.cpm), 'Meta: <R$55', h.cpm>0&&h.cpm<55?'green':'red');

  // Períodos — calcula a partir do histórico completo
  const hist = d.history_all || d.history || [];
  const todayD = new Date(today);
  const ystStr = new Date(todayD - 86400000).toISOString().slice(0,10);
  const w7Str  = new Date(todayD - 7*86400000).toISOString().slice(0,10);
  const d30Str = new Date(todayD - 30*86400000).toISOString().slice(0,10);

  const recOntem  = hist.filter(r => r.data === ystStr);
  const recSemana = hist.filter(r => r.data >= w7Str && r.data <= ystStr);
  const rec30d    = hist.filter(r => r.data >= d30Str && r.data <= ystStr);

  document.getElementById('periodo-title').textContent = `Histórico — Ontem · Última Semana · Últimos 30 dias`;
  document.getElementById('periodo-grid').innerHTML =
    periodoBlock(`Ontem — ${{fmtData(ystStr)}}`, recOntem) +
    periodoBlock(`Última Semana — ${{recSemana.length}} dias`, recSemana) +
    periodoBlock(`Últimos 30 dias (${{rec30d.length}} dias com dados)`, rec30d);

  // Acumulado quinzenal
  const q15Str = new Date(todayD - 14*86400000).toISOString().slice(0,10);
  const recQ   = hist.filter(r => r.data >= q15Str);
  const qRec   = sumPeriod(recQ,'receita_bruta');
  const qAds   = sumPeriod(recQ,'gasto_ads');
  const qMar   = sumPeriod(recQ,'margem_contribuicao');
  const qRes   = sumPeriod(recQ,'resultado');
  const qPed   = sumPeriod(recQ,'pedidos');
  const qFixos = d.fixed_total || 0;
  document.getElementById('acum-title').textContent = `Acumulado Quinzenal — ${{q15Str}} a ${{today}}`;
  document.getElementById('kpi-acum').innerHTML =
    kpiCard('Resultado total', BRL(qRes), 'Lucro/Prejuízo', qRes>=0?'green':'red') +
    kpiCard('Receita total', BRL(qRec), qPed+' pedidos', 'blue') +
    kpiCard('Margem contrib.', PCT(qRec>0?qMar/qRec*100:0), BRL(qMar)+' total', 'green') +
    kpiCard('Total ads', BRL(qAds), 'ROAS: '+(qAds>0?qRec/qAds:0).toFixed(2)+'x', 'orange') +
    kpiCard('Ticket médio', BRL(qPed>0?qRec/qPed:0), 'Por pedido', 'purple') +
    kpiCard('Fixos/mês', BRL(qFixos), BRL(qFixos/30)+'/dia', 'red');

  // Gráficos
  const chartHist = d.history || [];
  // Labels 2 linhas compactas: ["Sx", "01"] — dia 2 letras + número do dia
  const DOW2 = ['Do','Se','Te','Qa','Qi','Sx','Sb'];
  function dow2(ds) {{ return DOW2[new Date(ds+'T12:00:00').getDay()]; }}
  const labels  = chartHist.map(r => [dow2(r.data), r.data.slice(8,10)]);
  const recArr  = chartHist.map(r => r.receita_bruta||0);
  const adsArr  = chartHist.map(r => r.gasto_ads||0);
  const resArr  = chartHist.map(r => r.resultado||0);

  const xTicks = {{
    color:'#666',
    font:{{size:9}},
    autoSkip:false,
    maxRotation:0,
    minRotation:0
  }};
  const yTicks = {{ color:'#666', font:{{size:9}} }};
  const gridCfg = {{ color:'#1e2130' }};

  if(chartBar) chartBar.destroy();
  chartBar = new Chart(document.getElementById('chartBar'), {{
    type:'bar', data:{{labels, datasets:[
      {{label:'Receita',data:recArr,backgroundColor:'rgba(52,152,219,0.7)',borderRadius:3}},
      {{label:'Gasto Ads',data:adsArr,backgroundColor:'rgba(231,76,60,0.7)',borderRadius:3}}
    ]}},
    options:{{
      responsive:true,
      plugins:{{legend:{{labels:{{color:'#aaa',font:{{size:11}}}}}}}},
      scales:{{x:{{ticks:xTicks,grid:gridCfg}},y:{{ticks:yTicks,grid:gridCfg}}}}
    }}
  }});
  if(chartResult) chartResult.destroy();
  chartResult = new Chart(document.getElementById('chartResult'), {{
    type:'bar', data:{{labels, datasets:[{{
      label:'Resultado', data:resArr,
      backgroundColor:resArr.map(v=>v>=0?'rgba(39,174,96,0.8)':'rgba(231,76,60,0.8)'),borderRadius:3
    }}]}},
    options:{{
      responsive:true,
      plugins:{{legend:{{labels:{{color:'#aaa',font:{{size:11}}}}}}}},
      scales:{{x:{{ticks:xTicks,grid:gridCfg}},y:{{ticks:yTicks,grid:gridCfg}}}}
    }}
  }});

  // Campanhas
  document.getElementById('camp-body').innerHTML = !d.campaigns||d.campaigns.length===0
    ? '<tr><td colspan="8" style="text-align:center;color:#888">Sem campanhas ativas</td></tr>'
    : d.campaigns.map(c => `<tr>
        <td><span class="badge active">ATIVO</span>${{c.name}}</td>
        <td>${{BRL(c.spend)}}</td><td>${{c.impressions.toLocaleString('pt-BR')}}</td>
        <td>${{c.clicks.toLocaleString('pt-BR')}}</td>
        <td class="${{c.ctr>=2?'pos':'neg'}}">${{PCT(c.ctr)}}</td>
        <td class="${{c.cpm>0&&c.cpm<55?'pos':'neg'}}">${{BRL(c.cpm)}}</td>
        <td>${{c.purchases}}</td>
        <td>${{c.purchases>0?BRL(c.cpa):'—'}}</td>
      </tr>`).join('');

  // DRE 3 linhas
  const d1 = ystStr, d7 = w7Str, d30 = new Date(todayD - 30*86400000).toISOString().slice(0,10);
  const r1d  = hist.filter(r => r.data === d1);
  const r7d  = hist.filter(r => r.data >= d7  && r.data <= d1);
  const r30d = hist.filter(r => r.data >= d30 && r.data <= d1);
  function dreRow(label, recs) {{
    if(!recs.length) return `<tr><td style="font-weight:600">${{label}}</td><td colspan="7" style="color:#555">sem dados</td></tr>`;
    const ped=sumPeriod(recs,'pedidos'),rec=sumPeriod(recs,'receita_bruta'),
          mc=sumPeriod(recs,'margem_contribuicao'),ads=sumPeriod(recs,'gasto_ads'),
          fix=sumPeriod(recs,'fixos_dia'),res=sumPeriod(recs,'resultado'),
          roas=ads>0?rec/ads:0,mcp=rec>0?mc/rec*100:0;
    return `<tr>
      <td style="font-weight:600">${{label}}</td><td>${{ped}}</td><td>${{BRL(rec)}}</td>
      <td>${{BRL(mc)}} (${{mcp.toFixed(0)}}%)</td><td>${{BRL(ads)}}</td><td>${{BRL(fix)}}</td>
      <td class="${{res>=0?'pos':'neg'}}">${{BRL(res)}}</td><td>${{roas.toFixed(2)}}x</td>
    </tr>`;
  }}
  document.getElementById('dre-body').innerHTML =
    dreRow(`Ontem — ${{fmtData(d1)}}`, r1d) + dreRow('Últimos 7 dias', r7d) + dreRow('Últimos 30 dias', r30d);

  // Lançamentos
  renderLancamentos(d.lancamentos || []);

  // Custos fixos (tabela com add/delete)
  const fc = d.fixed_costs || {{}};
  const ft = d.fixed_total || 0;
  _fixedCostsFromAPI = fc;
  const CAT_COLORS = {{
    'Pessoal':'#9b59b6','Infraestrutura':'#3498db','Plataforma':'#1abc9c',
    'Marketing':'#e67e22','Logística':'#e74c3c','Administrativo':'#95a5a6',
    'Tecnologia':'#2ecc71','Outros':'#555'
  }};
  document.getElementById('fixos-body').innerHTML =
    Object.entries(fc).map(([k,v]) => {{
      const val = typeof v === 'object' ? v.valor : v;
      const cat = typeof v === 'object' ? v.categoria : 'Outros';
      const cor = CAT_COLORS[cat] || '#555';
      return `<tr>
        <td>${{k}}</td>
        <td><span style="background:${{cor}}22;color:${{cor}};border:1px solid ${{cor}}44;border-radius:4px;padding:2px 8px;font-size:.75rem;font-weight:600">${{cat}}</span></td>
        <td>${{BRL(val)}}</td>
        <td style="color:#888">${{BRL(val/30)}}/dia</td>
        <td><button onclick="deleteFixo('${{k}}')" style="background:#3d1a1a;color:#e74c3c;border:none;border-radius:4px;padding:3px 10px;cursor:pointer;font-size:.75rem">✕</button></td>
      </tr>`;
    }}).join('') +
    `<tr style="font-weight:700;border-top:2px solid #3d4060;color:#f39c12">
       <td colspan="2">TOTAL MENSAL</td><td>${{BRL(ft)}}</td><td style="color:#888">${{BRL(ft/30)}}/dia</td><td></td>
     </tr>`;

  // Kits resumo
  const kitsData = d.kits || [];
  document.getElementById('kits-resumo-body').innerHTML = kitsData.map(k => {{
    const cmvT = k.cmv + k.mixer;
    const mc = k.preco - cmvT - k.preco*0.025 - k.preco*0.0499 - k.preco*0.10 - 20;
    return `<tr><td>${{k.nome}}</td><td>${{BRL(k.preco)}}</td><td>${{BRL(cmvT)}}</td>
      <td class="pos">${{BRL(mc)}}</td><td class="pos">${{(mc/k.preco*100).toFixed(1)}}%</td></tr>`;
  }}).join('');

  // Inicializa fixos editáveis da precificação com valores da API
  const fixosPrec = document.getElementById('fixos-prec-rows');
  if(fixosPrec && Object.keys(fc).length > 0) {{
    fixosPrec.innerHTML = Object.entries(fc).map(([nome,val],i) => {{
      const v = typeof val === 'object' ? val.valor : val;
      return `<div class="prec-row">
        <span class="prec-label">${{nome}}</span>
        <input type="number" id="fixo_${{i}}" value="${{v.toFixed(2)}}" step="10" onchange="calc()">
      </div>`;
    }}).join('');
    window._nFixos = Object.keys(fc).length;
  }}
  calc();
}}

// ── Precificação cálculo ──────────────────────────────────────────────────
function calc() {{
  const nFixos = window._nFixos || 3;
  let fixosMes = 0;
  for(let i=0;i<nFixos;i++) {{
    const el = document.getElementById('fixo_'+i);
    if(el) fixosMes += parseFloat(el.value)||0;
  }}
  const fixosDia = fixosMes/30;
  const fmEl = document.getElementById('fixos_mes');
  const fdEl = document.getElementById('fixos_dia');
  if(fmEl) fmEl.textContent = fmt(fixosMes);
  if(fdEl) fdEl.textContent = fmt(fixosDia)+'/dia';

  const peds = parseInt(document.getElementById('peds_dia').value)||3;
  const fixoPorPed = fixosDia/peds;
  const metas = [0.10,0.13,0.15];
  let tbodyHtml = '';

  KIT_IDS.forEach(kid => {{
    const g = id => {{ const el=document.getElementById(kid+'_'+id); return el?parseFloat(el.value)||0:0; }};
    const preco=g('preco'),cmv=g('cmv'),mixer=g('mixer'),frete=g('frete'),
          imposto=g('imposto'),gateway=g('gateway'),yampi=g('yampi');
    const varTotal = cmv+mixer+frete+preco*imposto/100+preco*gateway/100+preco*yampi/100;
    const mc = preco - varTotal;

    const sl = id => document.getElementById(kid+'_'+id);
    if(sl('preco_label')) sl('preco_label').textContent = fmt(preco);
    if(preco>0) {{
      if(sl('cmv_pct'))   sl('cmv_pct').textContent   = pct(cmv/preco*100);
      if(sl('mixer_pct')) sl('mixer_pct').textContent = pct(mixer/preco*100);
      if(sl('frete_pct')) sl('frete_pct').textContent = pct(frete/preco*100);
    }}
    if(sl('var_total')) sl('var_total').textContent = fmt(varTotal);
    if(sl('var_pct'))   sl('var_pct').textContent   = preco>0?pct(varTotal/preco*100):'—';
    if(sl('mc'))        sl('mc').textContent        = fmt(mc);
    if(sl('mc_pct'))    sl('mc_pct').textContent    = preco>0?pct(mc/preco*100):'—';

    const ads13 = mc - fixoPorPed - preco*0.13;
    if(sl('roas13')) sl('roas13').textContent = ads13>0?(preco/ads13).toFixed(2)+'x':'inviável';
    if(sl('cpa13'))  sl('cpa13').textContent  = ads13>0?fmt(ads13):'—';

    let cells='', cpa13str='—';
    metas.forEach((meta,mi) => {{
      const ads = mc - fixoPorPed - preco*meta;
      if(ads<=0) {{ cells+=`<td style="color:#e74c3c">inviável</td>`; }}
      else {{
        const roas=preco/ads, cor=roas<=3?'#27ae60':roas<=4?'#e67e22':'#e74c3c';
        cells+=`<td style="color:${{cor}}">${{roas.toFixed(2)}}x</td>`;
        if(mi===1) cpa13str=fmt(ads);
      }}
    }});
    const nomes={{'k1':'1 Pacote','k2':'2 Pacotes (Power Duo)','k3':'3 Pacotes'}};
    tbodyHtml+=`<tr><td>${{nomes[kid]||kid}}</td>${{cells}}<td style="color:#3498db">${{cpa13str}}</td></tr>`;
  }});
  const tb = document.getElementById('roas-tbody');
  if(tb) tb.innerHTML = tbodyHtml;
}}

// ── Exclusão de lançamentos ───────────────────────────────────────────────
let _excluirId = null;
function abrirModalExcluir(id, desc) {{
  _excluirId = id;
  document.getElementById('modal-desc').textContent = desc;
  const m = document.getElementById('modal-excluir');
  m.style.display = 'flex';
}}
function fecharModal() {{
  _excluirId = null;
  document.getElementById('modal-excluir').style.display = 'none';
}}
function confirmarExclusao() {{
  if (!_excluirId) return;
  const por = document.getElementById('modal-por').value;
  fetch('/api/lancamento/delete', {{
    method: 'POST',
    headers: {{'Content-Type':'application/json'}},
    body: JSON.stringify({{id: _excluirId, excluido_por: por}})
  }})
  .then(r => r.json())
  .then(r => {{
    fecharModal();
    if (r.ok) loadData();
    else alert('Erro ao excluir: ' + r.erro);
  }})
  .catch(() => {{ fecharModal(); alert('Erro de conexão.'); }});
}}

// ── Lançamentos ───────────────────────────────────────────────────────────
function renderLancamentos(items) {{
  const reversed = [...items].reverse();
  document.getElementById('lanc-body').innerHTML = reversed.length === 0
    ? '<tr><td colspan="8" style="text-align:center;color:#888">Nenhum lançamento ainda</td></tr>'
    : reversed.map(l => `<tr>
        <td>${{l.data||'—'}}</td>
        <td>${{l.lancado_por||'—'}}</td>
        <td>${{l.categoria||'—'}}</td>
        <td>${{l.descricao||'—'}}</td>
        <td><span class="badge ${{l.tipo==='Receita'||l.tipo==='Entrada'?'active':'paused'}}">${{l.tipo||'—'}}</span></td>
        <td class="${{l.tipo==='Receita'||l.tipo==='Entrada'?'pos':'neg'}}">${{BRL(l.valor||0)}}</td>
        <td style="color:#666">${{l.criado_em||'—'}}</td>
        <td><button onclick="abrirModalExcluir(${{l.id}},'${{(l.descricao||'').replace(/'/g,'\\'')}} — ${{BRL(l.valor||0)}}')" style="background:none;border:1px solid #ef444466;color:#ef4444;border-radius:4px;padding:3px 8px;cursor:pointer;font-size:.75rem">✕</button></td>
      </tr>`).join('');

  const totalGastos  = items.filter(l => l.tipo==='Despesa').reduce((s,l) => s+(l.valor||0), 0);
  const totalReceita = items.filter(l => l.tipo==='Receita'||l.tipo==='Entrada').reduce((s,l) => s+(l.valor||0), 0);
  const saldo = totalReceita - totalGastos;
  document.getElementById('lanc-foot').innerHTML = `
    <tr style="border-top:2px solid #3d4060">
      <td colspan="4" style="text-align:right;font-size:.8rem;color:#888;font-weight:600;letter-spacing:.5px;text-transform:uppercase;padding:12px 10px">Total do mês</td>
      <td></td>
      <td></td>
      <td style="padding:12px 10px">
        <div style="display:flex;gap:24px;align-items:center">
          <span style="display:flex;flex-direction:column;gap:2px">
            <span style="font-size:.68rem;color:#888;text-transform:uppercase;letter-spacing:.5px">Gastos</span>
            <span style="font-size:1rem;font-weight:700;color:#ef4444">${{BRL(totalGastos)}}</span>
          </span>
          <span style="color:#3d4060;font-size:1.2rem">|</span>
          <span style="display:flex;flex-direction:column;gap:2px">
            <span style="font-size:.68rem;color:#888;text-transform:uppercase;letter-spacing:.5px">Receita Bruta</span>
            <span style="font-size:1rem;font-weight:700;color:#22c55e">${{BRL(totalReceita)}}</span>
          </span>
          <span style="color:#3d4060;font-size:1.2rem">|</span>
          <span style="display:flex;flex-direction:column;gap:2px">
            <span style="font-size:.68rem;color:#888;text-transform:uppercase;letter-spacing:.5px">Saldo</span>
            <span style="font-size:1rem;font-weight:700;color:${{saldo>=0?'#22c55e':'#ef4444'}}">${{BRL(saldo)}}</span>
          </span>
        </div>
      </td>
      <td></td>
    </tr>`;
}}

// Seletor visual de quem lança
function selecionarPor(nome) {{
  document.getElementById('l-por').value = nome;
  const bc = document.getElementById('btn-caio');
  const bf = document.getElementById('btn-felipe');
  if(nome === 'Caio') {{
    bc.style.background='#6c63ff'; bc.style.borderColor='#6c63ff'; bc.style.color='#fff';
    bf.style.background='transparent'; bf.style.borderColor='#3d4060'; bf.style.color='#aaa';
  }} else {{
    bf.style.background='#6c63ff'; bf.style.borderColor='#6c63ff'; bf.style.color='#fff';
    bc.style.background='transparent'; bc.style.borderColor='#3d4060'; bc.style.color='#aaa';
  }}
}}

// Preenche data padrão do formulário
document.addEventListener('DOMContentLoaded', () => {{
  const today = new Date().toISOString().slice(0,10);
  const ld = document.getElementById('l-data');
  if(ld) ld.value = today;
}});

// Lançamentos — submit
document.getElementById('lanc-form').addEventListener('submit', e => {{
  e.preventDefault();
  const btn   = document.getElementById('lanc-btn');
  const data  = document.getElementById('l-data').value;
  const cat   = document.getElementById('l-cat').value;
  const desc  = document.getElementById('l-desc').value.trim();
  const valor = parseFloat(document.getElementById('l-valor').value);
  const tipo  = document.getElementById('l-tipo').value;
  const por   = document.getElementById('l-por').value;
  if(!desc || !valor || valor <= 0) {{ alert('Preencha descrição e valor.'); return; }}
  btn.textContent = 'Salvando...'; btn.disabled = true;
  fetch('/api/lancamento', {{
    method: 'POST',
    headers: {{'Content-Type':'application/json'}},
    body: JSON.stringify({{data, categoria:cat, descricao:desc, valor, tipo, lancado_por:por}})
  }})
  .then(r => r.json())
  .then(() => {{
    btn.textContent = '✓ Salvo!';
    document.getElementById('l-desc').value = '';
    document.getElementById('l-valor').value = '';
    setTimeout(() => {{ btn.textContent = '+ Lançar'; btn.disabled = false; }}, 1500);
    loadData();
  }})
  .catch(() => {{ btn.textContent = '+ Lançar'; btn.disabled = false; alert('Erro ao salvar.'); }});
}});

// Preview de rateio no formulário
document.getElementById('f-valor').addEventListener('input', function() {{
  const v = parseFloat(this.value) || 0;
  document.getElementById('f-rateio').textContent = v > 0 ? BRL(v/30)+'/dia' : '—/dia';
}});

// Custos Fixos — adicionar
document.getElementById('fixos-form').addEventListener('submit', e => {{
  e.preventDefault();
  const btn       = document.getElementById('fixos-btn');
  const nome      = document.getElementById('f-nome').value.trim();
  const valor     = parseFloat(document.getElementById('f-valor').value);
  const categoria = document.getElementById('f-cat').value;
  if(!nome || !valor || valor <= 0) {{ alert('Preencha nome e valor.'); return; }}
  btn.textContent = 'Salvando...'; btn.disabled = true;
  fetch('/api/fixos/add', {{
    method:'POST', headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{nome, valor, categoria}})
  }}).then(r => r.json()).then(() => {{
    document.getElementById('f-nome').value = '';
    document.getElementById('f-valor').value = '';
    document.getElementById('f-rateio').textContent = '—/dia';
    btn.textContent = '✓ Adicionado!';
    setTimeout(() => {{ btn.textContent = '+ Adicionar'; btn.disabled = false; }}, 1500);
    loadData();
  }}).catch(() => {{ btn.textContent = '+ Adicionar'; btn.disabled = false; }});
}});

// Custos Fixos — deletar
function deleteFixo(nome) {{
  if(!confirm(`Remover "${{nome}}" dos custos fixos?`)) return;
  fetch('/api/fixos/delete', {{
    method:'POST', headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{nome}})
  }}).then(() => loadData());
}}

// ── Auto-refresh ──────────────────────────────────────────────────────────
let cd = 60;
setInterval(() => {{
  cd--;
  const el = document.getElementById('countdown');
  if(el) el.textContent = cd;
  if(cd <= 0) {{ cd = 60; loadData(); }}
}}, 1000);

function loadData() {{
  fetch(API)
    .then(r => r.json())
    .then(d => {{ render(d); cd = 60; }})
    .catch(() => {{
      document.getElementById('ts').textContent = '⚠️ Servidor offline — rode: python3 financeiro/server.py';
    }});
}}

loadData();
</script>
</body>
</html>"""

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Dashboard gerado: {OUT_FILE}")
print("   Abra: file://" + OUT_FILE)
print("   O dashboard busca dados de http://localhost:8080/api/data automaticamente.")

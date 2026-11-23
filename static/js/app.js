/* StockKnap front-end: routing, API calls, event handling, and rendering. */
(() => {
  'use strict';

  // ------------------------------------------------------------------ config
  const CURRENCY = '₹';
  const ALGO = {
    fractional:   { name: 'Greedy · Fractional', label: 'Fractional', color: '#2dd4bf', complexity: 'O(n log n)' },
    greedy_whole: { name: 'Greedy · Whole items', label: 'Greedy (whole)', color: '#fbbf24', complexity: 'O(n log n)' },
    dp:           { name: 'Dynamic Programming · 0/1', label: 'DP 0/1', color: '#10b981', complexity: 'O(n · W)' },
  };
  const SEG_COLORS = ['#10b981', '#34d399', '#2dd4bf', '#fbbf24', '#38bdf8', '#86efac', '#a7f3d0', '#f87171', '#06b6d4', '#eab308'];
  const PAGES = {
    home:      ['Home', 'Intelligent Knapsack Inventory Management'],
    inventory: ['Inventory', 'Manage the products the warehouse can choose from.'],
    optimize:  ['Optimize', 'Pick an algorithm and see exactly which products it selects.'],
    compare:   ['Compare', 'Greedy vs Dynamic Programming on your own data.'],
    benchmark: ['Benchmark', 'How running time grows with the number of products.'],
    history:   ['History', 'Every comparison you have run is stored here.'],
    theory:    ['Theory', 'The concepts and logic behind the algorithms.'],
    about:     ['About', 'System architecture, design rationale, and algorithmic theory.'],
  };

  // ------------------------------------------------------------------- state
  const state = {
    products: [],
    capacity: parseInt(localStorage.getItem('capacity'), 10) || 50,
    sort: { key: 'id', dir: 1 },
    query: '',
  };

  // ----------------------------------------------------------------- helpers
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const num = (n) => Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });
  const money = (n) => CURRENCY + num(n);
  const fmtMs = (v) => {
    v = Number(v);
    if (v >= 100) return v.toFixed(0) + ' ms';
    if (v >= 1) return v.toFixed(2) + ' ms';
    if (v >= 0.01) return v.toFixed(3) + ' ms';
    return v.toFixed(4) + ' ms';
  };
  const fmtMsAxis = (v) => (v === 0 ? '0' : v >= 1 ? Number(v.toPrecision(3)) : Number(v.toPrecision(2))) + '';
  const ratioOf = (p) => p.profit / p.weight;

  async function api(path, options = {}) {
    const init = { method: options.method || 'GET', headers: {} };
    if (options.body !== undefined) {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(options.body);
    }
    const res = await fetch(path, init);
    let data = null;
    try { data = await res.json(); } catch (_) { /* empty body */ }
    if (!res.ok) throw new Error((data && data.error) || `Request failed (${res.status})`);
    return data;
  }

  function toast(message, type = 'ok') {
    const el = document.createElement('div');
    el.className = 'toast' + (type === 'error' ? ' error' : '');
    el.textContent = message;
    $('#toast-root').appendChild(el);
    setTimeout(() => el.remove(), 4200);
  }

  async function withButton(btn, label, task) {
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span>${label}`;
    try { return await task(); }
    catch (err) { toast(err.message, 'error'); }
    finally { btn.disabled = false; btn.innerHTML = original; }
  }

  function algoBadge(key) {
    const a = ALGO[key];
    return `<span class="tag">${a.complexity}</span>`;
  }

  // ----------------------------------------------------------------- routing
  function showPage(name) {
    if (!PAGES[name]) name = 'home';
    $$('.page-section').forEach((p) => p.classList.toggle('active', p.id === 'page-' + name));
    $$('#nav-menu a, .nav-brand').forEach((a) => {
      a.classList.toggle('active', a.dataset.page === name);
    });
    document.title = `${PAGES[name][0]} | StockKnap`;
    if (name === 'history') loadHistory();
    // close mobile menu if opened
    $('#nav-menu')?.classList.remove('mobile-open');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  const routeFromHash = () => {
    const hash = location.hash.replace('#', '');
    showPage(hash || 'home');
  };

  // -------------------------------------------------------------- capacity
  function updateCapacityHint() {
    const total = state.products.reduce((s, p) => s + p.weight, 0);
    const hint = $('#inv-capacity-hint');
    if (hint) {
      if (!Number.isInteger(state.capacity) || state.capacity <= 0) {
        hint.textContent = 'Enter a valid positive number for warehouse capacity.';
      } else if (!state.products.length) {
        hint.textContent = 'No products in inventory yet.';
      } else {
        const pct = Math.min(100, Math.round((state.capacity / total) * 100));
        hint.textContent = `Total stock: ${num(total)} kg · Warehouse capacity holds ${pct}% (${num(state.capacity)} kg).`;
      }
    }

    const optHint = $('#optimize-hint');
    if (optHint) optHint.textContent = `Capacity: ${num(state.capacity)} kg · ${state.products.length} products available`;

    const cmpHint = $('#compare-hint');
    if (cmpHint) cmpHint.textContent = `Capacity: ${num(state.capacity)} kg · ${state.products.length} products available`;
  }

  function validCapacity() {
    if (!Number.isInteger(state.capacity) || state.capacity <= 0) {
      toast('Please enter a positive whole number of kg for capacity.', 'error');
      $('#capacity').focus();
      return false;
    }
    return true;
  }

  // ================================================================ INVENTORY
  async function loadProducts() {
    state.products = await api('/api/products');
    renderInventory();
    updateCapacityHint();
  }

  function renderInventory() {
    const list = state.products;
    const totalW = list.reduce((s, p) => s + p.weight, 0);
    const totalP = list.reduce((s, p) => s + p.profit, 0);

    const statsEl = $('#inv-stats');
    if (statsEl) {
      statsEl.innerHTML = `
        <div class="stat"><div class="label">Total Products</div><div class="value">${list.length}</div><div class="sub">${new Set(list.map((p) => p.category)).size} categories</div></div>
        <div class="stat"><div class="label">Aggregate Weight</div><div class="value">${num(totalW)} kg</div><div class="sub">entire warehouse catalog</div></div>
        <div class="stat"><div class="label">Catalog Valuation</div><div class="value">${money(totalP)}</div><div class="sub">theoretical total yield</div></div>
        <div class="stat accent"><div class="label">Active Capacity</div><div class="value">${num(state.capacity)} kg</div><div class="sub">editable via topbar</div></div>`;
    }

    const catList = $('#category-list');
    if (catList) {
      catList.innerHTML = [...new Set(list.map((p) => p.category))].map((c) => `<option value="${esc(c)}">`).join('');
    }
    
    const countEl = $('#inv-count');
    if (countEl) countEl.textContent = list.length;

    // Search and sort
    const q = state.query.trim().toLowerCase();
    let rows = list.filter((p) => !q || p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));
    const { key, dir } = state.sort;
    rows = [...rows].sort((a, b) => {
      const av = key === 'ratio' ? ratioOf(a) : a[key];
      const bv = key === 'ratio' ? ratioOf(b) : b[key];
      return (typeof av === 'string' ? av.localeCompare(bv) : av - bv) * dir;
    });

    $$('#product-table th[data-sort]').forEach((th) => {
      th.classList.toggle('sorted', th.dataset.sort === key);
      th.classList.toggle('desc', th.dataset.sort === key && dir === -1);
    });

    const bodyEl = $('#product-body');
    if (bodyEl) {
      bodyEl.innerHTML = rows.map((p) => `
        <tr>
          <td>${p.id}</td>
          <td><strong>${esc(p.name)}</strong></td>
          <td><span class="cat">${esc(p.category)}</span></td>
          <td class="num">${num(p.weight)} kg</td>
          <td class="num">${money(p.profit)}</td>
          <td class="num">${num(ratioOf(p).toFixed(2))}</td>
          <td class="num">
            <button class="icon-btn" data-edit="${p.id}">Edit</button>
            <button class="icon-btn del" data-del="${p.id}">Delete</button>
          </td>
        </tr>`).join('');
    }

    const empty = !rows.length;
    const emptyEl = $('#inv-empty');
    if (emptyEl) {
      emptyEl.hidden = !empty;
      emptyEl.innerHTML = list.length
        ? '<strong>No matching products.</strong><span>Try adjusting your search criteria.</span>'
        : '<strong>No products yet.</strong><span>Add a product above or load the default sample data.</span>';
    }
    const tableEl = $('#product-table');
    if (tableEl) tableEl.hidden = empty;
  }

  function bindInventory() {
    $('#product-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await api('/api/products', {
          method: 'POST',
          body: {
            name: $('#p-name').value,
            category: $('#p-category').value,
            weight: $('#p-weight').value,
            profit: $('#p-profit').value,
          },
        });
        e.target.reset();
        $('#p-name').focus();
        await loadProducts();
        toast('Product successfully added.');
      } catch (err) { toast(err.message, 'error'); }
    });

    $('#search')?.addEventListener('input', (e) => {
      state.query = e.target.value;
      renderInventory();
    });

    $('#product-table thead')?.addEventListener('click', (e) => {
      const th = e.target.closest('th[data-sort]');
      if (!th) return;
      const key = th.dataset.sort;
      state.sort = { key, dir: state.sort.key === key ? -state.sort.dir : 1 };
      renderInventory();
    });

    $('#product-body')?.addEventListener('click', async (e) => {
      const editId = e.target.dataset.edit;
      const delId = e.target.dataset.del;
      if (editId) openEdit(Number(editId));
      if (delId) {
        const p = state.products.find((x) => x.id === Number(delId));
        if (!confirm(`Remove "${p.name}" from inventory?`)) return;
        try {
          await api('/api/products/' + delId, { method: 'DELETE' });
          await loadProducts();
          toast('Product deleted.');
        } catch (err) { toast(err.message, 'error'); }
      }
    });

    $('#btn-samples')?.addEventListener('click', async () => {
      if (state.products.length && !confirm('Replace current catalog with benchmark sample set?')) return;
      try {
        await api('/api/products/samples', { method: 'POST' });
        await loadProducts();
        toast('Sample catalog loaded.');
      } catch (err) { toast(err.message, 'error'); }
    });

    $('#btn-clear')?.addEventListener('click', async () => {
      if (!state.products.length || !confirm('Permanently delete ALL products from catalog?')) return;
      try {
        await api('/api/products', { method: 'DELETE' });
        await loadProducts();
        toast('Catalog cleared.');
      } catch (err) { toast(err.message, 'error'); }
    });

    // edit modal dialog
    const dlg = $('#edit-dialog');
    $('#e-cancel')?.addEventListener('click', () => dlg?.close());
    $('#edit-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await api('/api/products/' + $('#e-id').value, {
          method: 'PUT',
          body: {
            name: $('#e-name').value,
            category: $('#e-category').value,
            weight: $('#e-weight').value,
            profit: $('#e-profit').value,
          },
        });
        dlg.close();
        await loadProducts();
        toast('Product updated.');
      } catch (err) { toast(err.message, 'error'); }
    });
  }

  function openEdit(id) {
    const p = state.products.find((x) => x.id === id);
    if (!p) return;
    $('#e-id').value = p.id;
    $('#e-name').value = p.name;
    $('#e-category').value = p.category;
    $('#e-weight').value = p.weight;
    $('#e-profit').value = p.profit;
    $('#edit-dialog')?.showModal();
  }

  // ================================================================ OPTIMIZE
  function selectedAlgo() { return $('input[name="algo"]:checked')?.value || 'dp'; }

  function syncAlgoCards() {
    $$('.algo-card').forEach((c) => c.classList.toggle('selected', $('input', c)?.checked));
  }

  function fractionBadge(f) {
    if (f >= 0.9999) return '<span class="badge badge-full">100% Stored</span>';
    if (f > 0) return `<span class="badge badge-partial">${(f * 100).toFixed(1)}% Fractional</span>`;
    return '<span class="badge badge-skip">Omitted</span>';
  }

  function capacityBar(res) {
    const cap = res.capacity;
    const segs = res.selected.map((s, i) => {
      const pct = (s.taken_weight / cap) * 100;
      return `<div class="seg" style="width:${pct}%;background:${SEG_COLORS[i % SEG_COLORS.length]}" title="${esc(s.name)}: ${num(s.taken_weight)} kg"></div>`;
    }).join('');
    const legend = res.selected.map((s, i) =>
      `<span><i style="background:${SEG_COLORS[i % SEG_COLORS.length]}"></i>${esc(s.name)} <b>${num(s.taken_weight)} kg</b></span>`).join('');
    return `
      <div class="capbar">${segs}</div>
      <div class="capbar-scale"><span>0 kg</span><span>${num(res.total_weight)} kg utilized · ${num(res.remaining)} kg free</span><span>${num(cap)} kg limit</span></div>
      <div class="legend">${legend || '<span class="muted">No items selected within capacity constraints.</span>'}</div>`;
  }

  function selectedTable(res) {
    if (!res.selected.length) return '<div class="empty"><strong>No products selected.</strong><span>Try increasing capacity or adding smaller weight items.</span></div>';
    const rows = res.selected.map((s) => `
      <tr>
        <td><strong>${esc(s.name)}</strong></td>
        <td><span class="cat">${esc(s.category)}</span></td>
        <td class="num">${num(s.weight)} kg</td>
        <td class="num">${money(s.profit)}</td>
        <td class="num">${fractionBadge(s.fraction)}</td>
        <td class="num">${num(s.taken_weight)} kg</td>
        <td class="num">${money(s.earned)}</td>
      </tr>`).join('');
    const ids = new Set(res.selected.map((s) => s.id));
    const left = state.products.filter((p) => !ids.has(p.id));
    return `
      <div class="table-wrap"><table class="table">
        <thead><tr><th>Product</th><th>Category</th><th class="num">Weight</th><th class="num">Unit Profit</th><th class="num">Capacity Ratio</th><th class="num">Weight Stored</th><th class="num">Net Profit Earned</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot><tr><td colspan="5">Optimal Summary</td><td class="num">${num(res.total_weight)} kg</td><td class="num">${money(res.total_profit)}</td></tr></tfoot>
      </table></div>
      <div class="sub-title">Unselected Catalog Items (${left.length})</div>
      <div class="chips">${left.length ? left.map((p) => `<span class="chip">${esc(p.name)} · ${num(p.weight)} kg · ${money(p.profit)}</span>`).join('') : '<span class="muted">All catalog items fully accommodated.</span>'}</div>`;
  }

  function greedyStepsTable(res) {
    const rows = res.steps.map((s) => {
      let badge = '<span class="badge badge-skip">Skip</span>';
      if (s.action === 'full') badge = '<span class="badge badge-full">Take 100%</span>';
      if (s.action === 'partial') badge = `<span class="badge badge-partial">Split ${(s.fraction * 100).toFixed(1)}%</span>`;
      return `<tr>
        <td>${s.rank}</td>
        <td><strong>${esc(s.name)}</strong></td>
        <td class="num">${num(s.weight)} kg</td>
        <td class="num">${money(s.profit)}</td>
        <td class="num"><b>${num(s.ratio)}</b></td>
        <td class="num">${num(s.remaining_before)} kg</td>
        <td>${badge}</td>
        <td class="muted">${esc(s.reason)}</td>
      </tr>`;
    }).join('');
    const intro = res.key === 'fractional'
      ? 'Products are sorted descending by <b>density (profit per kg)</b>. Full items are taken while space permits; the first item exceeding remaining space is split fractionally to exhaust capacity.'
      : 'Items are sorted descending by <b>profit per kg</b> and taken whole if remaining space allows. Items too large are skipped without backtracking.';
    return `<div class="explain">${intro}</div>
      <div class="table-wrap"><table class="table">
        <thead><tr><th>Rank</th><th>Product</th><th class="num">Weight</th><th class="num">Profit</th><th class="num">Profit / kg</th><th class="num">Available Space</th><th>Decision</th><th>Explanation</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>`;
  }

  function dpStepsTable(res) {
    const rows = res.steps.map((s) => `
      <tr>
        <td>${s.step}</td>
        <td><strong>${esc(s.name)}</strong> <span class="muted">(${num(s.weight)} kg, ${money(s.profit)})</span></td>
        <td class="num">${num(s.capacity_left)} kg</td>
        <td class="num">${money(s.with_item)}</td>
        <td class="num">${money(s.without_item)}</td>
        <td>${s.action === 'take' ? '<span class="badge badge-take">Include</span>' : '<span class="badge badge-skip">Omit</span>'}</td>
        <td class="muted">${esc(s.reason)}</td>
      </tr>`).join('');
    return `<div class="explain">After DP table completion, the optimal subset is reconstructed via <b>backtracking</b> from state <code>dp[n][W]</code>. If <code>dp[i][c] &ne; dp[i-1][c]</code>, product <i>i</i> was chosen.</div>
      <div class="table-wrap"><table class="table">
        <thead><tr><th>Step</th><th>Product i</th><th class="num">Capacity c</th><th class="num">dp[i][c]</th><th class="num">dp[i-1][c]</th><th>Decision</th><th>Reasoning</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>`;
  }

  function dpTable(res) {
    if (!res.table) return `<div class="empty"><strong>DP Table Display Limit.</strong><span>${esc(res.table_note || '')}</span></div>`;
    const { rows, labels, capacity, path } = res.table;
    const pathMap = new Map(path.map(([i, c, t]) => [i + ':' + c, t]));
    let head = '<tr><th>Item \\ Capacity</th>';
    for (let c = 0; c <= capacity; c++) head += `<th>${c}</th>`;
    head += '</tr>';
    const body = rows.map((row, i) => {
      const label = i === 0 ? '0 · (Baseline)' : `${i} · ${esc(labels[i - 1])}`;
      const cells = row.map((v, c) => {
        const key = i + ':' + c;
        let cls = '';
        if (pathMap.has(key)) cls = pathMap.get(key) ? 'taken' : 'path';
        if (i === rows.length - 1 && c === capacity) cls += ' answer';
        return `<td class="${cls}">${num(v)}</td>`;
      }).join('');
      return `<tr><th>${label}</th>${cells}</tr>`;
    }).join('');
    return `<div class="explain">State matrix where <code>dp[i][c]</code> contains maximum valuation reachable utilizing first <i>i</i> items within <i>c</i> kg.</div>
      <div class="dp-key">
        <span><i style="background:#059669"></i>Selected item (Backtrack node)</span>
        <span><i style="background:rgba(245, 158, 11, 0.25)"></i>Backtrack path (Item skipped)</span>
        <span><i style="outline:2px solid #34d399;outline-offset:-2px"></i>Optimum answer: dp[n][W]</span>
      </div>
      <div class="dp-scroll"><table class="dp-table"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
  }

  function renderOptimize(res) {
    const a = ALGO[res.key];
    const isDp = res.key === 'dp';
    const parts = res.partial_items ? `${res.full_items} whole + ${res.partial_items} partial` : `${res.full_items} whole`;
    const container = $('#optimize-result');
    if (!container) return;

    container.innerHTML = `
      <div class="result-stack">
        <div class="stat-grid">
          <div class="stat accent"><div class="label">Total Return</div><div class="value">${money(res.total_profit)}</div><div class="sub">${esc(a.name)}</div></div>
          <div class="stat"><div class="label">Stored Weight</div><div class="value">${num(res.total_weight)} kg</div><div class="sub">of ${num(res.capacity)} kg capacity</div></div>
          <div class="stat"><div class="label">Capacity Utilization</div><div class="value">${res.utilization}%</div><div class="progress"><div style="width:${res.utilization}%"></div></div></div>
          <div class="stat"><div class="label">Items Allocated</div><div class="value">${res.items_selected}</div><div class="sub">${parts}</div></div>
          <div class="stat"><div class="label">Latency</div><div class="value">${fmtMs(res.time_ms)}</div><div class="sub">${a.complexity}${isDp ? ` · ${num(res.table_cells)} cells` : ''}</div></div>
        </div>

        <div class="card">
          <div class="card-head"><h2>Warehouse Capacity Distribution</h2></div>
          ${capacityBar(res)}
        </div>

        <div class="card" id="opt-tabs">
          <div class="tabs">
            <button class="tab active" data-tab="t-sel">Selected Products</button>
            <button class="tab" data-tab="t-steps">${isDp ? 'Backtracking Trace' : 'Sequential Decisions'}</button>
            ${isDp ? '<button class="tab" data-tab="t-table">DP State Matrix</button>' : ''}
          </div>
          <div class="tab-panel active" id="t-sel">${selectedTable(res)}</div>
          <div class="tab-panel" id="t-steps">${isDp ? dpStepsTable(res) : greedyStepsTable(res)}</div>
          ${isDp ? `<div class="tab-panel" id="t-table">${dpTable(res)}</div>` : ''}
        </div>
      </div>`;
  }

  function bindTabs(root) {
    root?.addEventListener('click', (e) => {
      const tab = e.target.closest('.tab');
      if (!tab) return;
      const card = tab.closest('.card');
      $$('.tab', card).forEach((t) => t.classList.toggle('active', t === tab));
      $$('.tab-panel', card).forEach((p) => p.classList.toggle('active', p.id === tab.dataset.tab));
    });
  }

  function bindOptimize() {
    $$('input[name="algo"]').forEach((r) => r.addEventListener('change', syncAlgoCards));
    syncAlgoCards();
    bindTabs($('#optimize-result'));

    $('#btn-optimize')?.addEventListener('click', (e) => {
      if (!validCapacity()) return;
      withButton(e.currentTarget, 'Calculating…', async () => {
        const res = await api('/api/optimize', { method: 'POST', body: { capacity: state.capacity, algorithm: selectedAlgo() } });
        renderOptimize(res);
      });
    });
  }

  // ================================================================= COMPARE
  function decisionBadge(sel) {
    if (!sel) return '<span class="badge badge-skip">—</span>';
    if (sel.fraction >= 0.9999) return '<span class="badge badge-full">Selected</span>';
    return `<span class="badge badge-partial">${(sel.fraction * 100).toFixed(0)}% partial</span>`;
  }

  function renderCompare(data) {
    const { results: R, summary: S, items } = data;
    const keys = ['fractional', 'greedy_whole', 'dp'];

    let verdict;
    if (S.dp_minus_greedy_whole > 0) {
      verdict = `<div class="verdict warn"><h3>Dynamic Programming gained ${money(S.dp_minus_greedy_whole)} extra profit (+${S.gap_percent}%) over greedy heuristic.</h3>
        <p>Greedy commits to high-density items irreversibly and leaves wasted gaps. DP examines all subset combinations and is guaranteed optimal for 0/1 indivisible stock. Execution took <b>${num(S.dp_slowdown)}&times;</b> longer.</p></div>`;
    } else {
      verdict = `<div class="verdict good"><h3>Identical optimality reached: Both Greedy and DP yield ${money(R.dp.total_profit)}.</h3>
        <p>The highest density items happen to pack neatly without remainder in this capacity configuration. DP required <b>${num(S.dp_slowdown)}&times;</b> more time.</p></div>`;
    }
    if (S.fractional_minus_dp > 0) {
      verdict += `<div class="explain" style="margin-top:12px">Fractional knapsack upper bound: <b>${money(S.fractional_minus_dp)}</b> beyond DP because item splitting is permitted.</div>`;
    }

    const cards = keys.map((k) => {
      const r = R[k], a = ALGO[k];
      return `<div class="card algo-result" style="border-top-color:${a.color}">
        <h3>${esc(a.name)}</h3>${algoBadge(k)}
        <div class="big">${money(r.total_profit)}</div>
        <div class="kv"><span>Weight Stored</span><b>${num(r.total_weight)} / ${num(r.capacity)} kg</b></div>
        <div class="kv"><span>Space Efficiency</span><b>${r.utilization}%</b></div>
        <div class="kv"><span>Item Count</span><b>${r.items_selected}${r.partial_items ? ` (${r.partial_items} split)` : ''}</b></div>
        <div class="kv"><span>Avg Latency</span><b>${fmtMs(r.time_ms)}</b></div>
      </div>`;
    }).join('');

    const sel = {};
    keys.forEach((k) => { sel[k] = new Map(R[k].selected.map((s) => [s.id, s])); });
    const matrix = [...items].sort((a, b) => ratioOf(b) - ratioOf(a)).map((p) => {
      const differs = !!sel.greedy_whole.get(p.id) !== !!sel.dp.get(p.id);
      return `<tr class="${differs ? 'differs' : ''}">
        <td><strong>${esc(p.name)}</strong></td>
        <td class="num">${num(p.weight)} kg</td>
        <td class="num">${money(p.profit)}</td>
        <td class="num">${num(ratioOf(p).toFixed(2))}</td>
        <td>${decisionBadge(sel.fractional.get(p.id))}</td>
        <td>${decisionBadge(sel.greedy_whole.get(p.id))}</td>
        <td>${decisionBadge(sel.dp.get(p.id))}</td>
      </tr>`;
    }).join('');

    const container = $('#compare-result');
    if (!container) return;

    container.innerHTML = `
      <div class="result-stack">
        ${verdict}
        <div class="grid-3">${cards}</div>

        <div class="grid-2">
          <div class="card chart">
            <div class="chart-title">Net Valuation Yield</div>
            <div class="chart-sub">Higher is better</div>
            ${Charts.bar({ labels: keys.map((k) => ALGO[k].label), values: keys.map((k) => R[k].total_profit), colors: keys.map((k) => ALGO[k].color), format: (v) => CURRENCY + num(v) })}
          </div>
          <div class="card chart">
            <div class="chart-title">Algorithmic Latency</div>
            <div class="chart-sub">Lower is better</div>
            ${Charts.bar({ labels: keys.map((k) => ALGO[k].label), values: keys.map((k) => R[k].time_ms), colors: keys.map((k) => ALGO[k].color), format: (v) => fmtMsAxis(v) + ' ms' })}
          </div>
        </div>

        <div class="card">
          <div class="card-head"><h2>Per-Item Decision Comparison</h2></div>
          <p class="note" style="margin:-6px 0 14px">Sorted descending by profit per kg. Highlighted rows mark items where Heuristic Greedy and DP disagree.</p>
          <div class="table-wrap"><table class="table">
            <thead><tr><th>Product</th><th class="num">Weight</th><th class="num">Profit</th><th class="num">Profit / kg</th>
              <th>Fractional</th><th>Greedy (Whole)</th><th>DP 0/1</th></tr></thead>
            <tbody>${matrix}</tbody>
          </table></div>
        </div>
      </div>`;
  }

  function bindCompare() {
    $('#btn-compare')?.addEventListener('click', (e) => {
      if (!validCapacity()) return;
      withButton(e.currentTarget, 'Benchmarking…', async () => {
        renderCompare(await api('/api/compare', { method: 'POST', body: { capacity: state.capacity } }));
      });
    });
  }

  // =============================================================== BENCHMARK
  function renderBenchmark(rows, logScale = true) {
    const xs = rows.map((r) => r.n);
    const chart = (log) => Charts.line({
      xLabels: xs.map(String),
      log,
      format: fmtMsAxis,
      xTitle: 'Item Count (n)',
      yTitle: 'Time (ms)',
      series: [
        { name: ALGO.fractional.label, color: ALGO.fractional.color, values: rows.map((r) => r.fractional_ms) },
        { name: ALGO.greedy_whole.label, color: ALGO.greedy_whole.color, values: rows.map((r) => r.greedy_whole_ms) },
        { name: ALGO.dp.label, color: ALGO.dp.color, values: rows.map((r) => r.dp_ms) },
      ],
    });

    const body = rows.map((r) => `
      <tr>
        <td class="num"><b>${r.n}</b></td>
        <td class="num">${num(r.capacity)} kg</td>
        <td class="num">${num(r.dp_cells)}</td>
        <td class="num">${fmtMs(r.fractional_ms)}</td>
        <td class="num">${fmtMs(r.greedy_whole_ms)}</td>
        <td class="num">${fmtMs(r.dp_ms)}</td>
        <td class="num"><b>${num(r.speedup)}×</b></td>
        <td class="num">${money(r.greedy_whole_profit)}</td>
        <td class="num">${money(r.dp_profit)}</td>
      </tr>`).join('');

    const last = rows[rows.length - 1];
    const container = $('#bench-result');
    if (!container) return;

    container.innerHTML = `
      <div class="result-stack">
        <div class="verdict"><h3>At n = ${last.n}, greedy was ${num(last.speedup)}× faster than DP.</h3>
          <p>Greedy operates in O(n log n) by sorting item ratios. DP computes an n &times; W table (${num(last.dp_cells)} operations here), scaling with storage magnitude W.</p></div>
        <div class="card chart">
          <div class="card-head">
            <h2>Computational Latency Scaling</h2>
            <label class="check-row"><input type="checkbox" id="bench-log" ${logScale ? 'checked' : ''}> Logarithmic time axis</label>
          </div>
          <div id="bench-chart">${chart(logScale)}</div>
        </div>
        <div class="card">
          <div class="card-head"><h2>Empirical Benchmark Records</h2></div>
          <div class="table-wrap"><table class="table">
            <thead><tr><th class="num">n</th><th class="num">Capacity W</th><th class="num">DP Table Cells</th>
              <th class="num">Fractional</th><th class="num">Greedy (Whole)</th><th class="num">DP 0/1</th>
              <th class="num">DP Slowdown</th><th class="num">Greedy Profit</th><th class="num">DP Profit</th></tr></thead>
            <tbody>${body}</tbody>
          </table></div>
        </div>
      </div>`;

    $('#bench-log')?.addEventListener('change', (e) => {
      const c = $('#bench-chart');
      if (c) c.innerHTML = chart(e.target.checked);
    });
  }

  function bindBenchmark() {
    $('#btn-benchmark')?.addEventListener('click', (e) => {
      const sizes = $('#bench-preset')?.value.split(',').map(Number);
      const repeats = Number($('#bench-repeats')?.value);
      withButton(e.currentTarget, 'Testing…', async () => {
        const data = await api('/api/benchmark', { method: 'POST', body: { sizes, repeats } });
        renderBenchmark(data.rows);
      });
    });
  }

  // ================================================================= HISTORY
  async function loadHistory() {
    try {
      const runs = await api('/api/history');
      const emptyEl = $('#history-empty');
      if (emptyEl) emptyEl.hidden = runs.length > 0;
      const bodyEl = $('#history-body');
      if (bodyEl) {
        bodyEl.innerHTML = runs.map((r) => {
          const gain = r.dp_profit - r.greedy_whole_profit;
          const when = new Date(r.created_at.replace(' ', 'T') + 'Z').toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
          return `<tr>
            <td>${esc(when)}</td>
            <td class="num">${num(r.capacity)} kg</td>
            <td class="num">${r.n_items}</td>
            <td class="num">${money(r.fractional_profit)}</td>
            <td class="num">${money(r.greedy_whole_profit)}</td>
            <td class="num"><b>${money(r.dp_profit)}</b></td>
            <td class="num ${gain > 0 ? 'pos' : ''}">${gain > 0 ? '+' + money(gain) : '—'}</td>
            <td class="num">${fmtMs(r.greedy_whole_ms)}</td>
            <td class="num">${fmtMs(r.dp_ms)}</td>
          </tr>`;
        }).join('');
      }
    } catch (err) { toast(err.message, 'error'); }
  }

  function bindHistory() {
    $('#btn-clear-history')?.addEventListener('click', async () => {
      if (!confirm('Permanently purge all saved comparisons?')) return;
      try {
        await api('/api/history', { method: 'DELETE' });
        await loadHistory();
        toast('History cleared.');
      } catch (err) { toast(err.message, 'error'); }
    });
  }

  // ========================================================== HOME HERO SEARCH
  function bindHero() {
    $('#hero-quick-form')?.addEventListener('submit', (e) => {
      e.preventDefault();
      const val = $('#hero-search-input')?.value.trim();
      if (!val) {
        location.hash = '#inventory';
        return;
      }
      state.query = val;
      location.hash = '#inventory';
      const searchInput = $('#search');
      if (searchInput) searchInput.value = val;
      renderInventory();
    });
  }

  // ==================================================================== INIT
  function bindCapacity() {
    const input = $('#capacity');
    if (!input) return;
    input.value = state.capacity;
    input.addEventListener('input', () => {
      const v = Number(input.value);
      state.capacity = Number.isFinite(v) ? v : NaN;
      if (Number.isInteger(v) && v > 0) localStorage.setItem('capacity', String(v));
      updateCapacityHint();
      renderInventory();
    });
  }

  function bindNavigation() {
    // Mobile hamburger toggle
    $('#mobile-toggle')?.addEventListener('click', () => {
      $('#nav-menu')?.classList.toggle('mobile-open');
    });

    // Delegate internal page navigation clicks
    document.addEventListener('click', (e) => {
      const link = e.target.closest('[data-page]');
      if (!link) return;
      const pageName = link.dataset.page;
      if (pageName && PAGES[pageName]) {
        e.preventDefault();
        location.hash = '#' + pageName;
      }
    });

    window.addEventListener('hashchange', routeFromHash);
  }

  async function init() {
    $$('.cur').forEach((el) => { el.textContent = CURRENCY; });
    bindNavigation();
    bindCapacity();
    bindHero();
    bindInventory();
    bindOptimize();
    bindCompare();
    bindBenchmark();
    bindHistory();
    routeFromHash();
    try { await loadProducts(); }
    catch (err) { toast(err.message, 'error'); }
  }

  document.addEventListener('DOMContentLoaded', init);
})();

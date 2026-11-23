/* Tiny dependency-free SVG charts (bar + line) — Emerald/Mint green aesthetic */
const Charts = (() => {
  const GRID = 'rgba(255, 255, 255, 0.08)';
  const TEXT = 'rgba(255, 255, 255, 0.55)';
  const INK = '#ffffff';

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /** Round a maximum up to a "nice" number that divides well into 4 ticks. */
  function niceMax(v) {
    if (v <= 0) return 1;
    const e = Math.pow(10, Math.floor(Math.log10(v)));
    const f = v / e;
    const nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 4 ? 4 : f <= 8 ? 8 : 10;
    return nf * e;
  }

  /** Vertical bar chart: one bar per label — emerald glassmorphic */
  function bar({ labels, values, colors, format, height = 260 }) {
    const W = 460, H = height;
    const m = { t: 28, r: 14, b: 44, l: 62 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const max = niceMax(Math.max(...values));
    const ticks = 4;
    let out = `<svg viewBox="0 0 ${W} ${H}" role="img">`;

    for (let k = 0; k <= ticks; k++) {
      const y = m.t + ih - (ih * k) / ticks;
      out += `<line x1="${m.l}" x2="${W - m.r}" y1="${y}" y2="${y}" stroke="${GRID}" stroke-dasharray="3 3"/>`;
      out += `<text x="${m.l - 8}" y="${y + 4}" text-anchor="end" font-size="11" fill="${TEXT}" font-family="Plus Jakarta Sans, Inter, sans-serif">${esc(format((max * k) / ticks))}</text>`;
    }

    const slot = iw / labels.length;
    const bw = Math.min(68, slot * 0.55);
    labels.forEach((label, i) => {
      const h = Math.max(values[i] > 0 ? 3 : 0, (ih * values[i]) / max);
      const x = m.l + slot * i + (slot - bw) / 2;
      const y = m.t + ih - h;
      const gradId = `bar-grad-green-${i}`;
      out += `<defs><linearGradient id="${gradId}" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="${colors[i]}" stop-opacity="0.95"/>
        <stop offset="100%" stop-color="${colors[i]}" stop-opacity="0.45"/>
      </linearGradient></defs>`;
      out += `<rect x="${x}" y="${y}" width="${bw}" height="${h}" rx="6" fill="url(#${gradId})"><title>${esc(label)}: ${esc(format(values[i]))}</title></rect>`;
      out += `<text x="${x + bw / 2}" y="${y - 8}" text-anchor="middle" font-size="12" font-weight="700" fill="${INK}" font-family="Plus Jakarta Sans, Inter, sans-serif">${esc(format(values[i]))}</text>`;
      out += `<text x="${x + bw / 2}" y="${H - m.b + 22}" text-anchor="middle" font-size="11" fill="${TEXT}" font-family="Plus Jakarta Sans, Inter, sans-serif">${esc(label)}</text>`;
    });
    return out + '</svg>';
  }

  /** Line chart with categorical x axis, optional log-scale y axis */
  function line({ xLabels, series, format, log = false, xTitle = '', yTitle = '', height = 320 }) {
    const W = 760, H = height;
    const m = { t: 42, r: 24, b: 56, l: 74 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const all = series.flatMap((s) => s.values).filter((v) => v > 0);

    let yOf, ticks;
    if (log) {
      const lo = Math.pow(10, Math.floor(Math.log10(Math.min(...all))));
      let hi = Math.pow(10, Math.ceil(Math.log10(Math.max(...all))));
      if (hi <= lo) hi = lo * 10;
      const decades = Math.round(Math.log10(hi / lo));
      ticks = Array.from({ length: decades + 1 }, (_, k) => lo * Math.pow(10, k));
      yOf = (v) => m.t + ih - (ih * (Math.log10(Math.max(v, lo)) - Math.log10(lo))) / (decades || 1);
    } else {
      const max = niceMax(Math.max(...all));
      ticks = [0, 1, 2, 3, 4].map((k) => (max * k) / 4);
      yOf = (v) => m.t + ih - (ih * v) / max;
    }
    const xOf = (i) => (xLabels.length === 1 ? m.l + iw / 2 : m.l + (iw * i) / (xLabels.length - 1));

    let out = `<svg viewBox="0 0 ${W} ${H}" role="img">`;

    // Grid lines
    ticks.forEach((t) => {
      const y = yOf(t);
      out += `<line x1="${m.l}" x2="${W - m.r}" y1="${y}" y2="${y}" stroke="${GRID}" stroke-dasharray="3 3"/>`;
      out += `<text x="${m.l - 8}" y="${y + 4}" text-anchor="end" font-size="11" fill="${TEXT}" font-family="Plus Jakarta Sans, Inter, sans-serif">${esc(format(t))}</text>`;
    });
    xLabels.forEach((label, i) => {
      out += `<text x="${xOf(i)}" y="${H - m.b + 22}" text-anchor="middle" font-size="12" fill="${TEXT}" font-family="Plus Jakarta Sans, Inter, sans-serif">${esc(label)}</text>`;
    });
    if (xTitle) out += `<text x="${m.l + iw / 2}" y="${H - 8}" text-anchor="middle" font-size="12" fill="${TEXT}" font-family="Plus Jakarta Sans, Inter, sans-serif">${esc(xTitle)}</text>`;
    if (yTitle) out += `<text x="16" y="${m.t + ih / 2}" text-anchor="middle" font-size="12" fill="${TEXT}" font-family="Plus Jakarta Sans, Inter, sans-serif" transform="rotate(-90 16 ${m.t + ih / 2})">${esc(yTitle)}</text>`;

    // Lines with subtle radiant area fill
    series.forEach((s, si) => {
      const pts = s.values.map((v, i) => `${xOf(i)},${yOf(v)}`).join(' ');
      const areaId = `area-green-${si}`;
      const baseY = m.t + ih;
      const areaPoints = s.values.map((v, i) => `${xOf(i)},${yOf(v)}`).join(' ') + ` ${xOf(s.values.length - 1)},${baseY} ${xOf(0)},${baseY}`;
      out += `<defs><linearGradient id="${areaId}" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="${s.color}" stop-opacity="0.2"/>
        <stop offset="100%" stop-color="${s.color}" stop-opacity="0"/>
      </linearGradient></defs>`;
      out += `<polygon points="${areaPoints}" fill="url(#${areaId})"/>`;
      out += `<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>`;
      s.values.forEach((v, i) => {
        out += `<circle cx="${xOf(i)}" cy="${yOf(v)}" r="4.5" fill="#04120a" stroke="${s.color}" stroke-width="2.5"><title>${esc(s.name)} (n=${esc(xLabels[i])}): ${esc(format(v))}</title></circle>`;
      });
    });

    // Legend
    let lx = m.l;
    series.forEach((s) => {
      out += `<rect x="${lx}" y="14" width="12" height="12" rx="3" fill="${s.color}" opacity="0.9"/>`;
      out += `<text x="${lx + 18}" y="24" font-size="12" fill="${INK}" font-family="Plus Jakarta Sans, Inter, sans-serif">${esc(s.name)}</text>`;
      lx += 32 + s.name.length * 6.8;
    });
    return out + '</svg>';
  }

  return { bar, line };
})();

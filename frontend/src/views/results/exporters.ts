/**
 * Self-contained, client-side exports (no libraries, no backend).
 *
 *  - CSV: serializes the in-memory rows of the visible dataset window, named
 *    after the canonical dataset, e.g. `daily_epidemic_day0-59.csv`.
 *  - PNG: clones the chart's own SVG, inlines the computed presentation styles
 *    (the stylesheet lives outside the SVG, and CSS custom properties must be
 *    resolved), rasterizes it through an offscreen canvas at 2x and downloads
 *    the result.
 */

import type { DatasetRow } from '../../api';

function download(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Give the browser a tick to start the download before revoking.
  window.setTimeout(() => URL.revokeObjectURL(url), 4_000);
}

function csvCell(value: DatasetRow[string]): string {
  if (value == null) return '';
  const s = String(value);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function rowsToCsv(rows: DatasetRow[]): string {
  if (!rows.length) return '';
  const columns: string[] = [];
  const seen = new Set<string>();
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!seen.has(key)) {
        seen.add(key);
        columns.push(key);
      }
    }
  }
  const lines = [columns.join(',')];
  for (const row of rows) lines.push(columns.map((c) => csvCell(row[c])).join(','));
  return `${lines.join('\n')}\n`;
}

/** Day-window suffix used in every export filename. */
export function dayWindowSuffix(from: number, to: number): string {
  return from === to ? `day${from}` : `day${from}-${to}`;
}

export function exportRowsAsCsv(rows: DatasetRow[], filename: string): number {
  const csv = rowsToCsv(rows);
  download(new Blob([csv], { type: 'text/csv;charset=utf-8' }), filename);
  return rows.length;
}

export interface BarSpec {
  name: string;
  count: number;
  share: number;
  color?: string;
}

/**
 * The ranked-bar panels are HTML, not SVG, so "Chart as PNG" builds an
 * equivalent standalone SVG (explicit colors resolved from the theme tokens)
 * and rasterizes that instead.
 */
export function buildBarsSvg(title: string, rows: BarSpec[]): SVGSVGElement {
  const NS = 'http://www.w3.org/2000/svg';
  const rowH = 26;
  const padT = 44;
  const width = 720;
  const height = padT + rows.length * rowH + 16;
  const labelW = 190;
  const valueW = 130;
  const barX = labelW + 12;
  const barW = width - barX - valueW;
  const maxC = Math.max(...rows.map((r) => r.count), 1);

  const ink = cssVar('--ink', '#1a1a1a');
  const ink3 = cssVar('--ink-3', '#6b6b6b');
  const track = cssVar('--panel-2', '#f0efea');
  const accent = cssVar('--accent', '#20707b');
  const panel = cssVar('--panel', '#ffffff');

  const svg = document.createElementNS(NS, 'svg') as SVGSVGElement;
  svg.setAttribute('xmlns', NS);
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', String(width));
  svg.setAttribute('height', String(height));

  const bg = document.createElementNS(NS, 'rect');
  bg.setAttribute('width', String(width));
  bg.setAttribute('height', String(height));
  bg.setAttribute('fill', panel);
  svg.appendChild(bg);

  const heading = document.createElementNS(NS, 'text');
  heading.setAttribute('x', '16');
  heading.setAttribute('y', '24');
  heading.setAttribute('fill', ink);
  heading.setAttribute('style', 'font:650 14px sans-serif');
  heading.textContent = title;
  svg.appendChild(heading);

  rows.forEach((r, i) => {
    const y = padT + i * rowH;
    const name = document.createElementNS(NS, 'text');
    name.setAttribute('x', String(labelW));
    name.setAttribute('y', String(y + 11));
    name.setAttribute('text-anchor', 'end');
    name.setAttribute('fill', ink3);
    name.setAttribute('style', 'font:500 12px sans-serif');
    name.textContent = r.name;
    svg.appendChild(name);

    const bgBar = document.createElementNS(NS, 'rect');
    bgBar.setAttribute('x', String(barX));
    bgBar.setAttribute('y', String(y + 2));
    bgBar.setAttribute('width', String(barW));
    bgBar.setAttribute('height', '11');
    bgBar.setAttribute('rx', '3');
    bgBar.setAttribute('fill', track);
    svg.appendChild(bgBar);

    const bar = document.createElementNS(NS, 'rect');
    bar.setAttribute('x', String(barX));
    bar.setAttribute('y', String(y + 2));
    bar.setAttribute('width', String(Math.max(2, (barW * r.count) / maxC)));
    bar.setAttribute('height', '11');
    bar.setAttribute('rx', '3');
    bar.setAttribute('fill', r.color ? cssVar(r.color, accent) : accent);
    svg.appendChild(bar);

    const value = document.createElementNS(NS, 'text');
    value.setAttribute('x', String(width - 16));
    value.setAttribute('y', String(y + 11));
    value.setAttribute('text-anchor', 'end');
    value.setAttribute('fill', ink);
    value.setAttribute('style', 'font:500 12px ui-monospace,monospace');
    value.textContent = `${Math.round(r.count).toLocaleString('en-GB')} · ${(r.share * 100).toFixed(1)}%`;
    svg.appendChild(value);
  });

  return svg;
}

const STYLE_PROPS = [
  'fill',
  'fill-opacity',
  'stroke',
  'stroke-width',
  'stroke-opacity',
  'stroke-dasharray',
  'stroke-linecap',
  'stroke-linejoin',
  'opacity',
  'font-family',
  'font-size',
  'font-weight',
  'font-style',
  'letter-spacing',
  'text-anchor',
  'dominant-baseline',
  'paint-order',
];

function inlineStyles(source: Element, clone: Element): void {
  const computed = window.getComputedStyle(source);
  const decls: string[] = [];
  for (const prop of STYLE_PROPS) {
    const value = computed.getPropertyValue(prop);
    if (value && value !== 'none' && value !== 'normal') decls.push(`${prop}:${value}`);
  }
  if (decls.length) clone.setAttribute('style', decls.join(';'));
  clone.removeAttribute('class');

  const sourceKids = source.children;
  const cloneKids = clone.children;
  for (let i = 0; i < sourceKids.length && i < cloneKids.length; i += 1) {
    inlineStyles(sourceKids[i], cloneKids[i]);
  }
}

/** Resolves `--token` or `var(--token)` against the current theme. */
function cssVar(name: string, fallback: string): string {
  const token = name.startsWith('var(') ? name.slice(4, -1).trim() : name;
  if (!token.startsWith('--')) return name;
  const v = window.getComputedStyle(document.documentElement).getPropertyValue(token).trim();
  return v || fallback;
}

/** Rasterizes an on-page SVG into a downloaded PNG. Resolves when saved. */
export async function exportSvgAsPng(
  svg: SVGSVGElement,
  filename: string,
  scale = 2,
): Promise<void> {
  const rect = svg.getBoundingClientRect();
  const attrW = Number(svg.getAttribute('width'));
  const attrH = Number(svg.getAttribute('height'));
  const width = Math.max(1, Math.round(rect.width || attrW || svg.clientWidth || 960));
  const height = Math.max(1, Math.round(rect.height || attrH || svg.clientHeight || 320));

  const clone = svg.cloneNode(true) as SVGSVGElement;
  inlineStyles(svg, clone);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('width', String(width));
  clone.setAttribute('height', String(height));

  const markup = new XMLSerializer().serializeToString(clone);
  const svgBlob = new Blob([markup], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(svgBlob);

  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('Could not rasterize the chart'));
      img.src = url;
    });

    const canvas = document.createElement('canvas');
    canvas.width = width * scale;
    canvas.height = height * scale;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas is unavailable in this browser');
    ctx.fillStyle = cssVar('--panel', '#ffffff');
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'));
    if (!blob) throw new Error('Could not encode the PNG');
    download(blob, filename);
  } finally {
    URL.revokeObjectURL(url);
  }
}

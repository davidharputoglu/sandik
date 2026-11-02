// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
// Thèmes : ceux fournis par l'édition + ceux créés par l'utilisateur.
// Un thème personnalisé n'a besoin que de quelques couleurs : le reste est calculé.

export const themes = $state({ list: [], selected: 'auto', active: null, key: 'sandik.theme', systemDark: false })

const rgb = (h) => {
  h = String(h || '#000').replace('#', '')
  if (h.length === 3) h = [...h].map((c) => c + c).join('')
  const n = parseInt(h.slice(0, 6), 16) || 0
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
const hex = (c) => '#' + c.map((v) => Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2, '0')).join('')
export const mix = (a, b, t) => { const A = rgb(a), B = rgb(b); return hex(A.map((v, i) => v + (B[i] - v) * t)) }
const lum = (c) => {
  const [r, g, b] = rgb(c).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4 })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
export const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05) }
const isDark = (c) => lum(c) < 0.2

/** Complète un thème partiel (primary, bg, text, sidebar suffisent). */
export function complete(theme) {
  const t = { ...theme }
  t.label = t.name
  t.bg ||= '#f4f6f8'
  t.mode ||= isDark(t.bg) ? 'dark' : 'light'
  const light = t.mode === 'light'
  t.primary ||= '#0fa39c'
  t.text ||= light ? '#1f2a33' : '#e8ecf0'
  t.surface ||= light ? '#ffffff' : mix(t.bg, '#ffffff', 0.05)
  t.surface_2 ||= mix(t.surface, t.text, 0.05)
  t.border ||= mix(t.surface, t.text, light ? 0.13 : 0.15)
  t.muted ||= mix(t.text, t.bg, 0.42)
  if (!t.primary_strong) {
    let s = t.primary
    if (light) for (let i = 0; i < 8 && contrast(s, '#ffffff') < 4.5; i++) s = mix(s, '#000000', 0.12)
    t.primary_strong = s
  }
  t.on_primary ||= contrast(t.primary_strong, '#ffffff') >= contrast(t.primary_strong, '#0b1215') ? '#ffffff' : '#0b1215'
  t.primary_soft ||= mix(t.primary, t.surface, light ? 0.88 : 0.84)
  t.sidebar ||= light ? mix(t.primary, '#061a1c', 0.72) : mix(t.bg, '#000000', 0.3)
  t.sidebar_mode ||= isDark(t.sidebar) ? 'dark' : 'light'
  t.sidebar_text ||= t.sidebar_mode === 'dark' ? mix('#ffffff', t.primary, 0.14) : mix(t.text, t.sidebar, 0.08)
  t.accent ||= t.primary
  return t
}

const VARS = ['primary', 'primary_strong', 'on_primary', 'primary_soft', 'bg', 'surface', 'surface_2', 'border',
  'text', 'muted', 'sidebar', 'sidebar_text', 'accent']

export function applyTheme(t, root = document.documentElement) {
  for (const k of VARS) root.style.setProperty(`--${k.replace('_', '-')}`, t[k])
  root.dataset.mode = t.mode
  root.dataset.sidebar = t.sidebar_mode
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', t.sidebar)
}

function resolve(id) {
  if (id === 'auto' || !themes.list.some((t) => t.id === id)) {
    const wanted = themes.systemDark ? 'dark' : 'light'
    return themes.list.find((t) => t.mode === wanted) || themes.list[0]
  }
  return themes.list.find((t) => t.id === id)
}

function refresh() {
  themes.active = resolve(themes.selected)
  if (themes.active) applyTheme(themes.active)
}

export function initThemes(edition) {
  themes.key = `${edition.id}.theme`
  themes.list = [...(edition.themes || []), ...(edition.appearance?.custom_themes || [])].map(complete)
  let saved = null
  try { saved = localStorage.getItem(themes.key) } catch { /* ignoré */ }
  themes.selected = saved || edition.appearance?.theme || 'auto'
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  themes.systemDark = mq.matches
  mq.addEventListener?.('change', (e) => { themes.systemDark = e.matches; refresh() })
  document.documentElement.dataset.density = edition.appearance?.density || 'comfortable'
  refresh()
}

export function selectTheme(id) {
  themes.selected = id
  try { localStorage.setItem(themes.key, id) } catch { /* ignoré */ }
  refresh()
}

export function setCustomThemes(edition, custom) {
  themes.list = [...(edition.themes || []), ...custom].map(complete)
  refresh()
}

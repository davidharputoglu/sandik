// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
import { locale } from './i18n.svelte.js'

const cache = new Map()
function nf(opts) {
  const key = locale() + JSON.stringify(opts)
  if (!cache.has(key)) {
    try { cache.set(key, new Intl.NumberFormat(locale(), opts)) } catch { cache.set(key, new Intl.NumberFormat('fr-FR', opts)) }
  }
  return cache.get(key)
}

export const toNumber = (v) => {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(String(v).replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(n) ? n : 0
}

export const money = (v, currency = 'EUR') => nf({ style: 'currency', currency }).format(toNumber(v))
export const number = (v, max = 3) => nf({ maximumFractionDigits: max }).format(toNumber(v))
export const percent = (v) => `${number(v, 2)} %`

export function date(v, opts = { day: '2-digit', month: '2-digit', year: 'numeric' }) {
  if (!v) return ''
  const d = new Date(typeof v === 'string' && v.length === 10 ? `${v}T12:00:00` : v)
  try { return new Intl.DateTimeFormat(locale(), opts).format(d) } catch { return d.toLocaleDateString('fr-FR') }
}

export const today = () => new Date().toISOString().slice(0, 10)

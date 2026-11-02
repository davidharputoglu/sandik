// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
// Compare chaque traduction au français (référence) : clés manquantes et en trop.
import { readFileSync, readdirSync } from 'node:fs'

const dir = new URL('../src/i18n/', import.meta.url)
const flat = (o, p = '') => Object.entries(o).flatMap(([k, v]) => (typeof v === 'object' ? flat(v, `${p}${k}.`) : [`${p}${k}`]))
const ref = new Set(flat(JSON.parse(readFileSync(new URL('fr.json', dir)))))
let failed = false
for (const file of readdirSync(dir).filter((f) => f.endsWith('.json') && f !== 'fr.json').sort()) {
  const keys = new Set(flat(JSON.parse(readFileSync(new URL(file, dir)))))
  const missing = [...ref].filter((k) => !keys.has(k))
  const extra = [...keys].filter((k) => !ref.has(k))
  const pct = Math.round(((ref.size - missing.length) / ref.size) * 100)
  console.log(`${file.padEnd(9)} ${String(pct).padStart(3)} %${missing.length ? `  manquantes : ${missing.length}` : ''}${extra.length ? `  en trop : ${extra.join(', ')}` : ''}`)
  if (missing.length) failed = true
}
process.exit(failed && process.argv.includes('--strict') ? 1 : 0)

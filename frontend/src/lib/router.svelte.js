// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
// Routeur minimal par ancre (#/...) : fonctionne aussi dans l'application de bureau.
export const route = $state({ path: '/', query: {} })

function parse() {
  const [path, q] = (location.hash.slice(1) || '/').split('?')
  route.path = path || '/'
  route.query = Object.fromEntries(new URLSearchParams(q || ''))
}
window.addEventListener('hashchange', parse)
parse()

export function go(path) {
  if (location.hash.slice(1) === path) parse()
  else location.hash = path
}

/** match('/documents/:id', '/documents/12') → { id: '12' } ; sinon null */
export function match(pattern, path = route.path) {
  const a = pattern.split('/'), b = path.split('/')
  if (a.length !== b.length) return null
  const params = {}
  for (let i = 0; i < a.length; i++) {
    if (a[i].startsWith(':')) params[a[i].slice(1)] = decodeURIComponent(b[i])
    else if (a[i] !== b[i]) return null
  }
  return params
}

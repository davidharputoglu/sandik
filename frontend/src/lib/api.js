// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
// Accès à l'API du serveur.
export class ApiError extends Error {
  constructor(status, detail) {
    let message = 'Erreur'
    let code = null, details = [], params = {}
    if (typeof detail === 'string') message = detail
    else if (Array.isArray(detail)) { code = 'validation'; details = detail.map((d) => `${(d.loc || []).slice(1).join('.')} : ${d.msg}`) ; message = details.join('\n') }
    else if (detail && typeof detail === 'object') ({ code = null, message = 'Erreur', details = [], params = {} } = detail)
    super(message)
    Object.assign(this, { status, code, details, params })
  }
}

let onUnauthorized = null
export function setUnauthorizedHandler(fn) { onUnauthorized = fn }

async function request(method, url, body) {
  let res
  try {
    res = await fetch(url, {
      method,
      credentials: 'same-origin',
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw Object.assign(new ApiError(0, null), { code: 'network' })
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    if (res.status === 401 && onUnauthorized && !url.startsWith('/api/auth')) onUnauthorized()
    throw new ApiError(res.status, data?.detail)
  }
  return data
}

export const api = {
  get: (url) => request('GET', url),
  post: (url, body = {}) => request('POST', url, body),
  put: (url, body) => request('PUT', url, body),
  del: (url) => request('DELETE', url),
}

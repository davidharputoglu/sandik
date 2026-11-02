// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
export const toasts = $state([])
let id = 0
export function toast(message, kind = 'success', timeout = 3500) {
  const t = { id: ++id, message, kind }
  toasts.push(t)
  setTimeout(() => {
    const i = toasts.findIndex((x) => x.id === t.id)
    if (i >= 0) toasts.splice(i, 1)
  }, timeout)
}

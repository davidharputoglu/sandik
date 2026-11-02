// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
import { api } from './api.js'

/** État global : édition, utilisateur connecté, réglages. */
export const app = $state({ edition: null, auth: null, settings: null, ready: false })

export async function loadSettings() {
  app.settings = await api.get('/api/settings')
  return app.settings
}

export const vatRates = () => app.settings?.vat?.rates || ['20', '10', '5.5', '2.1', '0']
export const units = () => app.settings?.units?.list || ['u', 'h', 'forfait']
export const vatExempt = () => app.settings?.vat?.regime === 'franchise'

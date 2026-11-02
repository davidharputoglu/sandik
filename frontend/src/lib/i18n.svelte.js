// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
// Traductions. Le français est la langue source ; l'anglais sert de secours aux autres langues.
import fr from '../i18n/fr.json'

const loaders = import.meta.glob('../i18n/*.json')

/** Langues connues : nom dans la langue elle-même, sens d'écriture, format des nombres et dates. */
export const LANGS = {
  fr: { name: 'Français', locale: 'fr-FR' },
  en: { name: 'English', locale: 'en-GB' },
  ar: { name: 'العربية', locale: 'ar-u-nu-latn', dir: 'rtl' },
  es: { name: 'Español', locale: 'es-ES' },
  pt: { name: 'Português', locale: 'pt-PT' },
  it: { name: 'Italiano', locale: 'it-IT' },
  tr: { name: 'Türkçe', locale: 'tr-TR' },
  az: { name: 'Azərbaycanca', locale: 'az-Latn-AZ' },
  kk: { name: 'Қазақша', locale: 'kk-KZ' },
  uz: { name: 'Oʻzbekcha', locale: 'uz-Latn-UZ' },
  tk: { name: 'Türkmençe', locale: 'tk-TM' },
  ky: { name: 'Кыргызча', locale: 'ky-KG' },
  tt: { name: 'Татарча', locale: 'tt-RU' },
  ba: { name: 'Башҡортса', locale: 'ba-RU' },
  ug: { name: 'ئۇيغۇرچە', locale: 'ug-u-nu-latn', dir: 'rtl' },
  cv: { name: 'Чӑвашла', locale: 'cv-RU' },
  crh: { name: 'Qırımtatarca', locale: 'crh' },
  gag: { name: 'Gagauzca', locale: 'gag' },
  sah: { name: 'Саха тыла', locale: 'sah-RU' },
  kaa: { name: 'Qaraqalpaqsha', locale: 'kaa' },
}

export const i18n = $state({ lang: 'fr', dict: fr, fallback: fr, available: ['fr'], key: 'sandik.lang' })

function lookup(dict, key) {
  let v = dict
  for (const part of key.split('.')) {
    if (v == null || typeof v !== 'object') return undefined
    v = v[part]
  }
  return typeof v === 'string' ? v : undefined
}

export function t(key, params) {
  let v = lookup(i18n.dict, key) ?? lookup(i18n.fallback, key) ?? lookup(fr, key) ?? key
  if (params) v = v.replace(/\{(\w+)\}/g, (m, k) => (params[k] ?? m))
  return v
}

/** Vrai si la clé existe (utile pour traduire les codes d'erreur du serveur). */
export function has(key) {
  return lookup(i18n.dict, key) !== undefined || lookup(fr, key) !== undefined
}

async function load(code) {
  if (code === 'fr') return fr
  const loader = loaders[`../i18n/${code}.json`]
  return loader ? (await loader()).default : fr
}

export async function setLang(code) {
  if (!i18n.available.includes(code)) code = i18n.available[0]
  const [dict, fallback] = await Promise.all([load(code), code === 'fr' || code === 'en' ? fr : load('en')])
  i18n.dict = dict
  i18n.fallback = fallback
  i18n.lang = code
  document.documentElement.lang = code
  document.documentElement.dir = LANGS[code]?.dir || 'ltr'
  try { localStorage.setItem(i18n.key, code) } catch { /* navigation privée */ }
}

export async function initLang(edition) {
  // Seules les langues de l'édition déjà traduites sont proposées (les autres arrivent au fil des traductions).
  const translated = new Set(['fr', ...Object.keys(loaders).map((p) => p.match(/([\w-]+)\.json$/)[1])])
  const wanted = edition.i18n?.languages?.length ? edition.i18n.languages : ['fr']
  i18n.available = wanted.filter((l) => translated.has(l))
  if (!i18n.available.length) i18n.available = ['fr']
  i18n.key = `${edition.id}.lang`
  let saved = null
  try { saved = localStorage.getItem(i18n.key) } catch { /* ignoré */ }
  const browser = (navigator.languages || []).map((l) => l.split('-')[0]).find((l) => i18n.available.includes(l))
  // ordre : choix de l'utilisateur, langue choisie à l'installation, langue du navigateur, langue par défaut
  const preferred = edition.i18n?.preferred
  const pick = [saved, preferred, browser, edition.i18n?.default].find((l) => l && i18n.available.includes(l))
  await setLang(pick || i18n.available[0])
}

/** Nom affiché d'un thème : traduit pour les thèmes fournis, tel quel pour les thèmes personnalisés. */
export function themeName(th) {
  return th.custom ? th.name : (lookup(i18n.dict, `theme.names.${th.id}`) ?? lookup(i18n.fallback, `theme.names.${th.id}`) ?? th.name)
}

export function locale() {
  return LANGS[i18n.lang]?.locale || i18n.lang
}

/** Message d'erreur traduit à partir d'une ApiError. */
export function errorText(err) {
  if (err?.code === 'network') return t('errors.network')
  if (err?.code && has(`errors.${err.code}`)) return t(`errors.${err.code}`, err.params)
  return err?.message || t('errors.generic')
}

export function errorDetails(err) {
  return (err?.details || []).map((d) => (has(`errors.missing.${d}`) ? t(`errors.missing.${d}`) : d))
}

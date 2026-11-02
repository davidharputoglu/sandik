<!-- SPDX-License-Identifier: AGPL-3.0-or-later — Copyright (C) 2026 David HARPUTOGLU -->
<script>
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { themeName, t, has, errorText, errorDetails } from '../lib/i18n.svelte.js'
  import { app, loadSettings } from '../lib/session.svelte.js'
  import { themes, selectTheme, setCustomThemes, complete, applyTheme } from '../lib/theme.svelte.js'
  import { toast } from '../lib/toast.svelte.js'
  import { go } from '../lib/router.svelte.js'
  import Icon from '../components/Icon.svelte'

  let { tab = 'company' } = $props()
  const TABS = ['company', 'documents', 'numbering', 'vat', 'appearance', 'fields', 'modules', 'about']
  const FORMS = {
    company: [['name', 'text', 2], ['legal_form'], ['capital'], ['siren'], ['siret'], ['vat_number'], ['rcs'], ['ape'],
      ['address_line1', 'text', 2], ['address_line2', 'text', 2], ['postal_code'], ['city'], ['country'], ['email'], ['phone'],
      ['website'], ['bank_name'], ['iban'], ['bic'], ['insurance', 'textarea', 2]],
    documents: [['quote_validity_days', 'number'], ['payment_terms_days', 'number'],
      ['default_operation_nature', 'select', 1, ['services', 'goods', 'mixed'], (v) => t(`doc.nature.${v}`)],
      ['vat_on_debits', 'boolean'], ['payment_terms_text', 'textarea', 2], ['early_payment_text', 'textarea', 2],
      ['late_penalty_text', 'textarea', 2], ['quote_intro', 'textarea', 2], ['quote_footer', 'textarea', 2], ['invoice_footer', 'textarea', 2]],
    vat: [['regime', 'select', 1, ['normal', 'franchise'], (v) => t(`settings.vat.regime_${v}`)], ['default_rate'],
      ['rates', 'list', 2], ['franchise_text', 'text', 2]],
  }

  let form = $state(structuredClone($state.snapshot(app.settings)))
  let error = $state(null)
  let busy = $state(false)

  async function save(keys) {
    error = null; busy = true
    try {
      for (const k of keys) await api.put(`/api/settings/${k}`, $state.snapshot(form[k]))
      await loadSettings()
      form = structuredClone($state.snapshot(app.settings))
      toast(t('common.saved'))
    } catch (err) { error = { text: errorText(err), details: err.details?.length ? err.details : errorDetails(err) } }
    finally { busy = false }
  }

  // ---- numérotation : aperçu identique au serveur
  function render(p, n = 1, d = new Date()) {
    return p.replace(/\{(YYYY|YY|MM|N(?::(\d{1,2}))?)\}/g, (m, tok, w) =>
      tok === 'YYYY' ? String(d.getFullYear()) : tok === 'YY' ? String(d.getFullYear()).slice(2)
        : tok === 'MM' ? String(d.getMonth() + 1).padStart(2, '0') : String(n).padStart(Number(w || 1), '0'))
  }

  // ---- logo de l'entreprise
  let logoVersion = $state(Date.now())
  async function uploadLogo(e) {
    const file = e.currentTarget.files?.[0]
    if (!file) return
    const res = await fetch('/api/company/logo', { method: 'PUT', body: file, credentials: 'same-origin' })
    if (!res.ok) { toast(t('settings.company.logo_invalid'), 'error'); return }
    await loadSettings(); form.company.has_logo = true; logoVersion = Date.now(); toast(t('common.saved'))
  }
  async function removeLogo() { await api.del('/api/company/logo'); await loadSettings(); form.company.has_logo = false }

  // ---- thèmes personnalisés
  let draft = $state(null)
  function newTheme(base) {
    const src = base || themes.active
    draft = { id: base?.custom ? base.id : `perso-${Date.now().toString(36)}`, name: base?.custom ? base.name : t('settings.appearance.new_theme_name'),
      mode: src.mode, primary: src.primary, bg: src.bg, surface: src.surface, text: src.text, sidebar: src.sidebar, custom: true }
  }
  $effect(() => { if (draft) applyTheme(complete($state.snapshot(draft))) })
  function cancelTheme() { draft = null; selectTheme(themes.selected) }
  async function saveTheme() {
    const custom = (form.appearance.custom_themes || []).filter((x) => x.id !== draft.id)
    custom.push($state.snapshot(draft))
    form.appearance.custom_themes = custom
    await save(['appearance'])
    setCustomThemes(app.edition, custom)
    const id = draft.id; draft = null; selectTheme(id)
  }
  async function deleteTheme(id) {
    if (!confirm(t('settings.appearance.confirm_delete_theme'))) return
    form.appearance.custom_themes = form.appearance.custom_themes.filter((x) => x.id !== id)
    await save(['appearance'])
    setCustomThemes(app.edition, form.appearance.custom_themes)
    if (themes.selected === id) selectTheme('auto')
  }
  function setDensity(v) { form.appearance.density = v; document.documentElement.dataset.density = v }

  // ---- champs personnalisés
  let fields = $state([])
  let newField = $state({ entity: 'client', label: '', type: 'text', options: '', required: false, show_on_pdf: false })
  const slug = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').replace(/^(\d)/, 'f_$1').slice(0, 60) || 'champ'
  async function loadFields() { fields = await api.get('/api/custom-fields') }
  async function addField(e) {
    e.preventDefault(); error = null
    try {
      await api.post('/api/custom-fields', { ...$state.snapshot(newField), key: slug(newField.label),
        options: newField.options.split(',').map((s) => s.trim()).filter(Boolean) })
      newField.label = ''; newField.options = ''; loadFields(); toast(t('common.saved'))
    } catch (err) { error = { text: errorText(err), details: [] } }
  }
  async function deleteField(f) { if (confirm(t('settings.fields.confirm_delete'))) { await api.del(`/api/custom-fields/${f.id}`); loadFields() } }

  // ---- modules
  let modules = $state([])
  let restart = $state(false)
  async function loadModules() { modules = (await api.get('/api/modules-admin')).modules }
  async function importModule(e) {
    const file = e.currentTarget.files?.[0]
    e.currentTarget.value = ''
    if (!file || !confirm(t('settings.modules.import_warning'))) return
    const res = await fetch('/api/modules-admin/import', { method: 'POST', body: file, credentials: 'same-origin' })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) { toast(errorText({ code: data.detail?.code, message: data.detail?.message }), 'error'); return }
    restart = true; toast(t('settings.modules.imported', { name: data.name })); loadModules()
  }
  async function toggleModule(m) { await api.post(`/api/modules-admin/${m.id}/toggle`); restart = true; loadModules() }
  async function deleteModule(m) {
    if (!confirm(t('settings.modules.confirm_delete'))) return
    await api.del(`/api/modules-admin/${m.id}`); restart = true; loadModules()
  }

  onMount(() => { loadFields(); loadModules() })
  const ed = app.edition
  const isAdmin = $derived(!app.auth?.auth_enabled || app.auth?.user?.role === 'admin')
</script>

{#snippet formGrid(key, spec)}
  <div class="grid-2">
    {#each spec as [name, type = 'text', span = 1, options, optLabel]}
      {@const label = t(`settings.${key}.${name}`)}
      {@const hint = has(`settings.${key}.${name}_hint`) ? t(`settings.${key}.${name}_hint`) : ''}
      {#if type === 'boolean'}
        <label class="check"><input type="checkbox" bind:checked={form[key][name]} />{label}</label>
      {:else}
        <label class="field" class:span-2={span === 2}>
          <span>{label}</span>
          {#if type === 'textarea'}<textarea class="input" rows="3" bind:value={form[key][name]}></textarea>
          {:else if type === 'select'}
            <select class="input" bind:value={form[key][name]}>{#each options as o}<option value={o}>{optLabel(o)}</option>{/each}</select>
          {:else if type === 'list'}
            <input class="input" value={(form[key][name] || []).join(', ')}
              onchange={(e) => (form[key][name] = e.currentTarget.value.split(',').map((s) => s.trim()).filter(Boolean))} />
          {:else if type === 'number'}<input class="input" type="number" min="0" bind:value={form[key][name]} />
          {:else}<input class="input" bind:value={form[key][name]} />{/if}
          {#if hint}<small class="hint">{hint}</small>{/if}
        </label>
      {/if}
    {/each}
  </div>
{/snippet}

<div class="page">
  <div class="page-head"><div class="grow"><h1>{t('settings.title')}</h1><div class="sub">{t('settings.subtitle')}</div></div></div>
  <div class="settings">
    <nav class="tabs-v">
      {#each TABS as k}
        <a href={`#/parametres/${k}`} class:on={tab === k}>{t(`settings.tabs.${k}`)}</a>
      {/each}
    </nav>

    <div class="stack">
      {#if error}
        <div class="alert danger"><strong>{error.text}</strong>{#if error.details?.length}<ul>{#each error.details as d}<li>{d}</li>{/each}</ul>{/if}</div>
      {/if}

      {#if tab === 'company'}
        <section class="card card-body stack">
          <h2>{t('settings.company.logo')}</h2>
          <div class="row wrap">
            {#if form.company.has_logo}<img class="company-logo" src={`/api/company/logo?v=${logoVersion}`} alt="" />{/if}
            <label class="btn"><Icon name="plus" size={16} />{t('settings.company.logo_upload')}
              <input type="file" accept="image/png,image/jpeg,image/webp" hidden onchange={uploadLogo} /></label>
            {#if form.company.has_logo}<button class="btn danger" onclick={removeLogo}>{t('common.delete')}</button>{/if}
          </div>
          <small class="hint">{t('settings.company.logo_hint')}</small>
        </section>
        <section class="card card-body stack">
          {@render formGrid('company', FORMS.company)}
          <div class="row"><span class="grow"></span><button class="btn primary" disabled={busy} onclick={() => save(['company'])}>{t('common.save')}</button></div>
        </section>

      {:else if tab === 'documents'}
        <section class="card card-body stack">
          {@render formGrid('documents', FORMS.documents)}
          <label class="field"><span>{t('settings.documents.units')}</span>
            <input class="input" value={form.units.list.join(', ')} onchange={(e) => (form.units.list = e.currentTarget.value.split(',').map((s) => s.trim()).filter(Boolean))} /></label>
          <div class="row"><span class="grow"></span><button class="btn primary" disabled={busy} onclick={() => save(['documents', 'units'])}>{t('common.save')}</button></div>
        </section>

      {:else if tab === 'numbering'}
        <section class="card card-body stack">
          <p class="muted">{t('settings.numbering.intro')}</p>
          <div class="grid-2">
            {#each ['quote', 'invoice', 'credit_note'] as k}
              <label class="field"><span>{t(`doc.types.${k}`)}</span><input class="input" bind:value={form.numbering[k]} /></label>
              <div class="field"><span>{t('settings.numbering.preview')}</span><div class="preview">{render(form.numbering[k] || '')}</div></div>
            {/each}
            <label class="field"><span>{t('settings.numbering.reset')}</span>
              <select class="input" bind:value={form.numbering.reset}>
                {#each ['yearly', 'monthly', 'never'] as r}<option value={r}>{t(`settings.numbering.reset_${r}`)}</option>{/each}
              </select></label>
          </div>
          <div class="alert info small">{t('settings.numbering.tokens')}</div>
          <div class="row"><span class="grow"></span><button class="btn primary" disabled={busy} onclick={() => save(['numbering'])}>{t('common.save')}</button></div>
        </section>

      {:else if tab === 'vat'}
        <section class="card card-body stack">
          {@render formGrid('vat', FORMS.vat)}
          <div class="row"><span class="grow"></span><button class="btn primary" disabled={busy} onclick={() => save(['vat'])}>{t('common.save')}</button></div>
        </section>

      {:else if tab === 'appearance'}
        <section class="card card-body stack">
          <h2>{t('settings.appearance.my_theme')}</h2>
          <div class="theme-grid">
            <button class="theme-card" class:on={themes.selected === 'auto'} onclick={() => selectTheme('auto')}>
              <span class="swatch auto"><span></span><span></span></span><strong>{t('theme.auto')}</strong>
              <small class="muted">{t('settings.appearance.auto_hint')}</small>
            </button>
            {#each themes.list as th (th.id)}
              <div class="theme-card" class:on={themes.selected === th.id} role="button" tabindex="0"
                onclick={() => selectTheme(th.id)} onkeydown={(e) => e.key === 'Enter' && selectTheme(th.id)}>
                <span class="swatch" style:background={th.bg}>
                  <span class="side" style:background={th.sidebar}></span>
                  <span class="body"><span class="bar" style:background={th.surface} style:border-color={th.border}></span>
                    <span class="pill" style:background={th.primary_strong}></span></span>
                </span>
                <strong>{themeName(th)}</strong>
                {#if th.custom}
                  <span class="row">
                    <button class="btn sm ghost" onclick={(e) => { e.stopPropagation(); newTheme(th) }}><Icon name="edit" size={14} /></button>
                    <button class="btn sm ghost danger" onclick={(e) => { e.stopPropagation(); deleteTheme(th.id) }}><Icon name="trash" size={14} /></button>
                  </span>
                {:else}<small class="muted">{t(`theme.mode_${th.mode}`)}</small>{/if}
              </div>
            {/each}
            {#if isAdmin}
              <button class="theme-card add" onclick={() => newTheme()}><Icon name="palette" size={22} /><strong>{t('settings.appearance.create')}</strong></button>
            {/if}
          </div>
        </section>

        {#if draft}
          <section class="card card-body stack editor">
            <h2>{t('settings.appearance.editor')}</h2>
            <p class="muted small">{t('settings.appearance.editor_hint')}</p>
            <div class="grid-3">
              <label class="field"><span>{t('settings.appearance.theme_name')}</span><input class="input" bind:value={draft.name} /></label>
              <label class="field"><span>{t('settings.appearance.base')}</span>
                <select class="input" bind:value={draft.mode}><option value="light">{t('theme.mode_light')}</option><option value="dark">{t('theme.mode_dark')}</option></select></label>
              {#each ['primary', 'sidebar', 'bg', 'surface', 'text'] as c}
                <label class="field"><span>{t(`settings.appearance.color_${c}`)}</span>
                  <span class="color"><input type="color" bind:value={draft[c]} /><input class="input" bind:value={draft[c]} /></span></label>
              {/each}
            </div>
            <div class="row"><span class="grow"></span>
              <button class="btn" onclick={cancelTheme}>{t('common.cancel')}</button>
              <button class="btn primary" onclick={saveTheme}>{t('settings.appearance.save_theme')}</button></div>
          </section>
        {/if}

        {#if isAdmin}
          <section class="card card-body stack">
            <h2>{t('settings.appearance.organization')}</h2>
            <div class="grid-2">
              <label class="field"><span>{t('settings.appearance.default_theme')}</span>
                <select class="input" bind:value={form.appearance.theme}>
                  <option value="auto">{t('theme.auto')}</option>
                  {#each themes.list as th}<option value={th.id}>{themeName(th)}</option>{/each}
                </select></label>
              <label class="field"><span>{t('settings.appearance.density')}</span>
                <select class="input" value={form.appearance.density} onchange={(e) => setDensity(e.currentTarget.value)}>
                  <option value="comfortable">{t('settings.appearance.density_comfortable')}</option>
                  <option value="compact">{t('settings.appearance.density_compact')}</option>
                </select></label>
              <label class="field"><span>{t('settings.appearance.document_accent')}</span>
                <span class="color"><input type="color" value={form.appearance.document_accent || '#0b8079'} oninput={(e) => (form.appearance.document_accent = e.currentTarget.value)} />
                  <button class="btn sm" onclick={() => (form.appearance.document_accent = '')}>{t('settings.appearance.reset')}</button></span></label>
              <label class="check"><input type="checkbox" bind:checked={form.appearance.show_logo_on_documents} />{t('settings.appearance.show_logo')}</label>
            </div>
            <div class="row"><span class="grow"></span><button class="btn primary" disabled={busy} onclick={() => save(['appearance'])}>{t('common.save')}</button></div>
          </section>
        {/if}

      {:else if tab === 'fields'}
        <section class="card card-body stack">
          <p class="muted">{t('settings.fields.intro')}</p>
          <form class="grid-3" onsubmit={addField}>
            <label class="field"><span>{t('settings.fields.entity')}</span>
              <select class="input" bind:value={newField.entity}>{#each ['client', 'article', 'document'] as en}<option value={en}>{t(`settings.fields.entity_${en}`)}</option>{/each}</select></label>
            <label class="field"><span>{t('settings.fields.label')}</span><input class="input" bind:value={newField.label} required /></label>
            <label class="field"><span>{t('settings.fields.type')}</span>
              <select class="input" bind:value={newField.type}>{#each ['text', 'textarea', 'number', 'date', 'boolean', 'select'] as ty}<option value={ty}>{t(`settings.fields.type_${ty}`)}</option>{/each}</select></label>
            {#if newField.type === 'select'}
              <label class="field span-3"><span>{t('settings.fields.options')}</span><input class="input" bind:value={newField.options} placeholder="A, B, C" /></label>
            {/if}
            <label class="check"><input type="checkbox" bind:checked={newField.required} />{t('settings.fields.required')}</label>
            <span></span>
            <button class="btn primary"><Icon name="plus" size={16} />{t('settings.fields.add')}</button>
          </form>
        </section>
        <section class="card">
          {#if fields.length}
            <table class="table"><thead><tr><th>{t('settings.fields.label')}</th><th>{t('settings.fields.entity')}</th><th>{t('settings.fields.type')}</th><th></th></tr></thead>
              <tbody>{#each fields as f}
                <tr><td><strong>{f.label}</strong> <span class="muted small">{f.key}</span></td><td>{t(`settings.fields.entity_${f.entity}`)}</td>
                  <td>{t(`settings.fields.type_${f.type}`)}</td>
                  <td class="num">{#if f.id}<button class="btn sm ghost danger" onclick={() => deleteField(f)}><Icon name="trash" size={15} /></button>
                    {:else}<span class="badge">{t('settings.fields.from_module', { module: f.source })}</span>{/if}</td></tr>
              {/each}</tbody></table>
          {:else}<div class="empty">{t('settings.fields.empty')}</div>{/if}
        </section>

      {:else if tab === 'modules'}
        {#if restart}<div class="alert">{t('settings.modules.restart')}</div>{/if}
        <section class="card card-body stack">
          <p class="muted">{t('settings.modules.intro')}</p>
          {#if isAdmin}
            <div class="row"><label class="btn primary"><Icon name="plus" size={16} />{t('settings.modules.import')}
              <input type="file" accept=".zip,application/zip" hidden onchange={importModule} /></label>
              <small class="muted">{t('settings.modules.import_hint')}</small></div>
          {/if}
        </section>
        <section class="card">
          {#if modules.length}
            <table class="table"><thead><tr><th>{t('settings.modules.name')}</th><th>{t('settings.modules.version')}</th><th>{t('doc.status')}</th><th></th></tr></thead>
              <tbody>{#each modules as m}
                <tr><td><strong>{m.name}</strong><div class="muted small">{m.description || ''}</div></td><td>{m.version || ''}</td>
                  <td><span class="badge {m.active ? 'success' : ''}">{m.active ? t('settings.modules.active') : t(`settings.modules.reason_${m.reason}`)}</span></td>
                  <td class="num">{#if isAdmin}
                    {#if m.reason !== 'restart' && m.reason !== 'edition'}<button class="btn sm" onclick={() => toggleModule(m)}>{m.active ? t('settings.modules.disable') : t('settings.modules.enable')}</button>{/if}
                    {#if m.origin === 'imported'}<button class="btn sm ghost danger" onclick={() => deleteModule(m)}><Icon name="trash" size={15} /></button>{/if}
                  {/if}</td></tr>
              {/each}</tbody></table>
          {:else}<div class="empty"><h3>{t('settings.modules.empty_title')}</h3>{t('settings.modules.empty_text')}</div>{/if}
        </section>

      {:else if tab === 'about'}
        <section class="card card-body about">
          <img src={themes.active?.mode === 'dark' && ed.assets.logo_dark ? ed.assets.logo_dark : ed.assets.logo} alt={ed.name} />
          <dl>
            <dt>{t('settings.about.version')}</dt><dd>{ed.version}</dd>
            <dt>{t('settings.about.author')}</dt><dd>{ed.about.author}</dd>
            <dt>{t('settings.about.contact')}</dt><dd><a href={`mailto:${ed.about.contact}`}>{ed.about.contact}</a></dd>
            <dt>{t('settings.about.license')}</dt><dd>{ed.license}</dd>
            {#if ed.about.source_url}<dt>{t('settings.about.source')}</dt><dd><a href={ed.about.source_url} target="_blank" rel="noopener">{ed.about.source_url}</a></dd>{/if}
            <dt>API</dt><dd><a href="/api/docs" target="_blank" rel="noopener">/api/docs</a></dd>
          </dl>
          <p><strong>{t('settings.about.credits')}</strong></p>
          <p class="muted small">{ed.about.copyright}. {t(`settings.about.license_text_${ed.license.startsWith('AGPL') ? 'agpl' : 'private'}`)}</p>
          <div class="alert small">{t('settings.about.disclaimer')}</div>
          <p class="muted small">{t('settings.about.third_party')}</p>
        </section>
      {/if}
    </div>
  </div>
</div>

<style>
  .settings { display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: 20px; align-items: start; }
  @media (max-width: 900px) { .settings { grid-template-columns: 1fr; } .tabs-v { flex-direction: row; overflow-x: auto; } }
  .tabs-v { display: flex; flex-direction: column; gap: 2px; position: sticky; top: 16px; }
  .tabs-v a { padding: 9px 12px; border-radius: 8px; text-decoration: none; color: var(--muted); font-weight: 550; white-space: nowrap; }
  .tabs-v a:hover { background: var(--surface-2); color: var(--text); }
  .tabs-v a.on { background: var(--primary-soft); color: var(--primary-strong); }
  :global([data-mode='dark']) .tabs-v a.on { color: var(--primary); }
  .company-logo { max-height: 56px; max-width: 200px; border: 1px solid var(--border); border-radius: 8px; padding: 6px; background: #fff; }
  .preview { height: var(--input-h); display: flex; align-items: center; padding: 0 11px; border-radius: 8px; background: var(--surface-2); font-family: ui-monospace, monospace; }
  .theme-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; }
  .theme-card { all: unset; box-sizing: border-box; display: grid; gap: 6px; padding: 10px; border-radius: 12px; border: 2px solid var(--border); cursor: pointer; background: var(--surface); }
  .theme-card:hover { border-color: color-mix(in srgb, var(--primary) 50%, var(--border)); }
  .theme-card.on { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-soft); }
  .theme-card.add { place-items: center; align-content: center; min-height: 120px; border-style: dashed; color: var(--muted); }
  .swatch { height: 70px; border-radius: 8px; display: flex; overflow: hidden; border: 1px solid var(--border); }
  .swatch .side { width: 30%; }
  .swatch .body { flex: 1; padding: 8px; display: grid; gap: 6px; align-content: start; }
  .swatch .bar { height: 18px; border-radius: 4px; border: 1px solid; }
  .swatch .pill { width: 48%; height: 10px; border-radius: 4px; }
  .swatch.auto { background: linear-gradient(135deg, #f2f7f7 50%, #14181d 50%); }
  .color { display: flex; gap: 8px; align-items: center; }
  .color input[type='color'] { width: 42px; height: var(--input-h); border: 1px solid var(--border); border-radius: 8px; padding: 2px; background: var(--surface); }
  .editor { border-color: var(--primary); }
  .about img { width: 260px; max-width: 100%; margin-bottom: 12px; }
  .about dl { display: grid; grid-template-columns: max-content 1fr; gap: 6px 18px; }
  .about dt { color: var(--muted); }
  .about dd { margin: 0; font-weight: 550; }
</style>

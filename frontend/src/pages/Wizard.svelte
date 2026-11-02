<!-- SPDX-License-Identifier: AGPL-3.0-or-later — Copyright (C) 2026 David HARPUTOGLU -->
<script>
  // Assistant de premier lancement : langue, dossier des données (bureau), entreprise, thème.
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { themeName, t, i18n, LANGS, setLang, errorText } from '../lib/i18n.svelte.js'
  import { app, loadSettings } from '../lib/session.svelte.js'
  import { themes, selectTheme } from '../lib/theme.svelte.js'
  import Icon from '../components/Icon.svelte'

  let location = $state(null)
  let dataDir = $state('')
  let restart = $state(false)
  let error = $state('')
  let company = $state({ ...$state.snapshot(app.settings.company) })
  let regime = $state(app.settings.vat.regime)

  const steps = $derived(['language', ...(location?.can_change && !app.settings.setup.location_done ? ['location'] : []), 'company', 'theme'])
  let index = $state(0)
  const step = $derived(steps[index])

  onMount(async () => {
    try { location = await api.get('/api/system/location'); dataDir = location.data_dir } catch { location = { can_change: false } }
  })

  async function next() {
    error = ''
    try {
      if (step === 'language') await api.put('/api/system/location', { language: i18n.lang }).catch(() => {})
      if (step === 'location' && dataDir.trim() && dataDir.trim() !== location.data_dir) {
        const r = await api.put('/api/system/location', { data_dir: dataDir.trim() })
        if (r.restart_required) { restart = true; return }
      }
      if (step === 'company') {
        await api.put('/api/settings/company', $state.snapshot(company))
        await api.put('/api/settings/vat', { regime })
      }
      if (index < steps.length - 1) { index++; return }
      await finish()
    } catch (err) { error = errorText(err) }
  }

  async function finish() {
    await api.put('/api/settings/appearance', { theme: themes.selected })
    await api.put('/api/settings/setup', { done: true })
    await loadSettings()
  }
</script>

<div class="wrap">
  <div class="card box">
    <img class="logo" src={themes.active?.mode === 'dark' && app.edition.assets.logo_dark ? app.edition.assets.logo_dark : app.edition.assets.logo} alt={app.edition.name} />
    <div class="dots">{#each steps as s, i}<span class:on={i <= index}></span>{/each}</div>

    {#if restart}
      <h1>{t('wizard.restart_title')}</h1>
      <p class="muted">{t('wizard.restart_text')}</p>
    {:else if step === 'language'}
      <h1>{t('wizard.welcome', { name: app.edition.name })}</h1>
      <p class="muted">{t('wizard.language_text')}</p>
      <div class="langs">
        {#each i18n.available as code}
          <button class="lang" class:on={i18n.lang === code} onclick={() => setLang(code)} dir={LANGS[code]?.dir || 'ltr'}>{LANGS[code]?.name || code}</button>
        {/each}
      </div>
    {:else if step === 'location'}
      <h1>{t('wizard.location_title')}</h1>
      <p class="muted">{t('wizard.location_text')}</p>
      <label class="field"><span>{t('wizard.data_dir')}</span><input class="input" bind:value={dataDir} /></label>
      <small class="hint">{t('wizard.location_hint')}</small>
    {:else if step === 'company'}
      <h1>{t('wizard.company_title')}</h1>
      <p class="muted">{t('wizard.company_text')}</p>
      <div class="grid-2">
        <label class="field span-2"><span>{t('settings.company.name')}</span><input class="input" bind:value={company.name} /></label>
        <label class="field"><span>{t('settings.company.legal_form')}</span><input class="input" bind:value={company.legal_form} /></label>
        <label class="field"><span>{t('settings.company.siren')}</span><input class="input" bind:value={company.siren} /></label>
        <label class="field span-2"><span>{t('settings.company.address_line1')}</span><input class="input" bind:value={company.address_line1} /></label>
        <label class="field"><span>{t('settings.company.postal_code')}</span><input class="input" bind:value={company.postal_code} /></label>
        <label class="field"><span>{t('settings.company.city')}</span><input class="input" bind:value={company.city} /></label>
        <label class="field"><span>{t('settings.company.email')}</span><input class="input" type="email" bind:value={company.email} /></label>
        <label class="field"><span>{t('settings.company.phone')}</span><input class="input" bind:value={company.phone} /></label>
        <label class="field span-2"><span>{t('settings.vat.regime')}</span>
          <select class="input" bind:value={regime}>
            <option value="normal">{t('settings.vat.regime_normal')}</option><option value="franchise">{t('settings.vat.regime_franchise')}</option>
          </select></label>
      </div>
    {:else if step === 'theme'}
      <h1>{t('wizard.theme_title')}</h1>
      <p class="muted">{t('wizard.theme_text')}</p>
      <div class="themes">
        <button class="lang" class:on={themes.selected === 'auto'} onclick={() => selectTheme('auto')}>{t('theme.auto')}</button>
        {#each themes.list as th}
          <button class="lang" class:on={themes.selected === th.id} onclick={() => selectTheme(th.id)}>
            <span class="chip" style:background={th.sidebar} style:border-color={th.primary}></span>{themeName(th)}</button>
        {/each}
      </div>
    {/if}

    {#if error}<div class="alert danger">{error}</div>{/if}
    {#if !restart}
      <div class="row">
        {#if index > 0}<button class="btn ghost" onclick={() => index--}><Icon name="back" size={16} class="flip" />{t('common.back')}</button>{/if}
        <span class="grow"></span>
        <button class="btn ghost" onclick={finish}>{t('wizard.skip')}</button>
        <button class="btn primary" onclick={next}>{index === steps.length - 1 ? t('wizard.finish') : t('wizard.next')}</button>
      </div>
    {/if}
  </div>
</div>

<style>
  .wrap { min-height: 100vh; display: grid; place-items: center; padding: 24px;
    background: radial-gradient(1200px 600px at 10% -10%, color-mix(in srgb, var(--primary) 18%, transparent), transparent), var(--bg); }
  .box { width: 100%; max-width: 620px; padding: 32px; display: grid; gap: 16px; }
  .logo { width: 200px; max-width: 70%; margin: 0 auto; display: block; }
  h1 { font-size: 21px; } p { margin: -6px 0 0; }
  .dots { display: flex; gap: 6px; justify-content: center; }
  .dots span { width: 28px; height: 4px; border-radius: 4px; background: var(--border); }
  .dots span.on { background: var(--primary); }
  .langs, .themes { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; max-height: 320px; overflow-y: auto; }
  .lang { all: unset; box-sizing: border-box; display: flex; gap: 8px; align-items: center; padding: 10px 12px; border-radius: 9px;
    border: 1.5px solid var(--border); cursor: pointer; font-weight: 550; background: var(--surface); }
  .lang:hover { border-color: var(--primary); }
  .lang.on { border-color: var(--primary); background: var(--primary-soft); }
  .chip { width: 16px; height: 16px; border-radius: 5px; border: 3px solid; }
</style>

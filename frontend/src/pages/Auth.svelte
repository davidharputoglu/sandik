<script>
  import { api } from '../lib/api.js'
  import { app } from '../lib/session.svelte.js'
  import { t, errorText } from '../lib/i18n.svelte.js'
  import { themes } from '../lib/theme.svelte.js'

  let { onsignedin } = $props()
  const setup = $derived(app.auth?.needs_setup)
  let form = $state({ name: '', email: '', password: '' })
  let error = $state('')
  let busy = $state(false)
  const logo = $derived(themes.active?.mode === 'dark' && app.edition.assets.logo_dark ? app.edition.assets.logo_dark : app.edition.assets.logo)

  async function submit(e) {
    e.preventDefault()
    error = ''
    busy = true
    try {
      await api.post(setup ? '/api/auth/setup' : '/api/auth/login', form)
      await onsignedin()
    } catch (err) {
      error = err.status === 401 ? t('auth.bad_credentials') : errorText(err)
    } finally {
      busy = false
    }
  }
</script>

<div class="wrap">
  <form class="card box" onsubmit={submit}>
    <img class="logo" src={logo} alt={app.edition.name} />
    <h1>{setup ? t('auth.setup_title') : t('auth.login_title')}</h1>
    {#if setup}<p class="muted">{t('auth.setup_intro')}</p>{/if}
    {#if setup}
      <label class="field"><span>{t('auth.name')}</span><input class="input" bind:value={form.name} required autocomplete="name" /></label>
    {/if}
    <label class="field"><span>{t('auth.email')}</span><input class="input" type="email" bind:value={form.email} required autocomplete="email" /></label>
    <label class="field">
      <span>{t('auth.password')}</span>
      <input class="input" type="password" bind:value={form.password} required minlength={setup ? 8 : 1}
        autocomplete={setup ? 'new-password' : 'current-password'} />
      {#if setup}<small class="hint">{t('auth.password_hint')}</small>{/if}
    </label>
    {#if error}<div class="alert danger">{error}</div>{/if}
    <button class="btn primary" disabled={busy}>{setup ? t('auth.create_account') : t('auth.login')}</button>
  </form>
</div>

<style>
  .wrap {
    min-height: 100vh; display: grid; place-items: center; padding: 24px;
    background: radial-gradient(1200px 600px at 10% -10%, color-mix(in srgb, var(--primary) 18%, transparent), transparent),
      var(--bg);
  }
  .box { width: 100%; max-width: 400px; padding: 32px; display: grid; gap: 16px; }
  .logo { width: 220px; max-width: 80%; margin: 0 auto 6px; display: block; }
  h1 { font-size: 20px; text-align: center; }
  p { margin: -6px 0 0; text-align: center; }
  .btn { width: 100%; height: 42px; }
</style>

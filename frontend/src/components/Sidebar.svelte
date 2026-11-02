<script>
  import Icon from './Icon.svelte'
  import { app } from '../lib/session.svelte.js'
  import { route, go } from '../lib/router.svelte.js'
  import { themeName, t, i18n, LANGS, setLang } from '../lib/i18n.svelte.js'
  import { themes, selectTheme } from '../lib/theme.svelte.js'
  import { api } from '../lib/api.js'

  let { open = $bindable(false) } = $props()
  const ed = $derived(app.edition)
  const logo = $derived(themes.active?.sidebar_mode === 'dark' && ed.assets.logo_dark ? ed.assets.logo_dark : ed.assets.logo)

  const groups = $derived([
    { items: [{ path: '/', icon: 'dashboard', label: t('nav.dashboard') }] },
    { title: t('nav.sales'), items: [
      { path: '/clients', icon: 'users', label: t('nav.clients') },
      { path: '/devis', icon: 'quote', label: t('nav.quotes') },
    ] },
    { title: t('nav.billing'), items: [
      { path: '/factures', icon: 'invoice', label: t('nav.invoices') },
      { path: '/avoirs', icon: 'credit', label: t('nav.credit_notes') },
    ] },
    { title: t('nav.catalog'), items: [{ path: '/articles', icon: 'box', label: t('nav.articles') }] },
    ...(ed.modules.some((m) => m.menu.length) ? [{ title: t('nav.modules'), items: ed.modules.flatMap((m) =>
      m.menu.map((e) => ({ path: `/m/${m.id}?p=${encodeURIComponent(e.path)}`, icon: 'module', label: e.label }))) }] : []),
  ])

  const DOC_ROUTES = { quote: '/devis', invoice: '/factures', credit_note: '/avoirs' }
  function active(path) {
    if (path === '/') return route.path === '/'
    if (route.path.startsWith('/documents')) return DOC_ROUTES[route.query.type || app.currentDocType] === path
    return route.path === path.split('?')[0] || route.path.startsWith(path.split('?')[0] + '/')
  }

  async function quit() {
    await api.post('/api/system/shutdown').catch(() => {})
    document.body.innerHTML = `<p style="font-family:system-ui;padding:40px;text-align:center">${t('common.bye')}</p>`
  }

  async function logout() {
    await api.post('/api/auth/logout')
    location.reload()
  }
</script>

<aside class="sidebar" class:open>
  <div class="brand">
    <a href="#/" onclick={() => (open = false)}><img src={logo} alt={ed.name} /></a>
  </div>

  <nav class="nav" aria-label={t('nav.main')}>
    {#each groups as g}
      {#if g.title}<div class="group">{g.title}</div>{/if}
      {#each g.items as item}
        <a href={'#' + item.path} class:active={active(item.path)} onclick={() => (open = false)}>
          <Icon name={item.icon} />{item.label}
        </a>
      {/each}
    {/each}
  </nav>

  <div class="foot">
    <a href="#/parametres" class="setting" class:active={route.path.startsWith('/parametres')} onclick={() => (open = false)}>
      <Icon name="settings" />{t('nav.settings')}
    </a>
    <div class="prefs">
      <label class="pref" title={t('nav.language')}>
        <Icon name="globe" size={16} />
        <select value={i18n.lang} onchange={(e) => setLang(e.currentTarget.value)} aria-label={t('nav.language')}>
          {#each i18n.available as code}<option value={code}>{LANGS[code]?.name || code}</option>{/each}
        </select>
      </label>
      <label class="pref" title={t('nav.theme')}>
        <Icon name="palette" size={16} />
        <select value={themes.selected} onchange={(e) => selectTheme(e.currentTarget.value)} aria-label={t('nav.theme')}>
          <option value="auto">{t('theme.auto')}</option>
          {#each themes.list as th}<option value={th.id}>{themeName(th)}</option>{/each}
        </select>
      </label>
    </div>
    {#if ed.desktop}
      <button class="setting quit" onclick={quit}><Icon name="logout" class="flip" />{t('nav.quit')}</button>
    {/if}
    {#if app.auth?.user}
      <div class="user">
        <span class="avatar">{app.auth.user.name.slice(0, 1).toUpperCase()}</span>
        <span class="grow ellipsis">{app.auth.user.name}</span>
        <button class="icon-btn" onclick={logout} title={t('nav.logout')} aria-label={t('nav.logout')}><Icon name="logout" size={17} class="flip" /></button>
      </div>
    {/if}
  </div>
</aside>
{#if open}<button class="scrim" aria-label={t('common.close')} onclick={() => (open = false)}></button>{/if}

<style>
  .sidebar {
    position: fixed; inset-block: 0; inset-inline-start: 0; width: var(--sidebar-w); display: flex; flex-direction: column;
    background: var(--sidebar); color: var(--sidebar-text); z-index: 30;
    border-inline-end: 1px solid color-mix(in srgb, var(--sidebar-text) 10%, transparent);
  }
  .brand { padding: 20px 20px 14px; }
  .brand img { display: block; width: 100%; max-width: 190px; height: auto; }
  .nav { flex: 1; overflow-y: auto; padding: 4px 12px; }
  .group {
    margin: 18px 10px 6px; font-size: 11px; font-weight: 650; letter-spacing: .08em; text-transform: uppercase;
    color: color-mix(in srgb, var(--sidebar-text) 55%, transparent);
  }
  .nav a, .setting {
    position: relative; display: flex; align-items: center; gap: 11px; height: 40px; padding: 0 12px; margin: 2px 0;
    border-radius: 9px; color: inherit; text-decoration: none; font-weight: 520;
    transition: background .15s, color .15s;
  }
  .nav a:hover, .setting:hover { background: color-mix(in srgb, var(--sidebar-text) 9%, transparent); }
  .nav a.active, .setting.active { background: color-mix(in srgb, var(--accent) 16%, transparent); color: #fff; }
  :global([data-sidebar='light']) .nav a.active, :global([data-sidebar='light']) .setting.active { color: var(--primary-strong); }
  .nav a.active::before, .setting.active::before {
    content: ''; position: absolute; inset-inline-start: -12px; inset-block: 9px; width: 3px; border-radius: 0 3px 3px 0; background: var(--accent);
  }
  .foot { padding: 10px 12px 14px; border-top: 1px solid color-mix(in srgb, var(--sidebar-text) 12%, transparent); }
  .prefs { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 8px 0; }
  .pref {
    display: flex; align-items: center; gap: 6px; height: 34px; padding: 0 8px; border-radius: 8px;
    background: color-mix(in srgb, var(--sidebar-text) 8%, transparent); cursor: pointer; min-width: 0;
  }
  .pref select { all: unset; flex: 1; min-width: 0; font-size: 12.5px; cursor: pointer; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pref select option { color: #111; background: #fff; }
  .user { display: flex; align-items: center; gap: 10px; padding: 6px 4px 0; font-weight: 550; }
  .ellipsis { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .avatar {
    width: 30px; height: 30px; border-radius: 50%; display: grid; place-items: center; font-size: 13px; font-weight: 700;
    background: var(--accent); color: #06302f;
  }
  .icon-btn { all: unset; cursor: pointer; padding: 6px; border-radius: 7px; display: grid; }
  .icon-btn:hover { background: color-mix(in srgb, var(--sidebar-text) 12%, transparent); }
  .scrim { display: none; }
  .quit { all: unset; box-sizing: border-box; width: 100%; cursor: pointer; }
  @media (max-width: 900px) {
    .sidebar { transform: translateX(-105%); transition: transform .2s ease; box-shadow: 0 0 40px rgb(0 0 0 / 30%); }
    :global([dir='rtl']) .sidebar { transform: translateX(105%); }
    .sidebar.open, :global([dir='rtl']) .sidebar.open { transform: none; }
    .scrim { display: block; position: fixed; inset: 0; z-index: 25; background: rgb(0 0 0 / 35%); border: 0; }
  }
</style>

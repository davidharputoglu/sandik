<script>
  import { onMount } from 'svelte'
  import { api, setUnauthorizedHandler } from './lib/api.js'
  import { app, loadSettings } from './lib/session.svelte.js'
  import { initLang, t } from './lib/i18n.svelte.js'
  import { initThemes } from './lib/theme.svelte.js'
  import { route, match } from './lib/router.svelte.js'
  import Sidebar from './components/Sidebar.svelte'
  import Toasts from './components/Toasts.svelte'
  import Icon from './components/Icon.svelte'
  import Auth from './pages/Auth.svelte'
  import Dashboard from './pages/Dashboard.svelte'
  import Clients from './pages/Clients.svelte'
  import Articles from './pages/Articles.svelte'
  import Documents from './pages/Documents.svelte'
  import DocumentEditor from './pages/DocumentEditor.svelte'
  import DocumentPrint from './pages/DocumentPrint.svelte'
  import Settings from './pages/Settings.svelte'
  import ModuleFrame from './pages/ModuleFrame.svelte'
  import Wizard from './pages/Wizard.svelte'

  let menuOpen = $state(false)
  let failed = $state(false)

  async function start() {
    try {
      app.edition = await api.get('/api/edition')
      initThemes(app.edition)
      await initLang(app.edition)
      document.title = app.edition.name
      app.auth = await api.get('/api/auth/status')
      if (!app.auth.auth_enabled || app.auth.user) await loadSettings()
      app.ready = true
    } catch {
      failed = true
    }
  }

  async function signedIn() {
    app.auth = await api.get('/api/auth/status')
    await loadSettings()
  }

  setUnauthorizedHandler(() => { if (app.auth) app.auth.user = null })
  onMount(start)

  const LISTS = { '/devis': 'quote', '/factures': 'invoice', '/avoirs': 'credit_note' }
  const needsLogin = $derived(app.auth?.auth_enabled && !app.auth?.user)
  const printing = $derived(match('/documents/:id/print'))
  const isAdmin = $derived(!app.auth?.auth_enabled || app.auth?.user?.role === 'admin')
  const needsSetup = $derived(app.settings && !app.settings.setup?.done && isAdmin)
</script>

{#if failed}
  <div class="center"><div class="alert danger">{t('errors.network')}</div></div>
{:else if !app.ready}
  <div class="center"><div class="spinner" aria-label={t('common.loading')}></div></div>
{:else if needsLogin}
  <Auth onsignedin={signedIn} />
{:else if needsSetup}
  <Wizard />
{:else if printing}
  <DocumentPrint id={printing.id} />
{:else}
  <Sidebar bind:open={menuOpen} />
  <div class="main">
    <header class="mobile-bar">
      <button class="btn ghost icon" onclick={() => (menuOpen = true)} aria-label={t('nav.menu')}><Icon name="menu" /></button>
      <img src={app.edition.assets.icon_192} alt="" width="28" height="28" />
      <strong>{app.edition.name}</strong>
    </header>
    {#key route.path + JSON.stringify(route.query)}
      {#if route.path === '/'}
        <Dashboard />
      {:else if route.path === '/clients'}
        <Clients />
      {:else if route.path === '/articles'}
        <Articles />
      {:else if LISTS[route.path]}
        <Documents type={LISTS[route.path]} />
      {:else if route.path === '/documents/new'}
        <DocumentEditor id={null} type={route.query.type || 'quote'} />
      {:else if match('/documents/:id')}
        <DocumentEditor id={match('/documents/:id').id} />
      {:else if route.path === '/parametres' || match('/parametres/:tab')}
        <Settings tab={match('/parametres/:tab')?.tab || 'company'} />
      {:else if match('/m/:module')}
        <ModuleFrame module={match('/m/:module').module} path={route.query.p} />
      {:else}
        <div class="page"><div class="empty"><h3>404</h3>{t('common.not_found')}</div></div>
      {/if}
    {/key}
  </div>
{/if}
<Toasts />

<style>
  .main { margin-inline-start: var(--sidebar-w); min-height: 100vh; }
  .mobile-bar { display: none; }
  .center { min-height: 100vh; display: grid; place-items: center; padding: 20px; }
  .spinner { width: 34px; height: 34px; border-radius: 50%; border: 3px solid var(--border); border-top-color: var(--primary); animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg) } }
  @media (max-width: 900px) {
    .main { margin-inline-start: 0; }
    .mobile-bar {
      display: flex; align-items: center; gap: 10px; padding: 8px 12px; position: sticky; top: 0; z-index: 20;
      background: var(--surface); border-bottom: 1px solid var(--border);
    }
    .mobile-bar img { border-radius: 7px; }
  }
</style>

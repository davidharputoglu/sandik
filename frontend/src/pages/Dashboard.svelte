<script>
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { t } from '../lib/i18n.svelte.js'
  import { money, date } from '../lib/format.js'
  import { go } from '../lib/router.svelte.js'
  import { app } from '../lib/session.svelte.js'
  import Icon from '../components/Icon.svelte'
  import StatusBadge from '../components/StatusBadge.svelte'

  let data = $state(null)
  onMount(async () => { data = await api.get('/api/dashboard') })
  const company = $derived(app.settings?.company)
</script>

<div class="page">
  <div class="page-head">
    <div class="grow">
      <h1>{t('dashboard.title')}</h1>
      <div class="sub">{company?.name || app.edition.name}</div>
    </div>
    <a class="btn" href="#/documents/new?type=quote"><Icon name="plus" />{t('doc.new.quote')}</a>
    <a class="btn primary" href="#/documents/new?type=invoice"><Icon name="plus" />{t('doc.new.invoice')}</a>
  </div>

  {#if company && !company.siren}
    <a class="alert info setup" href="#/parametres/company">
      <strong>{t('dashboard.setup_title')}</strong> {t('dashboard.setup_text')}
    </a>
  {/if}

  {#if data}
    <div class="kpis">
      <div class="card kpi">
        <div class="kpi-head"><Icon name="trend" />{t('dashboard.revenue', { year: data.year })}</div>
        <div class="value">{money(data.revenue_ht)}</div>
        <div class="muted small">{t('dashboard.revenue_hint')}</div>
      </div>
      <a class="card kpi" href="#/devis">
        <div class="kpi-head"><Icon name="quote" />{t('dashboard.quotes_open')}</div>
        <div class="value">{money(data.quotes_open.total_ht)}</div>
        <div class="muted small">{t('dashboard.count', { n: data.quotes_open.count })}</div>
      </a>
      <a class="card kpi" href="#/factures">
        <div class="kpi-head"><Icon name="wallet" />{t('dashboard.unpaid')}</div>
        <div class="value">{money(data.unpaid.total_ttc)}</div>
        <div class="muted small">{t('dashboard.count', { n: data.unpaid.count })}</div>
      </a>
      <a class="card kpi" class:warn={data.overdue.count > 0} href="#/factures">
        <div class="kpi-head"><Icon name="clock" />{t('dashboard.overdue')}</div>
        <div class="value">{money(data.overdue.total_ttc)}</div>
        <div class="muted small">{t('dashboard.count', { n: data.overdue.count })}</div>
      </a>
    </div>

    <section class="card">
      <div class="card-head"><h2 class="grow">{t('dashboard.recent')}</h2></div>
      {#if data.recent.length}
        <div class="table-wrap">
          <table class="table">
            <thead><tr>
              <th>{t('doc.number')}</th><th>{t('doc.type')}</th><th>{t('doc.client')}</th>
              <th>{t('doc.status')}</th><th class="num">{t('doc.total_ttc')}</th>
            </tr></thead>
            <tbody>
              {#each data.recent as d}
                <tr class="click" onclick={() => go(`/documents/${d.id}`)}>
                  <td><strong>{d.number || t('doc.draft_number')}</strong></td>
                  <td>{t(`doc.types.${d.type}`)}</td>
                  <td>{d.client_name}</td>
                  <td><StatusBadge doc={d} /></td>
                  <td class="num">{money(d.total_ttc)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {:else}
        <div class="empty"><h3>{t('dashboard.empty_title')}</h3>{t('dashboard.empty_text')}</div>
      {/if}
    </section>
  {/if}
</div>

<style>
  .setup { display: block; margin-bottom: 18px; text-decoration: none; color: var(--text); }
  .kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-bottom: 20px; }
  @media (max-width: 1100px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  @media (max-width: 560px) { .kpis { grid-template-columns: 1fr; } }
  .kpi { padding: 18px 20px; text-decoration: none; color: inherit; display: grid; gap: 6px; transition: border-color .15s, transform .15s; }
  a.kpi:hover { border-color: var(--primary); }
  .kpi-head { display: flex; gap: 8px; align-items: center; color: var(--muted); font-weight: 550; font-size: 13px; }
  .kpi-head :global(.icon) { color: var(--primary); }
  .kpi.warn .kpi-head :global(.icon) { color: var(--warning); }
  .value { font-family: var(--font-head); font-size: 26px; font-weight: 650; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
</style>

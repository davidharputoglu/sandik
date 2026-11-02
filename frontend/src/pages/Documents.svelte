<script>
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { t } from '../lib/i18n.svelte.js'
  import { money, date } from '../lib/format.js'
  import { go } from '../lib/router.svelte.js'
  import { app } from '../lib/session.svelte.js'
  import Icon from '../components/Icon.svelte'
  import StatusBadge from '../components/StatusBadge.svelte'

  let { type } = $props()
  const STATUSES = { quote: ['draft', 'sent', 'accepted', 'refused'], invoice: ['draft', 'issued', 'paid'], credit_note: ['draft', 'issued'] }
  let items = $state([])
  let status = $state('')
  let q = $state('')
  app.currentDocType = type

  async function load() {
    items = await api.get(`/api/documents?type=${type}&status=${status}&q=${encodeURIComponent(q)}`)
  }
  onMount(load)
  let timer
  function search() { clearTimeout(timer); timer = setTimeout(load, 200) }
  const totals = $derived(items.reduce((s, d) => s + Number(d.total_ht), 0))
</script>

<div class="page">
  <div class="page-head">
    <div class="grow"><h1>{t(`doc.plural.${type}`)}</h1><div class="sub">{t(`doc.subtitle.${type}`)}</div></div>
    {#if type !== 'credit_note'}
      <a class="btn primary" href={`#/documents/new?type=${type}`}><Icon name="plus" />{t(`doc.new.${type}`)}</a>
    {/if}
  </div>

  <section class="card">
    <div class="card-head wrap">
      <div class="tabs" role="tablist">
        <button role="tab" class:on={status === ''} onclick={() => { status = ''; load() }}>{t('common.all')}</button>
        {#each STATUSES[type] as s}
          <button role="tab" class:on={status === s} onclick={() => { status = s; load() }}>{t(`status.${type}.${s}`)}</button>
        {/each}
      </div>
      <span class="grow"></span>
      <label class="search"><Icon name="search" size={16} />
        <input class="input" placeholder={t('common.search')} bind:value={q} oninput={search} /></label>
    </div>
    {#if items.length}
      <div class="table-wrap"><table class="table">
        <thead><tr>
          <th>{t('doc.number')}</th><th>{t('doc.client')}</th><th>{t('doc.title')}</th><th>{t('doc.issue_date')}</th>
          <th>{type === 'quote' ? t('doc.valid_until') : t('doc.due_date')}</th><th>{t('doc.status')}</th>
          <th class="num">{t('doc.total_ht')}</th><th class="num">{t('doc.total_ttc')}</th>
        </tr></thead>
        <tbody>
          {#each items as d (d.id)}
            <tr class="click" onclick={() => go(`/documents/${d.id}`)}>
              <td><strong>{d.number || t('doc.draft_number')}</strong></td>
              <td>{d.client_name}</td>
              <td class="muted clip">{d.title}</td>
              <td>{date(d.issue_date)}</td>
              <td>{date(type === 'quote' ? d.valid_until : d.due_date)}</td>
              <td><StatusBadge doc={d} /></td>
              <td class="num">{money(d.total_ht)}</td>
              <td class="num"><strong>{money(d.total_ttc)}</strong></td>
            </tr>
          {/each}
        </tbody>
        <tfoot><tr><td colspan="6" class="muted small">{t('dashboard.count', { n: items.length })}</td>
          <td class="num"><strong>{money(totals)}</strong></td><td></td></tr></tfoot>
      </table></div>
    {:else}
      <div class="empty"><h3>{t(`doc.empty.${type}`)}</h3>{t(`doc.empty_hint.${type}`)}</div>
    {/if}
  </section>
</div>

<style>
  .tabs { display: flex; gap: 2px; padding: 3px; border-radius: 9px; background: var(--surface-2); flex-wrap: wrap; }
  .tabs button { all: unset; padding: 6px 12px; border-radius: 7px; cursor: pointer; font-weight: 550; color: var(--muted); font-size: 13px; }
  .tabs button.on { background: var(--surface); color: var(--text); box-shadow: var(--shadow); }
  .search { position: relative; display: block; width: 260px; max-width: 100%; }
  .search :global(.icon) { position: absolute; inset-inline-start: 11px; top: 50%; transform: translateY(-50%); color: var(--muted); }
  .search .input { padding-inline-start: 34px; }
  .clip { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  tfoot td { height: 44px; padding: 0 var(--pad); border-top: 1px solid var(--border); }
</style>

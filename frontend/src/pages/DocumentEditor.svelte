<script>
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { t, errorText, errorDetails } from '../lib/i18n.svelte.js'
  import { money, percent, date, today, toNumber } from '../lib/format.js'
  import { go, route } from '../lib/router.svelte.js'
  import { app, vatRates, units, vatExempt } from '../lib/session.svelte.js'
  import { toast } from '../lib/toast.svelte.js'
  import Icon from '../components/Icon.svelte'
  import Modal from '../components/Modal.svelte'
  import StatusBadge from '../components/StatusBadge.svelte'
  import CustomFields from '../components/CustomFields.svelte'

  let { id = null, type: newType = 'quote' } = $props()
  const LIST = { quote: '/devis', invoice: '/factures', credit_note: '/avoirs' }
  const ACTION_UI = {
    send: { icon: 'send' }, accept: { icon: 'check' }, refuse: { icon: 'x' }, reopen: { icon: 'edit' },
    to_invoice: { icon: 'invoice', primary: true }, issue: { icon: 'check', primary: true },
    mark_paid: { icon: 'wallet', primary: true }, mark_unpaid: { icon: 'clock' },
    credit_note: { icon: 'credit' }, duplicate: { icon: 'copy' },
  }

  let doc = $state(null)
  let clients = $state([])
  let articles = $state([])
  let fields = $state([])
  let error = $state(null)
  let dirty = $state(false)
  let saving = $state(false)
  let picker = $state(false)
  let pickerQ = $state('')
  let issuing = $state(false)
  let issueDate = $state(today())

  const newLine = (kind = 'item') => ({
    kind, article_id: null, reference: '', label: '', description: '', quantity: '1', unit: kind === 'item' ? units()[0] : '',
    unit_price: '0', discount_percent: '0', vat_rate: vatExempt() ? '0' : app.settings.vat.default_rate || '20',
  })

  function blank(type, clientId) {
    const s = app.settings.documents
    return {
      id: null, type, status: 'draft', number: null, client_id: clientId ? Number(clientId) : null, title: '',
      issue_date: type === 'quote' ? today() : null, valid_until: null, due_date: null,
      operation_nature: s.default_operation_nature, vat_on_debits: s.vat_on_debits,
      vat_exemption_text: vatExempt() ? app.settings.vat.franchise_text : '', delivery_address: '',
      intro: type === 'quote' ? s.quote_intro : '', notes: '', terms: '', extra: {}, lines: [newLine()],
      editable: true, actions: [], vat_breakdown: [],
    }
  }

  onMount(async () => {
    ;[clients, articles, fields] = await Promise.all([
      api.get('/api/clients'), api.get('/api/articles'), api.get('/api/custom-fields?entity=document'),
    ])
    doc = id ? await api.get(`/api/documents/${id}`) : blank(newType, route.query.client)
    app.currentDocType = doc.type
  })

  const ro = $derived(!doc?.editable)
  const r2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100
  const lineTotal = (l) => (l.kind !== 'item' ? 0 : r2((toNumber(l.quantity) * toNumber(l.unit_price) * (100 - toNumber(l.discount_percent))) / 100))
  const totals = $derived.by(() => {
    const bases = {}
    for (const l of doc?.lines || []) if (l.kind === 'item') bases[toNumber(l.vat_rate)] = (bases[toNumber(l.vat_rate)] || 0) + lineTotal(l)
    const rates = Object.keys(bases).map(Number).sort((a, b) => b - a)
    const breakdown = rates.map((r) => ({ rate: r, base: r2(bases[r]), vat: r2((r2(bases[r]) * r) / 100) }))
    const ht = r2(breakdown.reduce((s, b) => s + b.base, 0))
    const vat = r2(breakdown.reduce((s, b) => s + b.vat, 0))
    return { ht, vat, ttc: r2(ht + vat), breakdown }
  })
  const client = $derived(clients.find((c) => c.id === doc?.client_id) || doc?.client)
  const filtered = $derived(articles.filter((a) => `${a.reference} ${a.label}`.toLowerCase().includes(pickerQ.toLowerCase())))
  const heading = $derived(doc ? (doc.id ? `${t(`doc.types.${doc.type}`)} ${doc.number || t('doc.draft_number').toLowerCase()}` : t(`doc.new.${doc.type}`)) : '')

  const touch = () => (dirty = true)
  function addLine(kind) { doc.lines.push(newLine(kind)); touch() }
  function addArticle(a) {
    doc.lines.push({ ...newLine(), article_id: a.id, reference: a.reference, label: a.label, description: a.description,
      unit: a.unit, unit_price: a.unit_price, vat_rate: vatExempt() ? '0' : a.vat_rate })
    picker = false; pickerQ = ''; touch()
  }
  function move(i, d) {
    const j = i + d
    if (j < 0 || j >= doc.lines.length) return
    const [l] = doc.lines.splice(i, 1)
    doc.lines.splice(j, 0, l); touch()
  }
  function removeLine(i) { doc.lines.splice(i, 1); touch() }

  function payload() {
    const d = $state.snapshot(doc)
    const keys = ['client_id', 'title', 'valid_until', 'due_date', 'operation_nature', 'vat_on_debits', 'vat_exemption_text',
      'delivery_address', 'intro', 'notes', 'terms', 'extra']
    const body = Object.fromEntries(keys.map((k) => [k, d[k] === '' && k.endsWith('_date') ? null : d[k]]))
    if (d.type === 'quote') body.issue_date = d.issue_date || null
    body.valid_until ||= null
    body.due_date ||= null
    body.type = d.type
    body.lines = d.lines.map(({ id: _i, total_ht: _t, position: _p, ...l }) => l)
    return body
  }

  function showError(err) { error = { text: errorText(err), details: errorDetails(err) } }

  async function save() {
    error = null
    if (!doc.client_id) { error = { text: t('errors.doc.client_required'), details: [] }; return false }
    saving = true
    try {
      const saved = doc.id ? await api.put(`/api/documents/${doc.id}`, payload()) : await api.post('/api/documents', payload())
      const created = !doc.id
      doc = saved; dirty = false
      toast(t('common.saved'))
      if (created) history.replaceState(null, '', `#/documents/${saved.id}`)
      return true
    } catch (err) { showError(err); return false } finally { saving = false }
  }

  async function act(action) {
    if (doc.editable && (dirty || !doc.id) && !(await save())) return
    if (action === 'issue') { issueDate = today(); issuing = true; return }
    await run(action, action === 'mark_paid' ? { paid_at: today() } : {})
  }

  async function run(action, params = {}) {
    error = null
    try {
      const res = await api.post(`/api/documents/${doc.id}/actions/${action}`, params)
      issuing = false
      if (res.id !== doc.id) { toast(t(`doc.done.${action}`)); go(`/documents/${res.id}`) }
      else { doc = res; toast(t(`doc.done.${action}`)) }
    } catch (err) { issuing = false; showError(err) }
  }

  async function remove() {
    if (!confirm(t('doc.confirm_delete'))) return
    await api.del(`/api/documents/${doc.id}`)
    toast(t('common.deleted'))
    go(LIST[doc.type])
  }
</script>

{#if doc}
<div class="page">
  <div class="page-head">
    <a class="btn ghost icon" href={'#' + LIST[doc.type]} aria-label={t('common.back')}><Icon name="back" class="flip" /></a>
    <div class="grow">
      <div class="row"><h1>{heading}</h1>{#if doc.id}<StatusBadge {doc} />{/if}</div>
      {#if doc.title}<div class="sub">{doc.title}</div>{/if}
    </div>
    {#if doc.id}
      <a class="btn" href={`#/documents/${doc.id}/print`}><Icon name="print" />{t('doc.print')}</a>
    {/if}
    {#each (doc.actions || []).filter((a) => ACTION_UI[a]) as a}
      <button class="btn" class:primary={ACTION_UI[a].primary} onclick={() => act(a)}><Icon name={ACTION_UI[a].icon} size={16} />{t(`actions.${a}`)}</button>
    {/each}
    {#if doc.editable}
      <button class="btn primary" onclick={save} disabled={saving}><Icon name="check" size={16} />{t('common.save')}</button>
    {/if}
  </div>

  {#if error}
    <div class="alert danger block"><strong>{error.text}</strong>
      {#if error.details.length}<ul>{#each error.details as d}<li>{d}</li>{/each}</ul>{/if}</div>
  {/if}
  {#if !doc.editable && doc.type !== 'quote'}
    <div class="alert info block">{t('doc.locked_info')}</div>
  {/if}

  <div class="layout">
      <section class="card card-body grid-2 info">
        <label class="field span-2"><span>{t('doc.client')} *</span>
          <select class="input" bind:value={doc.client_id} onchange={touch} disabled={ro}>
            <option value={null}>{t('doc.choose_client')}</option>
            {#each clients as c}<option value={c.id}>{c.name}{c.city ? ` — ${c.city}` : ''}</option>{/each}
          </select>
          {#if !clients.length}<small class="hint"><a href="#/clients">{t('doc.no_client_hint')}</a></small>{/if}
        </label>
        {#if client}
          <div class="client span-2 muted small">
            {[client.address_line1, client.address_line2, [client.postal_code, client.city].filter(Boolean).join(' ')].filter(Boolean).join(' · ')}
            {#if client.siren} · SIREN {client.siren}{/if}
          </div>
        {/if}
        <label class="field span-2"><span>{t('doc.title')}</span>
          <input class="input" bind:value={doc.title} oninput={touch} readonly={ro} placeholder={t('doc.title_placeholder')} /></label>
        {#if doc.type === 'quote'}
          <label class="field"><span>{t('doc.issue_date')}</span><input class="input" type="date" bind:value={doc.issue_date} oninput={touch} readonly={ro} /></label>
          <label class="field"><span>{t('doc.valid_until')}</span><input class="input" type="date" bind:value={doc.valid_until} oninput={touch} readonly={ro} /></label>
        {:else}
          <label class="field"><span>{t('doc.issue_date')}</span>
            <input class="input" value={doc.issue_date ? date(doc.issue_date) : t('doc.on_issue')} readonly /></label>
          <label class="field"><span>{t('doc.due_date')}</span><input class="input" type="date" bind:value={doc.due_date} oninput={touch} readonly={ro} />
            {#if !doc.due_date && !ro}<small class="hint">{t('doc.due_auto', { days: app.settings.documents.payment_terms_days })}</small>{/if}</label>
        {/if}
        <label class="field span-2"><span>{t('doc.intro')}</span>
          <textarea class="input" rows="2" bind:value={doc.intro} oninput={touch} readonly={ro}></textarea></label>
      </section>

    <aside class="stack">
      <section class="card totals">
        <div class="t-row"><span>{t('doc.total_ht')}</span><span class="num">{money(totals.ht)}</span></div>
        {#each totals.breakdown as b}
          <div class="t-row muted"><span>{t('doc.vat_at', { rate: percent(b.rate) })}</span><span class="num">{money(b.vat)}</span></div>
        {/each}
        <div class="t-row ttc"><span>{t('doc.total_ttc')}</span><span class="num">{money(totals.ttc)}</span></div>
        {#if doc.vat_exemption_text}<div class="muted small exempt">{doc.vat_exemption_text}</div>{/if}
      </section>


      {#if doc.id && (doc.actions.includes('delete') || doc.integrity_hash)}
        <section class="card card-body stack small">
          {#if doc.integrity_hash}
            <div><strong>{t('doc.integrity')}</strong><div class="muted hash">{doc.integrity_hash}</div></div>
          {/if}
          {#if doc.actions.includes('delete')}
            <button class="btn danger sm" onclick={remove}><Icon name="trash" size={15} />{t('doc.delete')}</button>
          {/if}
        </section>
      {/if}
    </aside>
    <div class="full stack">
      <section class="card">
        <div class="card-head"><h2 class="grow">{t('doc.lines')}</h2></div>
        <div class="table-wrap">
          <table class="lines" class:ro>
            <thead><tr>
              <th class="w-desc">{t('doc.line.label')}</th><th class="w-qty num">{t('doc.line.qty')}</th><th class="w-unit">{t('doc.line.unit')}</th>
              <th class="w-price num">{t('doc.line.unit_price')}</th><th class="w-disc num">{t('doc.line.discount')}</th>
              <th class="w-vat num">{t('doc.line.vat')}</th><th class="w-total num">{t('doc.line.total')}</th>{#if !ro}<th class="w-tools"></th>{/if}
            </tr></thead>
            <tbody>
              {#each doc.lines as line, i}
                <tr class={line.kind}>
                  {#if line.kind === 'item'}
                    <td>
                      <input class="input strong" bind:value={line.label} oninput={touch} readonly={ro} placeholder={t('doc.line.label_placeholder')} />
                      {#if !ro || line.description}
                        <textarea class="input desc" rows="1" bind:value={line.description} oninput={touch} readonly={ro} placeholder={t('doc.line.description')}></textarea>
                      {/if}
                    </td>
                    <td><input class="input num" inputmode="decimal" bind:value={line.quantity} oninput={touch} readonly={ro} /></td>
                    <td><input class="input" list="units-list" bind:value={line.unit} oninput={touch} readonly={ro} /></td>
                    <td><input class="input num" inputmode="decimal" bind:value={line.unit_price} oninput={touch} readonly={ro} /></td>
                    <td><input class="input num" inputmode="decimal" bind:value={line.discount_percent} oninput={touch} readonly={ro} /></td>
                    <td><select class="input num" bind:value={line.vat_rate} onchange={touch} disabled={ro || vatExempt()}>
                      {#each vatRates() as r}<option value={r}>{percent(r)}</option>{/each}
                      {#if !vatRates().includes(String(line.vat_rate))}<option value={line.vat_rate}>{percent(line.vat_rate)}</option>{/if}
                    </select></td>
                    <td class="num total">{money(lineTotal(line))}</td>
                  {:else if line.kind === 'section'}
                    <td colspan="7"><input class="input section-input" bind:value={line.label} oninput={touch} readonly={ro} placeholder={t('doc.line.section_placeholder')} /></td>
                  {:else}
                    <td colspan="7"><textarea class="input" rows="2" bind:value={line.description} oninput={touch} readonly={ro} placeholder={t('doc.line.text_placeholder')}></textarea></td>
                  {/if}
                  {#if !ro}
                    <td class="tools">
                      <button class="mini" onclick={() => move(i, -1)} aria-label={t('doc.line.up')}><Icon name="up" size={14} /></button>
                      <button class="mini" onclick={() => move(i, 1)} aria-label={t('doc.line.down')}><Icon name="down" size={14} /></button>
                      <button class="mini danger" onclick={() => removeLine(i)} aria-label={t('common.delete')}><Icon name="trash" size={14} /></button>
                    </td>
                  {/if}
                </tr>
              {/each}
            </tbody>
          </table>
          <datalist id="units-list">{#each units() as u}<option value={u}></option>{/each}</datalist>
        </div>
        {#if !ro}
          <div class="add row wrap">
            <button class="btn sm" onclick={() => addLine('item')}><Icon name="plus" size={15} />{t('doc.add_line')}</button>
            <button class="btn sm" onclick={() => (picker = true)}><Icon name="box" size={15} />{t('doc.from_catalog')}</button>
            <button class="btn sm ghost" onclick={() => addLine('section')}><Icon name="section" size={15} />{t('doc.add_section')}</button>
            <button class="btn sm ghost" onclick={() => addLine('text')}><Icon name="text" size={15} />{t('doc.add_text')}</button>
          </div>
        {/if}
      </section>

    </div>
      <section class="card card-body notes-card">
        <label class="field"><span>{t('doc.notes')}</span><textarea class="input" bind:value={doc.notes} oninput={touch} readonly={ro}></textarea></label>
      </section>
      <section class="card card-body stack">
        <h3>{t('doc.options')}</h3>
        <label class="field"><span>{t('doc.operation_nature')}</span>
          <select class="input" bind:value={doc.operation_nature} onchange={touch} disabled={ro}>
            {#each ['services', 'goods', 'mixed'] as n}<option value={n}>{t(`doc.nature.${n}`)}</option>{/each}
          </select></label>
        <label class="check small"><input type="checkbox" bind:checked={doc.vat_on_debits} onchange={touch} disabled={ro} />{t('doc.vat_on_debits')}</label>
        <label class="field"><span>{t('doc.vat_exemption')}</span>
          <input class="input" bind:value={doc.vat_exemption_text} oninput={touch} readonly={ro} placeholder={t('doc.vat_exemption_placeholder')} /></label>
        <label class="field"><span>{t('doc.delivery_address')}</span>
          <textarea class="input" rows="2" bind:value={doc.delivery_address} oninput={touch} readonly={ro}></textarea></label>
        {#if doc.type !== 'quote'}
          <label class="field"><span>{t('doc.terms')}</span>
            <textarea class="input" rows="4" bind:value={doc.terms} oninput={touch} readonly={ro} placeholder={t('doc.terms_auto')}></textarea></label>
        {/if}
        <CustomFields {fields} bind:values={doc.extra} readonly={ro} />
      </section>
  </div>
</div>

{#if picker}
  <Modal title={t('doc.from_catalog')} onclose={() => (picker = false)}>
    <input class="input" placeholder={t('common.search')} bind:value={pickerQ} />
    <div class="pick">
      {#each filtered as a (a.id)}
        <button class="pick-row" onclick={() => addArticle(a)}>
          <span class="grow"><strong>{a.label}</strong> <span class="muted small">{a.reference}</span></span>
          <span class="num">{money(a.unit_price)} / {a.unit}</span>
        </button>
      {:else}
        <div class="empty">{t('articles.empty_title')} — <a href="#/articles">{t('articles.new')}</a></div>
      {/each}
    </div>
  </Modal>
{/if}

{#if issuing}
  <Modal title={t(`doc.issue_title.${doc.type}`)} onclose={() => (issuing = false)} width="480px">
    <div class="stack">
      <p class="muted">{t('doc.issue_text')}</p>
      <label class="field"><span>{t('doc.issue_date')}</span><input class="input" type="date" bind:value={issueDate} /></label>
    </div>
    {#snippet footer()}
      <button class="btn" onclick={() => (issuing = false)}>{t('common.cancel')}</button>
      <button class="btn primary" onclick={() => run('issue', { issue_date: issueDate })}><Icon name="check" size={16} />{t('actions.issue')}</button>
    {/snippet}
  </Modal>
{/if}
{/if}

<style>
  .block { margin-bottom: 16px; }
  .layout { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 18px; align-items: start; }
  .full { grid-column: 1 / -1; }
  .info { align-self: stretch; }
  @media (max-width: 1100px) { .layout { grid-template-columns: 1fr; } }
  .client { margin-top: -6px; }
  .lines { width: 100%; border-collapse: collapse; min-width: 760px; }
  .lines th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 600;
    text-align: start; padding: 10px 6px; border-bottom: 1px solid var(--border); }
  .lines th:first-child, .lines td:first-child { padding-inline-start: var(--pad); }
  .lines td { padding: 6px; vertical-align: top; border-bottom: 1px solid var(--border); }
  .lines th.num { text-align: end; }
  .w-qty { width: 88px; } .w-unit { width: 92px; } .w-price { width: 120px; } .w-disc { width: 76px; }
  .w-vat { width: 116px; } .w-total { width: 120px; } .w-tools { width: 92px; }
  .lines .input { height: 34px; }
  .lines .strong { font-weight: 550; }
  .lines .desc { margin-top: 5px; min-height: 34px; font-size: 13px; color: var(--muted); }
  .lines td.total { padding-top: 14px; font-weight: 600; }
  .lines tr.section td { background: var(--surface-2); }
  .section-input { font-family: var(--font-head); font-weight: 650; background: transparent; }
  .lines.ro .input { border-color: transparent; background: transparent; padding-inline: 4px; opacity: 1; color: var(--text); }
  .lines.ro select.input { appearance: none; }
  .tools { white-space: nowrap; padding-top: 9px !important; }
  .mini { all: unset; display: inline-grid; place-items: center; width: 26px; height: 26px; border-radius: 6px; cursor: pointer; color: var(--muted); }
  .mini:hover { background: var(--surface-2); color: var(--text); }
  .mini.danger:hover { background: var(--danger-soft); color: var(--danger); }
  .add { padding: 12px var(--pad); gap: 8px; }
  .totals { padding: 16px var(--pad); display: grid; gap: 8px; }
  .t-row { display: flex; justify-content: space-between; gap: 12px; }
  .t-row.ttc { font-family: var(--font-head); font-size: 20px; font-weight: 700; padding-top: 10px; border-top: 1px solid var(--border); }
  .exempt { font-style: italic; }
  .hash { font-family: ui-monospace, monospace; font-size: 11px; word-break: break-all; }
  .pick { display: grid; margin-top: 12px; max-height: 50vh; overflow-y: auto; }
  .pick-row { all: unset; display: flex; gap: 12px; align-items: center; padding: 10px 8px; border-radius: 8px; cursor: pointer; }
  .pick-row:hover { background: var(--surface-2); }
  input[readonly]:not([type='date']), textarea[readonly] { background: var(--surface-2); }
  .lines.ro input[readonly], .lines.ro textarea[readonly] { background: transparent; }
</style>

<!-- SPDX-License-Identifier: AGPL-3.0-or-later — Copyright (C) 2026 David HARPUTOGLU -->
<script>
  // Aperçu imprimable (A4). « Imprimer » → « Enregistrer en PDF » dans la fenêtre d'impression.
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { t } from '../lib/i18n.svelte.js'
  import { money, number, percent, date } from '../lib/format.js'
  import { app } from '../lib/session.svelte.js'
  import { themes } from '../lib/theme.svelte.js'
  import Icon from '../components/Icon.svelte'

  let { id } = $props()
  let doc = $state(null)
  onMount(async () => { doc = await api.get(`/api/documents/${id}`) })

  const issuer = $derived(doc?.issuer || app.settings.company)
  const c = $derived(doc?.client || {})
  const look = $derived(app.settings.appearance)
  const accent = $derived(look.document_accent || (themes.list.find((th) => th.mode === 'light') || themes.active)?.primary_strong || '#0b8079')
  const hasDiscount = $derived(doc?.lines.some((l) => l.kind === 'item' && Number(l.discount_percent) > 0))
  const footer = $derived(doc?.type === 'quote' ? app.settings.documents.quote_footer : app.settings.documents.invoice_footer)
  const legal = $derived([
    issuer.name && issuer.legal_form ? `${issuer.name} — ${issuer.legal_form}` : issuer.name,
    issuer.capital && t('print.capital', { capital: issuer.capital }),
    issuer.siren && `SIREN ${issuer.siren}`, issuer.siret && `SIRET ${issuer.siret}`,
    issuer.rcs && `RCS ${issuer.rcs}`, issuer.ape && `APE ${issuer.ape}`,
    issuer.vat_number && `${t('print.vat_number')} ${issuer.vat_number}`,
  ].filter(Boolean).join(' · '))
</script>

{#if doc}
  <div class="toolbar">
    <a class="btn" href={`#/documents/${doc.id}`}><Icon name="back" class="flip" />{t('common.back')}</a>
    <span class="grow muted small">{t('print.hint')}</span>
    <button class="btn primary" onclick={() => window.print()}><Icon name="print" />{t('doc.print')}</button>
  </div>

  <article class="sheet" style:--accent={accent}>
    {#if doc.status === 'draft' && doc.type !== 'quote'}<div class="watermark">{t('print.draft')}</div>{/if}
    <header class="top">
      <div class="issuer">
        {#if look.show_logo_on_documents && app.settings.company.has_logo}
          <img class="logo" src="/api/company/logo" alt={issuer.name} />
        {/if}
        <strong class="name">{issuer.name}</strong>
        <div>{issuer.address_line1}</div>
        {#if issuer.address_line2}<div>{issuer.address_line2}</div>{/if}
        <div>{issuer.postal_code} {issuer.city}</div>
        {#if issuer.phone}<div>{issuer.phone}</div>{/if}
        {#if issuer.email}<div>{issuer.email}</div>{/if}
      </div>
      <div class="meta">
        <h1>{t(`print.title.${doc.type}`)}</h1>
        <div class="number">{doc.number ? `${t('print.number')} ${doc.number}` : t('print.draft')}</div>
        <dl>
          {#if doc.issue_date}<dt>{t('print.date')}</dt><dd>{date(doc.issue_date)}</dd>{/if}
          {#if doc.type === 'quote' && doc.valid_until}<dt>{t('print.valid_until')}</dt><dd>{date(doc.valid_until)}</dd>{/if}
          {#if doc.type === 'invoice' && doc.due_date}<dt>{t('print.due_date')}</dt><dd>{date(doc.due_date)}</dd>{/if}
        </dl>
      </div>
    </header>

    <section class="parties">
      <div class="client-box">
        <div class="label">{t('print.client')}</div>
        <strong>{c.name}</strong>
        {#if c.contact_name}<div>{c.contact_name}</div>{/if}
        <div>{c.address_line1}</div>
        {#if c.address_line2}<div>{c.address_line2}</div>{/if}
        <div>{c.postal_code} {c.city}{c.country && c.country !== 'FR' ? ` — ${c.country}` : ''}</div>
        {#if c.siren}<div class="small">SIREN {c.siren}</div>{/if}
        {#if c.vat_number}<div class="small">{t('print.vat_number')} {c.vat_number}</div>{/if}
      </div>
      {#if doc.delivery_address}
        <div class="client-box"><div class="label">{t('print.delivery_address')}</div><div class="pre">{doc.delivery_address}</div></div>
      {/if}
    </section>

    {#if doc.title}<h2 class="subject">{doc.title}</h2>{/if}
    {#if doc.intro}<p class="pre">{doc.intro}</p>{/if}

    <table class="items">
      <thead><tr>
        <th>{t('print.description')}</th><th class="num">{t('print.qty')}</th><th>{t('print.unit')}</th>
        <th class="num">{t('print.unit_price')}</th>{#if hasDiscount}<th class="num">{t('print.discount')}</th>{/if}
        <th class="num">{t('print.vat')}</th><th class="num">{t('print.total_ht')}</th>
      </tr></thead>
      <tbody>
        {#each doc.lines as l}
          {#if l.kind === 'section'}
            <tr class="section"><td colspan={hasDiscount ? 7 : 6}>{l.label}</td></tr>
          {:else if l.kind === 'text'}
            <tr class="text"><td colspan={hasDiscount ? 7 : 6} class="pre">{l.description}</td></tr>
          {:else}
            <tr>
              <td><div class="lbl">{l.label}</div>{#if l.description}<div class="desc pre">{l.description}</div>{/if}</td>
              <td class="num">{number(l.quantity)}</td><td>{l.unit}</td>
              <td class="num">{money(l.unit_price)}</td>{#if hasDiscount}<td class="num">{Number(l.discount_percent) ? percent(l.discount_percent) : ''}</td>{/if}
              <td class="num">{percent(l.vat_rate)}</td><td class="num">{money(l.total_ht)}</td>
            </tr>
          {/if}
        {/each}
      </tbody>
    </table>

    <section class="bottom">
      <div class="mentions">
        <div>{t('print.operation')} : {t(`doc.nature.${doc.operation_nature}`)}</div>
        {#if doc.vat_on_debits}<div>{t('print.vat_debits')}</div>{/if}
        {#if doc.vat_exemption_text}<div><strong>{doc.vat_exemption_text}</strong></div>{/if}
        {#if issuer.insurance}<div class="pre">{t('print.insurance')} : {issuer.insurance}</div>{/if}
      </div>
      <table class="totals">
        <tbody>
          <tr><td>{t('print.total_ht')}</td><td class="num">{money(doc.total_ht)}</td></tr>
          {#each doc.vat_breakdown as b}
            <tr class="vat"><td>{t('print.vat_line', { rate: percent(b.rate), base: money(b.base) })}</td><td class="num">{money(b.vat)}</td></tr>
          {/each}
          <tr class="ttc"><td>{doc.type === 'credit_note' ? t('print.total_credit') : t('print.total_ttc')}</td><td class="num">{money(doc.total_ttc)}</td></tr>
        </tbody>
      </table>
    </section>

    {#if doc.notes}<p class="pre notes">{doc.notes}</p>{/if}
    {#if doc.type !== 'quote' && doc.terms}<div class="terms pre">{doc.terms}</div>{/if}
    {#if doc.type === 'invoice' && issuer.iban}
      <div class="bank"><strong>{t('print.bank')}</strong> — {issuer.bank_name ? `${issuer.bank_name} · ` : ''}IBAN {issuer.iban}{issuer.bic ? ` · BIC ${issuer.bic}` : ''}</div>
    {/if}
    {#if doc.type === 'quote'}
      <div class="sign"><div class="label">{t('print.signature')}</div><div class="box"></div></div>
    {/if}
    {#if footer}<p class="pre small footer-text">{footer}</p>{/if}

    <footer class="legal">{legal}</footer>
  </article>
{/if}

<style>
  :global(body) { background: var(--bg); }
  .toolbar { position: sticky; top: 0; z-index: 5; display: flex; gap: 12px; align-items: center; padding: 10px 20px; background: var(--surface); border-bottom: 1px solid var(--border); }
  .sheet {
    position: relative; width: 210mm; min-height: 297mm; margin: 24px auto; padding: 16mm 15mm 22mm; background: #fff; color: #1d262d;
    box-shadow: 0 4px 30px rgb(0 0 0 / 15%); font-size: 10pt; line-height: 1.45; font-family: var(--font-body);
  }
  .top { display: flex; justify-content: space-between; gap: 24px; }
  .logo { max-width: 52mm; max-height: 22mm; object-fit: contain; display: block; margin-bottom: 4mm; }
  .issuer .name { font-size: 12pt; }
  .meta { text-align: end; }
  .meta h1 { font-family: var(--font-head); font-size: 22pt; letter-spacing: .06em; color: var(--accent); }
  .number { font-weight: 700; font-size: 11pt; margin-top: 1mm; }
  dl { display: grid; grid-template-columns: auto auto; gap: 1mm 4mm; justify-content: end; margin: 3mm 0 0; }
  dt { color: #66737d; } dd { margin: 0; font-weight: 600; }
  .parties { display: flex; justify-content: flex-end; gap: 6mm; margin: 9mm 0 7mm; }
  .client-box { min-width: 78mm; padding: 4mm 5mm; border-radius: 3mm; background: #f4f7f7; border-inline-start: 1.2mm solid var(--accent); }
  .label { font-size: 8pt; text-transform: uppercase; letter-spacing: .08em; color: #66737d; margin-bottom: 1mm; }
  .subject { font-family: var(--font-head); font-size: 12pt; margin: 0 0 2mm; }
  .pre { white-space: pre-line; }
  .items { width: 100%; border-collapse: collapse; margin-top: 4mm; }
  .items th { background: var(--accent); color: #fff; font-weight: 600; font-size: 8.5pt; text-align: start; padding: 2.2mm 2mm; }
  .items th.num, .items td.num { text-align: end; }
  .items td { padding: 2.2mm 2mm; border-bottom: .2mm solid #e1e7ea; vertical-align: top; }
  .items .desc { color: #5c6870; font-size: 9pt; }
  .items .lbl { font-weight: 550; }
  .items tr.section td { font-weight: 700; background: #f0f4f5; color: var(--accent); }
  .items tr.text td { color: #4a565e; }
  .bottom { display: flex; justify-content: space-between; gap: 10mm; margin-top: 6mm; align-items: flex-start; }
  .mentions { font-size: 9pt; color: #47535b; display: grid; gap: 1mm; }
  .totals { border-collapse: collapse; min-width: 72mm; }
  .totals td { padding: 1.6mm 2mm; }
  .totals tr.vat td { color: #5c6870; font-size: 9pt; }
  .totals tr.ttc td { font-weight: 800; font-size: 12pt; border-top: .4mm solid var(--accent); color: var(--accent); }
  .notes, .terms, .bank { margin-top: 6mm; font-size: 9pt; }
  .terms { color: #47535b; }
  .sign { margin-top: 8mm; margin-inline-start: auto; width: 80mm; }
  .sign .box { height: 28mm; border: .3mm dashed #9aa6ae; border-radius: 2mm; }
  .footer-text { color: #5c6870; margin-top: 6mm; }
  .legal { position: absolute; inset-inline: 15mm; bottom: 9mm; text-align: center; font-size: 7.5pt; color: #7a868e; border-top: .2mm solid #e1e7ea; padding-top: 2mm; }
  .watermark { position: absolute; inset: 0; display: grid; place-items: center; font-size: 80pt; font-weight: 800; color: rgb(200 40 40 / 8%); transform: rotate(-30deg); pointer-events: none; }
  .small { font-size: 8.5pt; }
  @media print {
    @page { size: A4; margin: 0; }
    :global(body) { background: #fff; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
</style>

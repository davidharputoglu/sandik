<script>
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { t, errorText } from '../lib/i18n.svelte.js'
  import { toast } from '../lib/toast.svelte.js'
  import { go } from '../lib/router.svelte.js'
  import Icon from '../components/Icon.svelte'
  import Modal from '../components/Modal.svelte'
  import CustomFields from '../components/CustomFields.svelte'

  const EMPTY = { kind: 'company', name: '', contact_name: '', email: '', phone: '', siren: '', vat_number: '',
    address_line1: '', address_line2: '', postal_code: '', city: '', country: 'FR', notes: '', extra: {} }

  let items = $state([])
  let fields = $state([])
  let q = $state('')
  let archived = $state(false)
  let editing = $state(null)
  let error = $state('')

  async function load() { items = await api.get(`/api/clients?archived=${archived}&q=${encodeURIComponent(q)}`) }
  onMount(async () => { fields = await api.get('/api/custom-fields?entity=client'); load() })

  function open(c) { error = ''; editing = structuredClone($state.snapshot(c || EMPTY)) }

  async function save(e) {
    e?.preventDefault()
    try {
      const body = $state.snapshot(editing)
      editing.id ? await api.put(`/api/clients/${editing.id}`, body) : await api.post('/api/clients', body)
      toast(t('common.saved'))
      editing = null
      load()
    } catch (err) { error = errorText(err) }
  }

  async function remove() {
    if (!confirm(t('clients.confirm_delete'))) return
    const r = await api.del(`/api/clients/${editing.id}`)
    toast(r.archived ? t('clients.archived_info') : t('common.deleted'))
    editing = null
    load()
  }

  let timer
  function search() { clearTimeout(timer); timer = setTimeout(load, 200) }
</script>

<div class="page">
  <div class="page-head">
    <div class="grow"><h1>{t('clients.title')}</h1><div class="sub">{t('clients.subtitle')}</div></div>
    <button class="btn primary" onclick={() => open()}><Icon name="plus" />{t('clients.new')}</button>
  </div>

  <section class="card">
    <div class="card-head">
      <label class="search grow"><Icon name="search" size={16} />
        <input class="input" placeholder={t('common.search')} bind:value={q} oninput={search} /></label>
      <label class="check small"><input type="checkbox" bind:checked={archived} onchange={load} />{t('common.show_archived')}</label>
    </div>
    {#if items.length}
      <div class="table-wrap"><table class="table">
        <thead><tr><th>{t('clients.name')}</th><th>{t('clients.contact')}</th><th>{t('clients.city')}</th><th>{t('clients.siren')}</th><th></th></tr></thead>
        <tbody>
          {#each items as c (c.id)}
            <tr class="click" onclick={() => open(c)}>
              <td><strong>{c.name}</strong> <span class="muted small">· {t(`clients.kind_${c.kind}`)}</span></td>
              <td>{c.contact_name || c.email || ''}</td>
              <td>{[c.postal_code, c.city].filter(Boolean).join(' ')}</td>
              <td class="muted">{c.siren}</td>
              <td class="num"><button class="btn sm ghost" onclick={(e) => { e.stopPropagation(); go(`/documents/new?type=quote&client=${c.id}`) }}>
                <Icon name="plus" size={15} />{t('doc.types.quote')}</button></td>
            </tr>
          {/each}
        </tbody>
      </table></div>
    {:else}
      <div class="empty"><h3>{t('clients.empty_title')}</h3>{t('clients.empty_text')}</div>
    {/if}
  </section>
</div>

{#if editing}
  <Modal title={editing.id ? t('clients.edit') : t('clients.new')} onclose={() => (editing = null)} width="760px">
    <form class="stack" onsubmit={save} id="client-form">
      <div class="segmented">
        {#each ['company', 'individual'] as k}
          <label class:on={editing.kind === k}><input type="radio" bind:group={editing.kind} value={k} />{t(`clients.kind_${k}`)}</label>
        {/each}
      </div>
      <div class="grid-2">
        <label class="field span-2"><span>{editing.kind === 'company' ? t('clients.company_name') : t('clients.full_name')} *</span>
          <input class="input" bind:value={editing.name} required /></label>
        {#if editing.kind === 'company'}
          <label class="field"><span>{t('clients.siren')}</span><input class="input" bind:value={editing.siren} inputmode="numeric" /></label>
          <label class="field"><span>{t('clients.vat_number')}</span><input class="input" bind:value={editing.vat_number} /></label>
          <label class="field span-2"><span>{t('clients.contact')}</span><input class="input" bind:value={editing.contact_name} /></label>
        {/if}
        <label class="field"><span>{t('clients.email')}</span><input class="input" type="email" bind:value={editing.email} /></label>
        <label class="field"><span>{t('clients.phone')}</span><input class="input" type="tel" bind:value={editing.phone} /></label>
        <label class="field span-2"><span>{t('clients.address')}</span><input class="input" bind:value={editing.address_line1} /></label>
        <label class="field span-2"><span class="sr-only">{t('clients.address_line2')}</span>
          <input class="input" bind:value={editing.address_line2} placeholder={t('clients.address_line2')} /></label>
        <label class="field"><span>{t('clients.postal_code')}</span><input class="input" bind:value={editing.postal_code} /></label>
        <label class="field"><span>{t('clients.city')}</span><input class="input" bind:value={editing.city} /></label>
        <label class="field"><span>{t('clients.country')}</span><input class="input" bind:value={editing.country} maxlength="2" /></label>
        <label class="field span-2"><span>{t('clients.notes')}</span><textarea class="input" bind:value={editing.notes}></textarea></label>
      </div>
      <CustomFields {fields} bind:values={editing.extra} />
      {#if error}<div class="alert danger">{error}</div>{/if}
    </form>
    {#snippet footer()}
      {#if editing.id}<button class="btn danger" onclick={remove}><Icon name="trash" size={16} />{t('common.delete')}</button>{/if}
      <span class="grow"></span>
      <button class="btn" onclick={() => (editing = null)}>{t('common.cancel')}</button>
      <button class="btn primary" type="submit" form="client-form">{t('common.save')}</button>
    {/snippet}
  </Modal>
{/if}

<style>
  .search { position: relative; display: block; max-width: 420px; }
  .search :global(.icon) { position: absolute; inset-inline-start: 11px; top: 50%; transform: translateY(-50%); color: var(--muted); }
  .search .input { padding-inline-start: 34px; }
  .segmented { display: inline-flex; padding: 3px; border-radius: 9px; background: var(--surface-2); gap: 2px; justify-self: start; }
  .segmented label { padding: 6px 14px; border-radius: 7px; cursor: pointer; font-weight: 550; color: var(--muted); }
  .segmented label.on { background: var(--surface); color: var(--text); box-shadow: var(--shadow); }
  .segmented input { display: none; }
</style>

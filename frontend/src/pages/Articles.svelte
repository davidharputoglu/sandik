<script>
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { t, errorText } from '../lib/i18n.svelte.js'
  import { money, percent } from '../lib/format.js'
  import { toast } from '../lib/toast.svelte.js'
  import { vatRates, units, vatExempt } from '../lib/session.svelte.js'
  import Icon from '../components/Icon.svelte'
  import Modal from '../components/Modal.svelte'
  import CustomFields from '../components/CustomFields.svelte'

  let items = $state([])
  let fields = $state([])
  let q = $state('')
  let editing = $state(null)
  let error = $state('')

  async function load() { items = await api.get(`/api/articles?q=${encodeURIComponent(q)}`) }
  onMount(async () => { fields = await api.get('/api/custom-fields?entity=article'); load() })

  function open(a) {
    error = ''
    editing = structuredClone($state.snapshot(a || { reference: '', label: '', description: '', unit: units()[0],
      unit_price: '0', vat_rate: vatExempt() ? '0' : '20', nature: 'service', extra: {} }))
  }
  async function save(e) {
    e?.preventDefault()
    try {
      const body = $state.snapshot(editing)
      editing.id ? await api.put(`/api/articles/${editing.id}`, body) : await api.post('/api/articles', body)
      toast(t('common.saved')); editing = null; load()
    } catch (err) { error = errorText(err) }
  }
  async function remove() {
    if (!confirm(t('articles.confirm_delete'))) return
    await api.del(`/api/articles/${editing.id}`)
    toast(t('common.deleted')); editing = null; load()
  }
  let timer
  function search() { clearTimeout(timer); timer = setTimeout(load, 200) }
</script>

<div class="page">
  <div class="page-head">
    <div class="grow"><h1>{t('articles.title')}</h1><div class="sub">{t('articles.subtitle')}</div></div>
    <button class="btn primary" onclick={() => open()}><Icon name="plus" />{t('articles.new')}</button>
  </div>
  <section class="card">
    <div class="card-head">
      <label class="search grow"><Icon name="search" size={16} />
        <input class="input" placeholder={t('common.search')} bind:value={q} oninput={search} /></label>
    </div>
    {#if items.length}
      <div class="table-wrap"><table class="table">
        <thead><tr><th>{t('articles.reference')}</th><th>{t('articles.label')}</th><th>{t('articles.unit')}</th>
          <th class="num">{t('articles.unit_price')}</th><th class="num">{t('articles.vat_rate')}</th></tr></thead>
        <tbody>
          {#each items as a (a.id)}
            <tr class="click" onclick={() => open(a)}>
              <td class="muted">{a.reference}</td><td><strong>{a.label}</strong></td><td>{a.unit}</td>
              <td class="num">{money(a.unit_price)}</td><td class="num">{percent(a.vat_rate)}</td>
            </tr>
          {/each}
        </tbody>
      </table></div>
    {:else}
      <div class="empty"><h3>{t('articles.empty_title')}</h3>{t('articles.empty_text')}</div>
    {/if}
  </section>
</div>

{#if editing}
  <Modal title={editing.id ? t('articles.edit') : t('articles.new')} onclose={() => (editing = null)}>
    <form class="stack" id="article-form" onsubmit={save}>
      <div class="grid-3">
        <label class="field"><span>{t('articles.reference')}</span><input class="input" bind:value={editing.reference} /></label>
        <label class="field span-2"><span>{t('articles.label')} *</span><input class="input" bind:value={editing.label} required /></label>
        <label class="field span-3"><span>{t('articles.description')}</span><textarea class="input" bind:value={editing.description}></textarea></label>
        <label class="field"><span>{t('articles.unit')}</span>
          <input class="input" list="units" bind:value={editing.unit} />
          <datalist id="units">{#each units() as u}<option value={u}></option>{/each}</datalist></label>
        <label class="field"><span>{t('articles.unit_price')}</span><input class="input num" inputmode="decimal" bind:value={editing.unit_price} /></label>
        <label class="field"><span>{t('articles.vat_rate')}</span>
          <select class="input" bind:value={editing.vat_rate} disabled={vatExempt()}>
            {#each vatRates() as r}<option value={r}>{percent(r)}</option>{/each}
          </select></label>
        <label class="field"><span>{t('articles.nature')}</span>
          <select class="input" bind:value={editing.nature}>
            <option value="service">{t('articles.nature_service')}</option><option value="goods">{t('articles.nature_goods')}</option>
          </select></label>
      </div>
      <CustomFields {fields} bind:values={editing.extra} />
      {#if error}<div class="alert danger">{error}</div>{/if}
    </form>
    {#snippet footer()}
      {#if editing.id}<button class="btn danger" onclick={remove}><Icon name="trash" size={16} />{t('common.delete')}</button>{/if}
      <span class="grow"></span>
      <button class="btn" onclick={() => (editing = null)}>{t('common.cancel')}</button>
      <button class="btn primary" type="submit" form="article-form">{t('common.save')}</button>
    {/snippet}
  </Modal>
{/if}

<style>
  .search { position: relative; display: block; max-width: 420px; }
  .search :global(.icon) { position: absolute; inset-inline-start: 11px; top: 50%; transform: translateY(-50%); color: var(--muted); }
  .search .input { padding-inline-start: 34px; }
</style>

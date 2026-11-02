<script>
  import { t } from '../lib/i18n.svelte.js'
  let { doc } = $props()
  const KIND = { draft: '', sent: 'info', accepted: 'success', refused: 'danger', issued: 'primary', paid: 'success' }
  const overdue = $derived(doc.type === 'invoice' && doc.status === 'issued' && doc.due_date && doc.due_date < new Date().toISOString().slice(0, 10))
</script>

{#if overdue}
  <span class="badge warning">{t('status.overdue')}</span>
{:else}
  <span class="badge {KIND[doc.status] ?? ''}">{t(`status.${doc.type}.${doc.status}`)}</span>
{/if}

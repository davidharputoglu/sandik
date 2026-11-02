<script>
  import Icon from './Icon.svelte'
  import { t } from '../lib/i18n.svelte.js'
  let { title, onclose, children, footer, width = '640px' } = $props()
  function key(e) { if (e.key === 'Escape') onclose?.() }
</script>

<svelte:window onkeydown={key} />
<div class="backdrop" role="presentation" onmousedown={(e) => e.target === e.currentTarget && onclose?.()}>
  <div class="modal card" role="dialog" aria-modal="true" aria-label={title} style:max-width={width}>
    <header class="card-head">
      <h2 class="grow">{title}</h2>
      <button class="btn ghost icon" onclick={onclose} aria-label={t('common.close')}><Icon name="x" /></button>
    </header>
    <div class="body">{@render children()}</div>
    {#if footer}<footer>{@render footer()}</footer>{/if}
  </div>
</div>

<style>
  .backdrop {
    position: fixed; inset: 0; z-index: 50; display: grid; place-items: start center; padding: 6vh 16px;
    background: rgb(8 14 18 / 45%); backdrop-filter: blur(2px); overflow-y: auto; animation: fade .12s ease-out;
  }
  .modal { width: 100%; animation: rise .16s ease-out; }
  .body { padding: var(--pad); }
  footer { display: flex; justify-content: flex-end; gap: 10px; padding: 14px var(--pad); border-top: 1px solid var(--border); }
  @keyframes fade { from { opacity: 0 } }
  @keyframes rise { from { transform: translateY(8px); opacity: 0 } }
</style>

<script>
  import { toasts } from '../lib/toast.svelte.js'
  import Icon from './Icon.svelte'
</script>

<div class="toasts" aria-live="polite">
  {#each toasts as toast (toast.id)}
    <div class="toast {toast.kind}"><Icon name={toast.kind === 'error' ? 'alert' : 'check'} size={16} />{toast.message}</div>
  {/each}
</div>

<style>
  .toasts { position: fixed; inset-block-end: 20px; inset-inline-end: 20px; display: grid; gap: 8px; z-index: 80; }
  .toast {
    display: flex; gap: 9px; align-items: center; padding: 11px 15px; border-radius: 10px; max-width: 420px;
    background: var(--text); color: var(--bg); box-shadow: 0 8px 24px rgb(0 0 0 / 22%); font-weight: 550;
    animation: in .18s ease-out; white-space: pre-line;
  }
  .toast.error { background: var(--danger); color: #fff; }
  @keyframes in { from { transform: translateY(10px); opacity: 0 } }
</style>

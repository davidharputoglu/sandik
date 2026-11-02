<!-- SPDX-License-Identifier: AGPL-3.0-or-later — Copyright (C) 2026 David HARPUTOGLU -->
<script>
  import { app } from '../lib/session.svelte.js'
  let { module, path } = $props()
  const info = $derived(app.edition.modules.find((m) => m.id === module))
  const safe = $derived(path && path.startsWith(`/modules/${module}`) ? path : `/modules/${module}/`)
</script>

<div class="frame-page">
  <iframe title={info?.name || module} src={safe}></iframe>
</div>

<style>
  .frame-page { height: 100vh; }
  iframe { width: 100%; height: 100%; border: 0; display: block; background: var(--bg); }
  @media (max-width: 900px) { .frame-page { height: calc(100vh - 53px); } }
</style>

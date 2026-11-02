<script>
  // Icônes dessinées pour sandik (trait 1,8 px, grille 24 px).
  let { name, size = 18, class: cls = '' } = $props()
  const P = {
    dashboard: '<rect x="4" y="4" width="7" height="8" rx="1.5"/><rect x="13" y="4" width="7" height="5" rx="1.5"/><rect x="13" y="11" width="7" height="9" rx="1.5"/><rect x="4" y="14" width="7" height="6" rx="1.5"/>',
    users: '<circle cx="9.5" cy="8" r="3.5"/><path d="M3 20v-1a5 5 0 0 1 5-5h3a5 5 0 0 1 5 5v1M16 4.3a3.5 3.5 0 0 1 0 7.4M21 20v-1a5 5 0 0 0-3.5-4.8"/>',
    box: '<path d="M21 7.5 12 3 3 7.5l9 4.5 9-4.5Z"/><path d="M3 7.5v9L12 21l9-4.5v-9M12 12v9"/>',
    quote: '<path d="M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V8Z"/><path d="M14 3v5h5M8.5 13h7M8.5 16.5h4.5"/>',
    invoice: '<path d="M6 3h12v18l-2.5-1.6L13 21l-2.5-1.6L8 21l-2-1.3Z"/><path d="M9 8h6M9 11.5h6M9 15h3.5"/>',
    credit: '<path d="M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V8Z"/><path d="M14 3v5h5M9 14.5h6"/>',
    settings: '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
    module: '<path d="M9 3h6v5h5v6h-5v7H9v-7H4V8h5Z"/>',
    logout: '<path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4M10 16.5 14.5 12 10 7.5M14.5 12H4"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    search: '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    edit: '<path d="M4 20h4L19 9l-4-4L4 16v4Z"/><path d="m13.5 6.5 4 4"/>',
    print: '<path d="M7 9V3.5h10V9M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"/><path d="M7 14h10v7H7Z"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    send: '<path d="M21 3 10.5 13.5M21 3l-6.5 18-4-7.5L3 9.5Z"/>',
    back: '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3Z"/>',
    palette: '<path d="M12 3a9 9 0 1 0 0 18c1 0 1.7-.8 1.7-1.7 0-.5-.2-.9-.5-1.2-.3-.3-.5-.7-.5-1.2 0-.9.7-1.6 1.6-1.6H16a5 5 0 0 0 5-5C21 6.3 17 3 12 3Z"/><circle cx="7.5" cy="11" r=".9" fill="currentColor"/><circle cx="10" cy="7.3" r=".9" fill="currentColor"/><circle cx="14.5" cy="7.3" r=".9" fill="currentColor"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    up: '<path d="M12 19V5M6 11l6-6 6 6"/>',
    down: '<path d="M12 5v14M6 13l6 6 6-6"/>',
    trend: '<path d="m3 17 6-6 4 4 8-8M15 7h6v6"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    alert: '<path d="M12 3.5 21.5 20h-19Z"/><path d="M12 10v4.5M12 17.3v.2"/>',
    wallet: '<path d="M4 7.5V18a2 2 0 0 0 2 2h13a1 1 0 0 0 1-1v-3M4 7.5A2.5 2.5 0 0 1 6.5 5H17v2.5M4 7.5h15a1 1 0 0 1 1 1V12"/><path d="M15 12h6v4h-6a2 2 0 0 1 0-4Z"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    more: '<path d="M5 12h.01M12 12h.01M19 12h.01" stroke-width="3"/>',
    text: '<path d="M5 6h14M5 12h14M5 18h9"/>',
    section: '<path d="M5 5h14M5 9h9"/><rect x="5" y="13" width="14" height="6" rx="1.5"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    moon: '<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/>',
  }
</script>

<svg class="icon {cls}" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
  stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{@html P[name] || ''}</svg>

<style>
  .icon { flex: none; display: block; }
  :global([dir='rtl']) .icon.flip { transform: scaleX(-1); }
</style>

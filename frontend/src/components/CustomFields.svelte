<script>
  // Champs personnalisés (définis dans Paramètres → Champs personnalisés, ou par un module).
  let { fields = [], values = $bindable({}), readonly = false } = $props()
</script>

{#if fields.length}
  <div class="grid-2">
    {#each fields as f (f.key)}
      {#if f.type === 'boolean'}
        <label class="check"><input type="checkbox" bind:checked={values[f.key]} disabled={readonly} />{f.label}</label>
      {:else}
        <label class="field" class:span-2={f.type === 'textarea'}>
          <span>{f.label}{f.required ? ' *' : ''}</span>
          {#if f.type === 'textarea'}
            <textarea class="input" bind:value={values[f.key]} required={f.required} readonly={readonly}></textarea>
          {:else if f.type === 'select'}
            <select class="input" bind:value={values[f.key]} required={f.required} disabled={readonly}>
              <option value=""></option>
              {#each f.options as o}<option>{o}</option>{/each}
            </select>
          {:else}
            <input class="input" type={f.type === 'number' ? 'number' : f.type === 'date' ? 'date' : 'text'}
              step="any" bind:value={values[f.key]} required={f.required} readonly={readonly} />
          {/if}
        </label>
      {/if}
    {/each}
  </div>
{/if}

(function () {
  if (!window.IndexedRows) return;

  function escapeAttr(s) {
    return String(s ?? "").replace(/"/g, "&quot;");
  }

  function buildOptions(values, selected) {
    if (!values) return "";
    return values
      .map((v) => `<option value="${escapeAttr(v)}" ${v === selected ? "selected" : ""}>${v}</option>`)
      .join("");
  }

  function initDamageList(opts) {
    const { prefix, rowsId, addId, label } = opts;

    window.IndexedRows.initIndexedRows({
      prefix,
      rowsContainerId: rowsId,
      addButtonId: addId,
      createRowEl: (data, idx) => {
        const row = document.createElement("div");
        row.className = "grid grid-cols-1 md:grid-cols-12 gap-2 items-end";

        row.innerHTML = `
          <div class="md:col-span-11">
            <select name="${prefix}[${idx}].type" data-field="type" class="w-full">
              <option value="">— ${label} —</option>
              ${buildOptions(window.MONSTER_ENUMS?.DamageType, data.type)}
            </select>
          </div>
          <div class="md:col-span-1 flex md:justify-end">
            <button type="button" class="px-2 py-2 rounded border" data-remove-row title="Remove">✕</button>
          </div>
        `;
        return row;
      },
    });
  }

  initDamageList({
    prefix: "damage_resistances",
    rowsId: "damage-resistances-rows",
    addId: "damage-resistances-add",
    label: "resistance",
  });

  initDamageList({
    prefix: "damage_immunities",
    rowsId: "damage-immunities-rows",
    addId: "damage-immunities-add",
    label: "immunity",
  });

  initDamageList({
    prefix: "damage_vulnerabilities",
    rowsId: "damage-vulnerabilities-rows",
    addId: "damage-vulnerabilities-add",
    label: "vulnerability",
  });
})();
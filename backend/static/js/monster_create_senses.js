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

  window.IndexedRows.initIndexedRows({
    prefix: "senses",
    rowsContainerId: "senses-rows",
    addButtonId: "senses-add",
    createRowEl: (data, idx) => {
      const row = document.createElement("div");
      row.className = "grid grid-cols-1 md:grid-cols-12 gap-2 items-end";

      row.innerHTML = `
        <div class="md:col-span-6">
          <select name="senses[${idx}].sense" data-field="sense" class="w-full">
            <option value="">— sense —</option>
            ${buildOptions(window.MONSTER_ENUMS?.Sense, data.sense)}
          </select>
        </div>

        <div class="md:col-span-5">
          <input type="number" min="1" step="1" name="senses[${idx}].range" data-field="range"
            placeholder="range (ft)" class="w-full" value="${escapeAttr(data.range || "")}">
        </div>

        <div class="md:col-span-1 flex md:justify-end">
          <button type="button" class="px-2 py-2 rounded border" data-remove-row title="Remove">✕</button>
        </div>
      `;
      return row;
    },
  });
})();
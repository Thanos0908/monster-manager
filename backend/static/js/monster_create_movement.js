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
    prefix: "movement",
    rowsContainerId: "movement-rows",
    addButtonId: "movement-add",
    createRowEl: (data, idx) => {
      const row = document.createElement("div");
      row.className = "grid grid-cols-1 md:grid-cols-12 gap-2 items-end";

      row.innerHTML = `
        <div class="md:col-span-4">
          <select name="movement[${idx}].type" data-field="type" class="w-full">
            <option value="">— type —</option>
            ${buildOptions(window.MONSTER_ENUMS?.MovementType, data.type)}
          </select>
        </div>

        <div class="md:col-span-4">
          <input type="number" min="1" step="1" name="movement[${idx}].speed" data-field="speed"
            placeholder="speed (ft)" class="w-full" value="${escapeAttr(data.speed || "")}">
        </div>

        <div class="md:col-span-3">
          <label class="inline-flex items-center gap-2">
            <input type="checkbox" name="movement[${idx}].hover" data-field="hover" ${data.hover === "on" ? "checked" : ""}>
            Hover
          </label>
        </div>

        <div class="md:col-span-1 flex md:justify-end">
          <button type="button" class="px-2 py-2 rounded border" data-remove-row title="Remove">✕</button>
        </div>
      `;
      return row;
    },
  });
})();
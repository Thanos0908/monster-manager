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
    prefix: "languages",
    rowsContainerId: "languages-rows",
    addButtonId: "languages-add",
    createRowEl: (data, idx) => {
      const row = document.createElement("div");
      row.className = "grid grid-cols-1 md:grid-cols-12 gap-2 items-end";

      row.innerHTML = `
        <div class="md:col-span-11">
          <select name="languages[${idx}].language" data-field="language" class="w-full">
            <option value="">— language —</option>
            ${buildOptions(window.MONSTER_ENUMS?.Language, data.language)}
          </select>
        </div>

        <div class="md:col-span-1 flex md:justify-end">
          <button type="button" class="px-2 py-2 rounded border" data-remove-row title="Remove">✕</button>
        </div>
      `;
      return row;
    },
  });
})();

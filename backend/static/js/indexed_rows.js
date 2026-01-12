(function () {
  function readExisting(prefix) {
    const inputs = document.querySelectorAll(`input[data-existing="${prefix}"]`);
    const byIdx = new Map();

    for (const inp of inputs) {
      const idx = Number(inp.getAttribute("data-idx"));
      const key = inp.getAttribute("data-key");
      const value = inp.value;

      if (!value) continue;

      if (!byIdx.has(idx)) byIdx.set(idx, {});
      byIdx.get(idx)[key] = value;
    }

    // return rows in index order
    return Array.from(byIdx.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([_, obj]) => obj);
  }

  function initIndexedRows(opts) {
    const {
      prefix,            // "movement" | "senses" | "languages"
      rowsContainerId,   // "movement-rows"
      addButtonId,       // "movement-add"
      createRowEl,       // (rowData, index) => HTMLElement
    } = opts;

    const rowsEl = document.getElementById(rowsContainerId);
    const addBtn = document.getElementById(addButtonId);
    if (!rowsEl || !addBtn) return;

    function nextIndex() {
      // indices must be dense-ish but uniqueness is enough
      return rowsEl.children.length;
    }

    function addRow(rowData = {}) {
      const idx = nextIndex();
      const rowEl = createRowEl(rowData, idx);

      // Remove button (if present)
      const removeBtn = rowEl.querySelector("[data-remove-row]");
      if (removeBtn) {
        removeBtn.addEventListener("click", () => {
          rowEl.remove();
          // Re-index all rows so the posted names remain 0..n-1
          reindexAll();
        });
      }

      rowsEl.appendChild(rowEl);
    }

    function reindexAll() {
      const rows = Array.from(rowsEl.children);
      rowsEl.innerHTML = "";
      for (let i = 0; i < rows.length; i++) {
        const old = rows[i];

        // Rebuild a row by reading current inputs into data object
        const data = {};
        old.querySelectorAll("[data-field]").forEach((el) => {
          const key = el.getAttribute("data-field");
          if (el.type === "checkbox") data[key] = el.checked ? "on" : "";
          else data[key] = el.value;
        });

        addRow(data);
      }
    }

    // Hydrate from hidden “existing” inputs (server re-render)
    const existing = readExisting(prefix);
    if (existing.length) {
      existing.forEach((row) => addRow(row));
    } else {
      addRow();
    }

    addBtn.addEventListener("click", () => addRow());
  }

  window.IndexedRows = { initIndexedRows };
})();
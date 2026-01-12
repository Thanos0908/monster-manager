(function () {
  const jsonEl = document.getElementById("legendary_actions_json");
  const rowsEl = document.getElementById("legendary-actions-rows");
  const addBtn = document.getElementById("legendary-actions-add");

  if (!jsonEl || !rowsEl || !addBtn) return;

  function safeParseJsonArray(value) {
    if (!value || !value.trim()) return [];
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function sync() {
    const out = [];
    for (const r of rowsEl.children) {
      const n = (r.__name?.value ?? "").trim();
      const t = (r.__text?.value ?? "").trim();
      if (!n && !t) continue;
      out.push({ name: n, text: t });
    }
    jsonEl.value = out.length ? JSON.stringify(out) : "";
  }

  function createRow({ name = "", text = "" } = {}) {
    const row = document.createElement("div");
    row.className = "grid grid-cols-1 md:grid-cols-12 gap-2 items-start";

    const nameWrap = document.createElement("div");
    nameWrap.className = "md:col-span-4";
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.placeholder = "Legendary action name (e.g., Detect)";
    nameInput.value = name;
    nameWrap.appendChild(nameInput);

    const textWrap = document.createElement("div");
    textWrap.className = "md:col-span-7";
    const textInput = document.createElement("textarea");
    textInput.rows = 3;
    textInput.placeholder = "Legendary action description";
    textInput.value = text;
    textWrap.appendChild(textInput);

    const removeWrap = document.createElement("div");
    removeWrap.className = "md:col-span-1 flex md:justify-end";
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "px-2 py-2 rounded border";
    removeBtn.textContent = "✕";
    removeBtn.title = "Remove legendary action";
    removeWrap.appendChild(removeBtn);

    row.append(nameWrap, textWrap, removeWrap);

    row.__name = nameInput;
    row.__text = textInput;

    nameInput.addEventListener("input", sync);
    textInput.addEventListener("input", sync);

    removeBtn.addEventListener("click", () => {
      row.remove();
      sync();
      ensureOneRow();
    });

    return row;
  }

  function ensureOneRow() {
    if (!rowsEl.children.length) {
      rowsEl.appendChild(createRow());
    }
  }

  function hydrate() {
    const items = safeParseJsonArray(jsonEl.value);
    rowsEl.innerHTML = "";
    if (!items.length) {
      ensureOneRow();
    } else {
      for (const item of items) rowsEl.appendChild(createRow(item));
    }
    sync();
  }

  hydrate();

  addBtn.addEventListener("click", () => {
    rowsEl.appendChild(createRow());
    sync();
  });

  const form = jsonEl.closest("form");
  if (form) {
    form.addEventListener("submit", () => sync());
  }
})();

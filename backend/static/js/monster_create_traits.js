(function () {
  const traitsJsonEl = document.getElementById("traits_json");
  const rowsEl = document.getElementById("traits-rows");
  const addBtn = document.getElementById("traits-add");

  if (!traitsJsonEl || !rowsEl || !addBtn) return;

  function safeParseJsonArray(value) {
    if (!value || !value.trim()) return [];
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  // Normalize values before assigning to input/textarea .value
  function normalizeValue(s) {
    return String(s ?? "");
  }

  function createRow({ name = "", text = "" } = {}) {
    const wrapper = document.createElement("div");
    wrapper.className = "grid grid-cols-1 md:grid-cols-12 gap-2 items-start";

    // Name input
    const nameWrap = document.createElement("div");
    nameWrap.className = "md:col-span-4";
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.placeholder = "Trait name (e.g., Keen Smell)";
    nameInput.className = "w-full";
    nameInput.value = normalizeValue(name);
    nameWrap.appendChild(nameInput);

    // Text input
    const textWrap = document.createElement("div");
    textWrap.className = "md:col-span-7";
    const textInput = document.createElement("textarea");
    textInput.rows = 3;
    textInput.placeholder = "Trait text (description)";
    textInput.className = "w-full";
    textInput.value = normalizeValue(text);
    textWrap.appendChild(textInput);

    // Remove button
    const removeWrap = document.createElement("div");
    removeWrap.className = "md:col-span-1 flex md:justify-end";
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "px-2 py-2 rounded border";
    removeBtn.textContent = "✕";
    removeBtn.title = "Remove trait";
    removeWrap.appendChild(removeBtn);

    wrapper.appendChild(nameWrap);
    wrapper.appendChild(textWrap);
    wrapper.appendChild(removeWrap);

    removeBtn.addEventListener("click", () => {
      wrapper.remove();
      syncTraitsJson();
      ensureAtLeastOneRow();
    });

    nameInput.addEventListener("input", syncTraitsJson);
    textInput.addEventListener("input", syncTraitsJson);

    // Store refs for reading later
    wrapper.__traitNameInput = nameInput;
    wrapper.__traitTextInput = textInput;

    return wrapper;
  }

  function getAllRows() {
    return Array.from(rowsEl.children);
  }

  function buildJsonFromRows() {
    const out = [];

    for (const row of getAllRows()) {
      const name = (row.__traitNameInput?.value ?? "").trim();
      const text = (row.__traitTextInput?.value ?? "").trim();

      if (!name && !text) continue;

      out.push({ name, text });
    }

    return out;
  }

  function syncTraitsJson() {
    const out = buildJsonFromRows();
    traitsJsonEl.value = out.length ? JSON.stringify(out) : "";
  }

  function ensureAtLeastOneRow() {
    if (getAllRows().length === 0) {
      rowsEl.appendChild(createRow());
    }
  }

  function hydrateFromTraitsJson() {
    const items = safeParseJsonArray(traitsJsonEl.value);

    if (items.length === 0) {
      rowsEl.innerHTML = "";
      rowsEl.appendChild(createRow());
      syncTraitsJson();
      return;
    }

    rowsEl.innerHTML = "";
    for (const item of items) {
      rowsEl.appendChild(
        createRow({
          name: item?.name ?? "",
          text: item?.text ?? "",
        })
      );
    }

    syncTraitsJson();
  }

  hydrateFromTraitsJson();

  // Add row button
  addBtn.addEventListener("click", () => {
    rowsEl.appendChild(createRow());
    syncTraitsJson();
  });

  const formEl = traitsJsonEl.closest("form");
  if (formEl) {
    formEl.addEventListener("submit", () => {
      syncTraitsJson();
    });
  }
})();
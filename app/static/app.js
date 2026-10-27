const $ = (id) => document.getElementById(id);
const money = (value) => new Intl.NumberFormat("en-IN", {style:"currency", currency:"INR", maximumFractionDigits:2}).format(value);
let products = [];
let debounceTimer;

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: {"Content-Type":"application/json", ...(options.headers || {})},
    ...options
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = Array.isArray(body.detail) ? body.detail.map(x => x.msg).join(", ") : (body.detail || detail);
    } catch (_) {}
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

function showMessage(message = "") { $("message").textContent = message; }

async function loadDashboard() {
  const data = await api("/api/dashboard");
  $("total-products").textContent = data.total_products.toLocaleString("en-IN");
  $("total-units").textContent = data.total_units.toLocaleString("en-IN");
  $("inventory-value").textContent = money(data.inventory_value);
  $("low-stock-count").textContent = data.low_stock_count.toLocaleString("en-IN");
}

async function loadCategories(selected = $("category-filter").value) {
  const categories = await api("/api/categories");
  const select = $("category-filter");
  select.innerHTML = '<option value="">All categories</option>';
  categories.forEach(category => {
    const option = document.createElement("option");
    option.value = category;
    option.textContent = category;
    select.appendChild(option);
  });
  select.value = categories.includes(selected) ? selected : "";
}

function statusFor(product) {
  if (product.quantity === 0) return {label:"Out of stock", cls:"out"};
  if (product.quantity <= product.reorder_level) return {label:"Low stock", cls:"low"};
  return {label:"In stock", cls:"ok"};
}

function makeCell(text, className = "") {
  const td = document.createElement("td");
  if (className) td.className = className;
  td.textContent = text;
  return td;
}

function renderProducts(items) {
  const body = $("product-rows");
  body.replaceChildren();
  if (!items.length) {
    const row = document.createElement("tr");
    const cell = makeCell("No products found. Add a product to get started.");
    cell.colSpan = 7; cell.className = "empty"; row.appendChild(cell); body.appendChild(row);
  }
  items.forEach(product => {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    const name = document.createElement("div"); name.className = "product-name"; name.textContent = product.name;
    const desc = document.createElement("div"); desc.className = "product-description"; desc.textContent = product.description || "No description";
    nameCell.append(name, desc);
    row.append(nameCell, makeCell(product.sku, "sku"), makeCell(product.category),
      makeCell(money(product.price), "price"), makeCell(product.quantity.toLocaleString("en-IN"), "qty"));
    const statusCell = document.createElement("td");
    const status = statusFor(product);
    const pill = document.createElement("span"); pill.className = `pill ${status.cls}`; pill.textContent = status.label;
    statusCell.appendChild(pill); row.appendChild(statusCell);

    const actions = document.createElement("td");
    const actionWrap = document.createElement("div"); actionWrap.className = "actions";
    [["Edit", () => openEdit(product)], ["Stock", () => openStock(product)], ["Delete", () => deleteProduct(product)]].forEach(([label, fn]) => {
      const button = document.createElement("button");
      button.type = "button"; button.className = "action-btn"; button.textContent = label;
      button.addEventListener("click", fn); actionWrap.appendChild(button);
    });
    actions.appendChild(actionWrap); row.appendChild(actions); body.appendChild(row);
  });
  $("result-count").textContent = `${items.length} product${items.length === 1 ? "" : "s"}`;
}

async function refresh() {
  showMessage("");
  try {
    const params = new URLSearchParams();
    const search = $("search").value.trim();
    const category = $("category-filter").value;
    if (search) params.set("search", search);
    if (category) params.set("category", category);
    if ($("low-only").checked) params.set("low_stock", "true");
    products = await api(`/api/products?${params}`);
    renderProducts(products);
    await loadDashboard();
    await loadCategories(category);
    $("api-status").textContent = "connected";
  } catch (error) {
    showMessage(error.message);
    $("api-status").textContent = "unavailable";
    $("product-rows").innerHTML = '<tr><td colspan="7" class="empty">Could not load inventory. Is the API running?</td></tr>';
  }
}

function resetProductForm() {
  $("product-form").reset();
  $("product-id").value = "";
  $("quantity").disabled = false;
  $("quantity-label").style.display = "";
  $("dialog-title").textContent = "Add product";
  $("save-btn").textContent = "Save product";
  $("edit-note").textContent = "Fields marked * are required.";
}
function openCreate() {
  resetProductForm();
  $("product-dialog").showModal();
}
function openEdit(product) {
  resetProductForm();
  $("dialog-title").textContent = "Edit product";
  $("save-btn").textContent = "Save changes";
  $("product-id").value = product.id;
  ["name","sku","category","price","reorder-level","description"].forEach(id => {
    const key = id === "reorder-level" ? "reorder_level" : id;
    $(id).value = product[key] ?? "";
  });
  $("quantity").value = product.quantity;
  $("quantity").disabled = true;
  $("quantity-label").style.display = "none";
  $("edit-note").textContent = "Use the Stock action to adjust inventory and keep a movement history.";
  $("product-dialog").showModal();
}

$("product-form").addEventListener("submit", async event => {
  event.preventDefault();
  const id = $("product-id").value;
  const payload = {
    name: $("name").value.trim(), sku: $("sku").value.trim(),
    category: $("category").value.trim(), price: Number($("price").value),
    reorder_level: Number($("reorder-level").value), description: $("description").value.trim()
  };
  if (!id) payload.quantity = Number($("quantity").value);
  try {
    await api(id ? `/api/products/${id}` : "/api/products", {
      method: id ? "PATCH" : "POST", body: JSON.stringify(payload)
    });
    $("product-dialog").close(); await refresh();
  } catch (error) { showMessage(error.message); }
});

function openStock(product) {
  $("stock-form").reset();
  $("stock-product-id").value = product.id;
  $("stock-product-name").textContent = `${product.name} · Current stock: ${product.quantity}`;
  $("stock-amount").value = 1;
  $("stock-dialog").showModal();
}
$("stock-form").addEventListener("submit", async event => {
  event.preventDefault();
  const direction = $("stock-direction").value === "add" ? 1 : -1;
  const change = Number($("stock-amount").value) * direction;
  try {
    await api(`/api/products/${$("stock-product-id").value}/stock`, {
      method:"POST",
      body:JSON.stringify({change, reason:direction > 0 ? "restock" : "sale_or_removal", note:$("stock-note").value.trim()})
    });
    $("stock-dialog").close(); await refresh();
  } catch (error) { showMessage(error.message); }
});

async function deleteProduct(product) {
  if (!confirm(`Delete "${product.name}" (${product.sku})? Its stock movement history will also be deleted.`)) return;
  try {
    await api(`/api/products/${product.id}`, {method:"DELETE"});
    await refresh();
  } catch (error) { showMessage(error.message); }
}

$("add-product-btn").addEventListener("click", openCreate);
$("close-dialog").addEventListener("click", () => $("product-dialog").close());
$("cancel-dialog").addEventListener("click", () => $("product-dialog").close());
$("close-stock-dialog").addEventListener("click", () => $("stock-dialog").close());
$("cancel-stock-dialog").addEventListener("click", () => $("stock-dialog").close());
$("refresh-btn").addEventListener("click", refresh);
$("search").addEventListener("input", () => { clearTimeout(debounceTimer); debounceTimer = setTimeout(refresh, 250); });
$("category-filter").addEventListener("change", refresh);
$("low-only").addEventListener("change", refresh);
$("show-low-stock").addEventListener("click", () => {
  $("low-only").checked = true; refresh();
  $("products").scrollIntoView({behavior:"smooth"});
});
refresh();

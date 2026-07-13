/**
 * Profile page logic — load and update the current user's profile.
 */

async function loadProfile() {
  const resp = await apiFetch("/users/me");
  if (!resp.ok) return;
  const user = await resp.json();

  // Header
  const initials = user.full_name.split(" ").slice(0, 2).map(n => n[0]).join("").toUpperCase();
  document.getElementById("avatar").textContent = initials;
  document.getElementById("profile-name").textContent = user.full_name;
  document.getElementById("profile-email").textContent = user.email;

  const badge = document.getElementById("email-badge");
  if (user.email_confirmed) {
    badge.textContent = "Verificado";
    badge.className = "badge badge-green";
  } else {
    badge.textContent = "Nao verificado";
    badge.className = "badge badge-orange";
  }

  // Fill form
  const fields = ["full_name", "zip_code", "city", "state", "phone", "bio"];
  for (const f of fields) {
    const el = document.getElementById(f);
    if (el) el.value = user[f] || "";
  }
}

async function handleProfileUpdate(e) {
  e.preventDefault();
  const form = e.target;
  const alert = document.getElementById("alert");
  const btn = form.querySelector("button[type=submit]");

  hideAlert(alert);
  setLoading(btn, true);

  const payload = {
    full_name: form.full_name.value.trim() || undefined,
    zip_code:  form.zip_code.value.trim()  || undefined,
    city:      form.city.value.trim()      || undefined,
    state:     form.state.value.trim()     || undefined,
    phone:     form.phone.value.trim()     || undefined,
    bio:       form.bio.value.trim()       || undefined,
  };

  // Remove undefined keys
  Object.keys(payload).forEach(k => payload[k] === undefined && delete payload[k]);

  try {
    const resp = await apiFetch("/users/me", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (resp.ok) {
      showAlert(alert, "Perfil atualizado com sucesso!", "success");
      await loadProfile();
    } else {
      showAlert(alert, data.detail || "Erro ao salvar.", "error");
    }
  } catch {
    showAlert(alert, "Erro de conexao.", "error");
  } finally {
    setLoading(btn, false);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  loadProfile();
  const form = document.getElementById("profile-form");
  if (form) form.addEventListener("submit", handleProfileUpdate);
});

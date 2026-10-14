const form = document.querySelector("[data-lead-form]");

if (form) {
  const button = form.querySelector("button[type=submit]");
  const status = form.querySelector("[data-form-status]");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    status.textContent = "";
    form.querySelectorAll("[data-error-for]").forEach((element) => {
      element.textContent = "";
    });

    const data = Object.fromEntries(new FormData(form));
    data.accepte_appel = form.elements.accepte_appel.checked;
    data.consentement_rgpd = form.elements.consentement_rgpd.checked;
    for (const key of ["utm_source", "utm_campaign"]) {
      if (!data[key]) delete data[key];
    }

    try {
      const response = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const body = await response.json();
      if (response.status === 201) {
        window.location.assign(body.redirect);
        return;
      }
      for (const [field, message] of Object.entries(body.errors ?? {})) {
        const target = form.querySelector(`[data-error-for="${field}"]`);
        if (target) target.textContent = message;
      }
      if (body.message) status.textContent = body.message;
    } catch {
      status.textContent = form.dataset.networkError;
    } finally {
      button.disabled = false;
    }
  });
}

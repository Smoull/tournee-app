// Portée isolée : les scripts classiques partagent la portée globale.
(() => {
  const Motion = window.Motion;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function setupStops() {
    for (const stop of document.querySelectorAll("[data-route-stop]")) {
      stop.classList.remove("is-reached");
      Motion.inView(stop, () => stop.classList.add("is-reached"), { amount: 1 });
    }
  }

  function setupReveals() {
    const { animate, inView, stagger } = Motion;
    for (const group of document.querySelectorAll("[data-reveal-group]")) {
      const items = [...group.children];
      for (const item of items) item.style.opacity = "0";
      inView(group, () => {
        animate(items, { opacity: [0, 1], y: [24, 0] }, { delay: stagger(0.12), duration: 0.5 });
      }, { amount: "some" });
    }
  }

  function setupOffer() {
    const { animate, inView, stagger } = Motion;
    const offer = document.querySelector("[data-offer]");
    if (!offer) return;
    const strike = offer.querySelector("[data-strike-line]");
    const early = offer.querySelector("[data-price-early]");
    const amount = offer.querySelector("[data-count-to]");
    const dots = [...offer.querySelectorAll("[data-place-dot]")];
    strike.style.transform = "scaleX(0)";
    early.style.opacity = "0";
    if (amount) amount.textContent = "0";
    for (const dot of dots) dot.style.transform = "scale(0)";

    inView(offer, async () => {
      await animate(strike, { scaleX: [0, 1] }, { duration: 0.5, ease: "easeOut" });
      animate(early, { opacity: [0, 1], scale: [0.9, 1] }, { duration: 0.4 });
      if (amount) {
        animate(0, Number(amount.dataset.countTo), {
          duration: 1.2,
          ease: "easeOut",
          onUpdate: (value) => {
            amount.textContent = String(Math.round(value));
          },
        }).then(() => {
          amount.textContent = amount.dataset.countFinal;
        });
      }
      animate(dots, { scale: [0, 1] }, { delay: stagger(0.05), duration: 0.3 });
    }, { amount: "some" });
  }

  if (Motion && !reduceMotion) {
    setupStops();
    setupReveals();
    setupOffer();
  }
})();

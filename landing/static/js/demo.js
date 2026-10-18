// Portée isolée : les scripts classiques partagent la portée globale.
(() => {
  const Motion = window.Motion;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function setupDemo(figure) {
    const { inView, stagger } = Motion;
    const before = figure.querySelector("[data-route-before]");
    const after = figure.querySelector("[data-route-after]");
    const markers = [...figure.querySelectorAll("[data-marker]")];
    const incident = figure.querySelector("[data-incident]");
    const sms = figure.querySelector("[data-sms]");
    const replay = figure.querySelector("[data-demo-replay]");
    const removed = markers.filter((marker) => !marker.dataset.heureApres);
    const added = markers.filter((marker) => !marker.dataset.heureAvant);
    const initial = markers.filter((marker) => marker.dataset.heureAvant);
    let running = false;
    const active = new Set();

    function animate(target, keyframes, options) {
      const controls = Motion.animate(target, keyframes, options);
      active.add(controls);
      controls.finished.then(() => active.delete(controls));
      return controls;
    }

    function setTimes(key) {
      for (const marker of markers) {
        const value = marker.dataset[key];
        if (value) marker.querySelector("[data-heure]").textContent = value;
      }
    }

    function resetToStart() {
      before.style.strokeDasharray = "1";
      before.style.strokeDashoffset = "1";
      before.style.opacity = "1";
      after.style.strokeDasharray = "1";
      after.style.strokeDashoffset = "1";
      for (const marker of markers) marker.style.opacity = "0";
      setTimes("heureAvant");
      incident.style.opacity = "0";
      sms.style.opacity = "0";
    }

    async function play() {
      if (running) return;
      running = true;
      resetToStart();
      animate(before, { strokeDashoffset: [1, 0] }, { duration: 1.2, ease: "easeOut" });
      await animate(initial, { opacity: [0, 1] }, { delay: stagger(0.2), duration: 0.3 });
      await animate(incident, { opacity: [0, 1], y: [-8, 0] }, { delay: 0.3, duration: 0.4 });
      await Promise.all([
        animate(removed, { opacity: 0 }, { duration: 0.5 }),
        animate(before, { opacity: 0.25 }, { duration: 0.5 }),
      ]);
      await Promise.all([
        animate(after, { strokeDashoffset: [1, 0] }, { duration: 1, ease: "easeInOut" }),
        animate(added, { opacity: [0, 1] }, { delay: 0.3, duration: 0.4 }),
      ]);
      setTimes("heureApres");
      await animate(before, { opacity: 0 }, { duration: 0.3 });
      await animate(sms, { opacity: [0, 1], y: [16, 0] }, { duration: 0.5 });
      running = false;
    }

    // Une lecture (~4 s) à chaque entrée à l'écran, puis arrêt sur l'état final : pas de mouvement sans fin
    // (WCAG 2.2.2). Pause hors écran : qui défile vite retrouve la démo là où il l'a quittée.
    inView(figure, () => {
      if (running) active.forEach((controls) => controls.play());
      else play();
      return () => active.forEach((controls) => controls.pause());
    });
    replay.addEventListener("click", play);
  }

  if (Motion && !reduceMotion) {
    document.querySelectorAll("[data-demo]").forEach(setupDemo);
  }
})();

const header = document.querySelector("[data-header]");
const nav = document.querySelector("[data-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");

const setHeaderState = () => {
  header?.classList.toggle("is-scrolled", window.scrollY > 24);
};

setHeaderState();
window.addEventListener("scroll", setHeaderState, { passive: true });

navToggle?.addEventListener("click", () => {
  const isOpen = nav?.classList.toggle("is-open") ?? false;
  navToggle.setAttribute("aria-expanded", String(isOpen));
});

nav?.addEventListener("click", (event) => {
  if (event.target instanceof HTMLAnchorElement) {
    nav.classList.remove("is-open");
    navToggle?.setAttribute("aria-expanded", "false");
  }
});

const phases = [
  {
    period: "Monat 0 bis 6",
    title: "Erwerb & Funktionsfähigkeit",
    copy:
      "Hof übernehmen, Brunnen und Abwasser auf Endausbau vorbereiten, Ferienhaus fertigstellen und erste Einnahmen ermöglichen.",
    items: [
      "Kauf und Besitz sichern",
      "Wasser und Abwasser installieren",
      "Ferienhaus in den ersten drei Monaten vermietbar machen",
    ],
  },
  {
    period: "Monat 6 bis 18",
    title: "Rundhaus & Begegnung",
    copy:
      "Ein ganzjährig nutzbarer Mittelpunkt für Workshops, Essen, kleine Kulturformate und regionale Begegnung entsteht.",
    items: [
      "15 Meter Rundhaus planen und bauen",
      "Außenbereiche, Wege und Sitzflächen anlegen",
      "Erste Backtage, Schmiedetage und Begegnungsabende starten",
    ],
  },
  {
    period: "Jahr 2 bis 3",
    title: "Backhaus & Schmiede",
    copy:
      "Handwerk und Wissen werden wirtschaftlich nutzbar: mit Kursen, Verkauf, Auftragsarbeiten und ganzjährigen Tagesangeboten.",
    items: [
      "Backhaus mit Holzofen für Kurse und Hofverkauf",
      "Schmiede mit Sicherheitskonzept und Kursbetrieb",
      "Externe Anbieter in erste Formate einbinden",
    ],
  },
  {
    period: "Jahr 3 bis 5",
    title: "Gästehäuser & längere Aufenthalte",
    copy:
      "Vier bis fünf kleine Häuser erhöhen Kapazität und Aufenthaltsdauer, ergänzt um Sanitärhaus, Wege und wintertaugliche Infrastruktur.",
    items: [
      "10 bis 15 Übernachtungsgäste ermöglichen",
      "Häuser naturnah statt siedlungsartig platzieren",
      "Mehrtagestourismus und Winterangebote stärken",
    ],
  },
  {
    period: "Jahr 5 bis 10",
    title: "Konsolidierung & Qualität",
    copy:
      "Der Hof wächst nicht um jeden Preis. Kooperationen, Abläufe, wiederkehrende Gäste und regionale Verankerung werden wichtiger als Expansion.",
    items: [
      "Betrieb optimieren und Qualität erhöhen",
      "Kooperationen und externe Kursanbieter ausbauen",
      "Mitarbeiter nur bei stabiler Nachfrage ergänzen",
    ],
  },
];

const roadmap = document.querySelector("[data-roadmap]");
const tabs = Array.from(document.querySelectorAll("[data-phase]"));
const periodNode = document.querySelector("[data-phase-period]");
const titleNode = document.querySelector("[data-phase-title]");
const copyNode = document.querySelector("[data-phase-copy]");
const listNode = document.querySelector("[data-phase-list]");

const renderPhase = (index) => {
  const phase = phases[index];
  if (!phase || !periodNode || !titleNode || !copyNode || !listNode) return;

  tabs.forEach((tab, tabIndex) => {
    const isActive = tabIndex === index;
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
  });

  periodNode.textContent = phase.period;
  titleNode.textContent = phase.title;
  copyNode.textContent = phase.copy;
  listNode.replaceChildren(
    ...phase.items.map((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      return li;
    }),
  );
};

roadmap?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  const tab = target.closest("[data-phase]");
  if (!(tab instanceof HTMLElement)) return;

  const phaseIndex = Number(tab.dataset.phase);
  renderPhase(phaseIndex);
});

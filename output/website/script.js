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

const phasesByLang = {
  de: [
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
  ],
  sv: [
    {
      period: "Månad 0 till 6",
      title: "Förvärv & funktionsduglighet",
      copy:
        "Ta över gården, förbereda brunn och avlopp för slutlig utbyggnad, färdigställa fritidshuset och möjliggöra de första intäkterna.",
      items: [
        "Säkra köp och ägande",
        "Installera vatten och avlopp",
        "Göra fritidshuset uthyrningsbart under de första tre månaderna",
      ],
    },
    {
      period: "Månad 6 till 18",
      title: "Rundhus & möten",
      copy:
        "Ett centrum som kan användas året runt växer fram för workshops, måltider, små kulturformat och regionala möten.",
      items: [
        "Planera och bygga ett rundhus på 15 meter",
        "Anlägga uteytor, stigar och sittplatser",
        "Starta de första bakdagarna, smidesdagarna och möteskvällarna",
      ],
    },
    {
      period: "År 2 till 3",
      title: "Bagerihus & smedja",
      copy:
        "Hantverk och kunskap blir ekonomiskt användbara genom kurser, försäljning, beställningsarbeten och dagsaktiviteter året runt.",
      items: [
        "Bagerihus med vedugn för kurser och gårdsförsäljning",
        "Smedja med säkerhetskoncept och kursverksamhet",
        "Integrera externa aktörer i de första formaten",
      ],
    },
    {
      period: "År 3 till 5",
      title: "Gästhus & längre vistelser",
      copy:
        "Fyra till fem små hus ökar kapacitet och vistelselängd, kompletterat med sanitetsbyggnad, stigar och vinterduglig infrastruktur.",
      items: [
        "Möjliggöra 10 till 15 övernattande gäster",
        "Placera husen naturnära i stället för som en stugby",
        "Stärka flerdagsturism och vintererbjudanden",
      ],
    },
    {
      period: "År 5 till 10",
      title: "Konsolidering & kvalitet",
      copy:
        "Gården växer inte till varje pris. Samarbeten, rutiner, återkommande gäster och regional förankring blir viktigare än expansion.",
      items: [
        "Optimera verksamheten och höja kvaliteten",
        "Bygga ut samarbeten och externa kursledare",
        "Komplettera med medarbetare först vid stabil efterfrågan",
      ],
    },
  ],
  en: [
    {
      period: "Month 0 to 6",
      title: "Acquisition & usability",
      copy:
        "Take over the farm, prepare well and wastewater systems for final expansion, complete the holiday house and enable first income.",
      items: [
        "Secure purchase and ownership",
        "Install water and wastewater systems",
        "Make the holiday house rentable in the first three months",
      ],
    },
    {
      period: "Month 6 to 18",
      title: "Roundhouse & encounters",
      copy:
        "A year-round center emerges for workshops, meals, small cultural formats and regional encounters.",
      items: [
        "Plan and build a 15-meter roundhouse",
        "Create outdoor areas, paths and seating",
        "Start first baking days, forging days and evening gatherings",
      ],
    },
    {
      period: "Years 2 to 3",
      title: "Bakehouse & forge",
      copy:
        "Craft and knowledge become economically usable through courses, sales, commissioned work and year-round day offers.",
      items: [
        "Bakehouse with wood-fired oven for courses and farm sales",
        "Forge with safety concept and course operation",
        "Integrate external providers into the first formats",
      ],
    },
    {
      period: "Years 3 to 5",
      title: "Guest houses & longer stays",
      copy:
        "Four to five small houses increase capacity and length of stay, complemented by a sanitary building, paths and winter-ready infrastructure.",
      items: [
        "Enable 10 to 15 overnight guests",
        "Place houses close to nature rather than like a cottage settlement",
        "Strengthen multi-day tourism and winter offers",
      ],
    },
    {
      period: "Years 5 to 10",
      title: "Consolidation & quality",
      copy:
        "The farm does not grow at any price. Partnerships, processes, returning guests and regional roots become more important than expansion.",
      items: [
        "Optimize operations and raise quality",
        "Expand partnerships and external course providers",
        "Add employees only when demand is stable",
      ],
    },
  ],
};

const pageLang = document.documentElement.lang.slice(0, 2);
const phases = phasesByLang[pageLang] ?? phasesByLang.de;

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

renderPhase(0);

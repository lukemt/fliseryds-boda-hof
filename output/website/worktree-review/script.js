const nav = document.querySelector("[data-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");
const lightbox = document.querySelector("[data-lightbox]");
const lightboxImage = document.querySelector("[data-lightbox-image]");
const lightboxCaption = document.querySelector("[data-lightbox-caption]");
const lightboxClose = document.querySelector("[data-lightbox-close]");

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

document.querySelectorAll("[data-gallery] button").forEach((button) => {
  button.addEventListener("click", () => {
    const image = button.querySelector("img");
    const caption = button.closest("figure")?.querySelector("figcaption")?.textContent ?? image?.alt ?? "";
    if (!image || !(lightbox instanceof HTMLDialogElement) || !lightboxImage || !lightboxCaption) return;

    lightboxImage.setAttribute("src", image.currentSrc || image.src);
    lightboxImage.setAttribute("alt", image.alt);
    lightboxCaption.textContent = caption;
    lightbox.showModal();
  });
});

lightboxClose?.addEventListener("click", () => {
  if (lightbox instanceof HTMLDialogElement) lightbox.close();
});

lightbox?.addEventListener("click", (event) => {
  if (event.target === lightbox && lightbox instanceof HTMLDialogElement) lightbox.close();
});

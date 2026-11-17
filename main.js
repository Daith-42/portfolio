// Portfolio David Ameline : menu mobile, téléphone masqué, section active.
// Menu mobile : un bouton qui déplie les liens de navigation.
const nav = document.getElementById('nav');
const menuBtn = document.querySelector('.menu-btn');
function setMenu(open) {
  nav.classList.toggle('is-open', open);
  menuBtn.setAttribute('aria-expanded', String(open));
  menuBtn.setAttribute('aria-label', open ? menuBtn.dataset.labelClose : menuBtn.dataset.labelOpen);
}
menuBtn.addEventListener('click', () => setMenu(!nav.classList.contains('is-open')));
nav.addEventListener('click', e => { if (e.target.closest('a')) setMenu(false); });
addEventListener('keydown', e => { if (e.key === 'Escape') setMenu(false); });

// Téléphone : absent du HTML pour les robots qui ramassent les numéros,
// reconstruit seulement quand un visiteur clique sur « Afficher le numéro ».
document.querySelectorAll('.reveal-phone').forEach(btn => {
  btn.addEventListener('click', () => {
    const intl = atob(btn.dataset.k).split('').reverse().join('');      // +33…
    const local = document.documentElement.lang === 'en'
      ? intl.replace(/^\+33(\d)(\d{2})(\d{2})(\d{2})(\d{2})$/, '+33 $1 $2 $3 $4 $5') // +33 7 66 … (format international)
      : ('0' + intl.slice(3)).replace(/(\d{2})(?=\d)/g, '$1 ');                         // 07 66 …
    const link = document.createElement('a');
    link.href = 'tel:' + intl;
    link.innerHTML = btn.innerHTML;
    link.querySelector('.val').textContent = local;
    btn.replaceWith(link);
    link.focus();
  });
});

// Souligne dans la navigation la section en cours de lecture.
const links = [...document.querySelectorAll('.nav a')];
const sections = links.map(a => document.getElementById(a.getAttribute('href').slice(1)));
let ticking = false;
function markCurrent() {
  ticking = false;
  const y = innerHeight * 0.4;
  let current = -1;
  sections.forEach((s, i) => { if (s && s.getBoundingClientRect().top <= y) current = i; });
  const contact = document.getElementById('contact');
  if (contact && contact.getBoundingClientRect().top <= y) current = -1;
  links.forEach((a, i) => i === current ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current'));
}
addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(markCurrent); } }, { passive: true });
markCurrent();

// Pop-ups de détails des projets (<dialog> natif : Échap, focus et retour du focus gérés par le navigateur).
document.querySelectorAll('[data-dialog]').forEach(opener => {
  const dialog = document.getElementById(opener.dataset.dialog);
  if (!dialog || typeof dialog.showModal !== 'function') return;
  opener.addEventListener('click', () => dialog.showModal());
  dialog.querySelectorAll('[data-close]').forEach(btn => btn.addEventListener('click', () => dialog.close()));
  // Un clic sur le fond assombri (hors de la fenêtre) ferme aussi.
  dialog.addEventListener('click', e => {
    if (e.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
    if (!inside) dialog.close();
  });
});

// Projets sur mobile : chaque carte se replie en accordéon (badges + titre), et s'ouvre au toucher.
// La classe .js active le repli : sans JavaScript, toutes les cartes restent ouvertes.
const projectList = document.querySelector('.projects');
if (projectList) {
  document.documentElement.classList.add('js');
  const labelMore = projectList.dataset.labelMore;
  const labelLess = projectList.dataset.labelLess;
  projectList.querySelectorAll(':scope > .project').forEach((card, i) => {
    const title = card.querySelector('h3');
    if (!title) return;
    if (!card.id) card.id = 'projet-' + (i + 1);
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'project-toggle';
    toggle.setAttribute('aria-controls', card.id);
    toggle.innerHTML = '<span></span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
    const label = toggle.querySelector('span');
    const setOpen = open => {
      card.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      label.textContent = open ? labelLess : labelMore;
    };
    setOpen(false);
    toggle.addEventListener('click', () => setOpen(!card.classList.contains('is-open')));
    title.after(toggle);
  });
}

// Changement de langue : l'autre page s'ouvre au même endroit, pas tout en haut.
// Les deux pages ont la même structure (l'anglaise est générée depuis la française) : on retient
// le bloc en haut de l'écran par son rang, et la position dans ce bloc (les textes n'ont pas la même longueur).
// La section part aussi dans l'adresse, au cas où le stockage du navigateur serait bloqué.
const LANG_KEY = 'lang-switch-pos';
const scrollOffset = () => parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
// Rang compté sur tous les blocs, même repliés (accordéon mobile), pour qu'il reste le même d'une page à l'autre.
const anchors = () => [...document.querySelectorAll('main h2, main h3, main p, main li, main .card')]
  .filter(el => !el.closest('dialog'));
document.querySelectorAll('.lang-switch').forEach(a => a.addEventListener('click', () => {
  if (scrollY < 10) return;
  const offset = scrollOffset();
  const list = anchors();
  let index = -1;
  list.forEach((el, i) => { if (el.offsetHeight > 0 && el.getBoundingClientRect().top <= offset + 1) index = i; });
  const el = list[index];
  const section = el && el.closest('section[id]');
  if (!section) return;
  const r = el.getBoundingClientRect();
  const ratio = Math.min(1, Math.max(0, (offset - r.top) / r.height));
  try { sessionStorage.setItem(LANG_KEY, JSON.stringify({ id: section.id, index, ratio })); } catch {}
  a.href = a.getAttribute('href').split('#')[0] + '#' + section.id;
}));
try {
  const saved = JSON.parse(sessionStorage.getItem(LANG_KEY) || 'null');
  sessionStorage.removeItem(LANG_KEY);
  let target = saved && location.hash === '#' + saved.id && anchors()[saved.index];
  while (target && target.offsetHeight === 0) target = target.parentElement; // bloc replié ici : on vise sa carte
  if (target) {
    const restore = () => {
      const top = target.getBoundingClientRect().top + scrollY + saved.ratio * target.offsetHeight - scrollOffset();
      scrollTo({ top, behavior: 'instant' });
    };
    restore();
    // Les polices peuvent encore décaler la page : on recale une fois chargées, si le visiteur n'a pas bougé.
    const y = scrollY;
    document.fonts && document.fonts.ready.then(() => { if (Math.abs(scrollY - y) < 2) restore(); });
  }
} catch {}

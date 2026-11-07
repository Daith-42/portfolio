// Portfolio David Ameline : menu mobile, téléphone masqué, section active.
// Menu mobile : un bouton qui déplie les liens de navigation.
const nav = document.getElementById('nav');
const menuBtn = document.querySelector('.menu-btn');
function setMenu(open) {
  nav.classList.toggle('is-open', open);
  menuBtn.setAttribute('aria-expanded', String(open));
  menuBtn.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
}
menuBtn.addEventListener('click', () => setMenu(!nav.classList.contains('is-open')));
nav.addEventListener('click', e => { if (e.target.closest('a')) setMenu(false); });
addEventListener('keydown', e => { if (e.key === 'Escape') setMenu(false); });

// Téléphone : absent du HTML pour les robots qui ramassent les numéros,
// reconstruit seulement quand un visiteur clique sur « Afficher le numéro ».
document.querySelectorAll('.reveal-phone').forEach(btn => {
  btn.addEventListener('click', () => {
    const intl = atob(btn.dataset.k).split('').reverse().join('');      // +33…
    const local = ('0' + intl.slice(3)).replace(/(\d{2})(?=\d)/g, '$1 '); // 07 66 …
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

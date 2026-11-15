/* ============================================================
   GamesT5 — app.js
   SPA com rotas em hash: #/ | #/jogo/{appid} | #/categoria/{slug}
   #/pesquisa/{q} | #/carrinho
   ============================================================ */
'use strict';

/* ---------------- utilidades ---------------- */
const $  = (s, el) => (el || document).querySelector(s);
const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
const app = $('#app');

const esc = s => String(s).replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));

const fmt = v => 'US$ ' + v.toFixed(2).replace('.', ',');
const fmtK = n => n >= 1e6 ? (n / 1e6).toFixed(1).replace('.', ',') + ' mi'
             : n >= 1e3 ? (n / 1e3).toFixed(1).replace('.', ',') + ' mil' : String(n);

/* ---------------- metadados de categorias ---------------- */
const CATS = {
  'anime':        { nome: 'Anime',        ic: '🌸' },
  'fps':          { nome: 'FPS',          ic: '🎯' },
  'corrida':      { nome: 'Corrida',      ic: '🏎️' },
  'rpg':          { nome: 'RPG',          ic: '⚔️' },
  'acao':         { nome: 'Ação',         ic: '💥' },
  'aventura':     { nome: 'Aventura',     ic: '🧭' },
  'terror':       { nome: 'Terror',       ic: '👻' },
  'esportes':     { nome: 'Esportes',     ic: '⚽' },
  'estrategia':   { nome: 'Estratégia',   ic: '♟️' },
  'simulacao':    { nome: 'Simulação',    ic: '🛠️' },
  'sobrevivencia':{ nome: 'Sobrevivência',ic: '🏕️' },
  'mundo-aberto': { nome: 'Mundo Aberto', ic: '🌍' },
  'battle-royale':{ nome: 'Battle Royale',ic: '🪂' },
  'luta':         { nome: 'Luta',         ic: '🥊' },
  'plataforma':   { nome: 'Plataforma',   ic: '🍄' },
  'roguelike':    { nome: 'Roguelike',    ic: '🎲' },
  'metroidvania': { nome: 'Metroidvania', ic: '🗺️' },
  'souls-like':   { nome: 'Souls-like',   ic: '🔥' },
  'puzzle':       { nome: 'Puzzle',       ic: '🧩' },
  'indie':        { nome: 'Indie',        ic: '✨' },
  'mmo':          { nome: 'MMO',          ic: '🌐' },
  'coop':         { nome: 'Co-op',        ic: '🤝' },
  'sandbox':      { nome: 'Sandbox',      ic: '🧱' },
  'zumbis':       { nome: 'Zumbis',       ic: '🧟' },
};
const CAT_NAV_ORDER = ['anime','fps','corrida','rpg','acao','aventura','terror','esportes',
  'estrategia','simulacao','sobrevivencia','mundo-aberto','battle-royale','luta','plataforma',
  'roguelike','metroidvania','souls-like','puzzle','indie','mmo','coop','sandbox','zumbis'];

const catNome = slug => (CATS[slug] || {}).nome || slug;
const catIc   = slug => (CATS[slug] || {}).ic || '🎮';

/* ---------------- imagens Steam CDN ---------------- */
const CDN = id => `https://cdn.cloudflare.steamstatic.com/steam/apps/${id}`;
const IMG = {
  header:   id => `${CDN(id)}/header.jpg`,
  capsule:  id => `${CDN(id)}/capsule_616x353.jpg`,
  hero:     id => `${CDN(id)}/library_hero.jpg`,
  portrait: id => `${CDN(id)}/library_600x900.jpg`,
};

function placeholder(name, w, h) {
  const ini = name.split(/\s+/).slice(0, 2).map(p => p[0] || '').join('').toUpperCase();
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">` +
    `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">` +
    `<stop offset="0" stop-color="#0b0e22"/><stop offset="1" stop-color="#1a0f33"/></linearGradient></defs>` +
    `<rect width="${w}" height="${h}" fill="url(#g)"/>` +
    `<rect x="4" y="4" width="${w - 8}" height="${h - 8}" fill="none" stroke="#00f0ff55" stroke-width="2" rx="10"/>` +
    `<text x="50%" y="46%" text-anchor="middle" font-family="Arial Black,Arial" font-size="${Math.round(h / 3.2)}" font-weight="900" fill="#00f0ffcc">${ini}</text>` +
    `<text x="50%" y="72%" text-anchor="middle" font-family="Arial" font-size="${Math.round(h / 12)}" fill="#ff2bd6cc">GamesT5</text></svg>`;
  return 'data:image/svg+xml,' + encodeURIComponent(svg);
}

/* cadeia de fallback de imagens: data-fb="url1|url2|..." */
window.G5_imgErr = function (img) {
  const fb = (img.dataset.fb || '').split('|').filter(Boolean);
  if (fb.length) {
    img.src = fb.shift();
    img.dataset.fb = fb.join('|');
  } else {
    img.onerror = null;
    img.src = placeholder(img.dataset.nome || 'G5', 460, 215);
  }
};

function imgTag(g, kind, cls) {
  const chain = [IMG[kind](g.appid)];
  ['header', 'capsule', 'hero'].forEach(k => { if (k !== kind) chain.push(IMG[k](g.appid)); });
  return `<img src="${chain.shift()}" data-fb="${chain.join('|')}" data-nome="${esc(g.nome)}"
    alt="${esc(g.nome)}" loading="lazy" onerror="G5_imgErr(this)">`;
}

/* ---------------- estado ---------------- */
const state = {
  games: [],
  byId: new Map(),
  cart: [],
  hero: { idx: 0, timer: null, list: [] },
  view: null, // estado da vista atual (paginacao, ordenacao...)
};

/* ---------------- carrinho ---------------- */
function loadCart() {
  try { state.cart = JSON.parse(localStorage.getItem('gt5cart') || '[]'); }
  catch { state.cart = []; }
}
function saveCart() { localStorage.setItem('gt5cart', JSON.stringify(state.cart)); updateBadge(); }
function cartAdd(id) {
  if (!state.cart.includes(id)) state.cart.push(id);
  saveCart();
  const g = state.byId.get(id);
  toast(`✅ ${g ? g.nome : 'Jogo'} adicionado ao carrinho`);
}
function cartRemove(id) { state.cart = state.cart.filter(x => x !== id); saveCart(); }
function updateBadge() {
  const b = $('#cartBadge');
  b.hidden = state.cart.length === 0;
  b.textContent = state.cart.length;
}

/* ---------------- toast / modal ---------------- */
function toast(msg) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = msg;
  $('#toastRoot').appendChild(el);
  setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 260); }, 2600);
}
function modal(html) {
  const root = $('#modalRoot');
  root.innerHTML = `<div class="modal-overlay" data-action="overlay-close"><div class="modal">
    <button class="modal-close" data-action="modal-close">✕</button>${html}</div></div>`;
}
function closeModal() { $('#modalRoot').innerHTML = ''; }

/* ---------------- componentes ---------------- */
function gameCard(g) {
  const pct = g.precoSteam > 0 ? Math.round((1 - g.preco / g.precoSteam) * 100) : 0;
  return `
  <article class="game-card">
    <a href="#/jogo/${g.appid}" aria-label="${esc(g.nome)}">
      <div class="card-media">
        <span class="off-badge">-${fmt(g.economia)}</span>
        <span class="card-cat">${catIc(g.cat)} ${catNome(g.cat)}</span>
        ${imgTag(g, 'header')}
      </div>
      <div class="card-body">
        <h3 class="card-name">${esc(g.nome)}</h3>
        <div class="card-meta">
          <span class="card-nota">${g.nota || '—'}</span>
          <span>${g.ano || ''}</span>
          <span>⭐ ${fmtK(g.reviews)}</span>
        </div>
        <div class="card-prices">
          <span class="old">${fmt(g.precoSteam)}</span>
          <span class="new">${fmt(g.preco)}</span>
          <span class="card-save">${pct > 0 ? '-' + pct + '%' : ''}</span>
        </div>
      </div>
    </a>
    <div style="padding:0 14px 14px">
      <button class="btn btn-neon btn-sm card-cta" data-action="add" data-id="${g.appid}">🛒 Comprar</button>
    </div>
  </article>`;
}

function rowSection(id, titulo, ic, games, link) {
  if (!games.length) return '';
  return `
  <section class="section">
    <div class="section-head">
      <h2 class="section-title"><span class="ic">${ic}</span>${titulo}</h2>
      <a class="section-link" href="${link}">ver tudo (${games.length})</a>
    </div>
    <div class="row-wrap">
      <button class="row-arrow prev" data-action="row-prev" data-row="${id}" aria-label="Anterior">‹</button>
      <div class="row" id="${id}">${games.slice(0, 14).map(gameCard).join('')}</div>
      <button class="row-arrow next" data-action="row-next" data-row="${id}" aria-label="Próximo">›</button>
    </div>
  </section>`;
}

const SORTS = {
  'pop':    { label: 'Mais populares',      fn: (a, b) => b.reviews - a.reviews },
  'nota':   { label: 'Melhor avaliados',    fn: (a, b) => b.nota - a.nota || b.reviews - a.reviews },
  'ano':    { label: 'Lançamentos recentes',fn: (a, b) => b.ano - a.ano || b.reviews - a.reviews },
  'eco':    { label: 'Maior economia',      fn: (a, b) => b.economia - a.economia || b.reviews - a.reviews },
  'preco-': { label: 'Preço: menor primeiro',fn: (a, b) => a.preco - b.preco },
  'preco+': { label: 'Preço: maior primeiro',fn: (a, b) => b.preco - a.preco },
};

function listView(titulo, ic, desc, games, defSort) {
  // restaura estado pendente (usado por "Carregar mais" e pela ordenação)
  const pending = state.pending || {};
  state.view = { sort: pending.sort || defSort || 'pop', visible: pending.visible || 24 };
  delete state.pending;
  const st = state.view;
  const sortKey = st.sort;
  const sorted = games.slice().sort(SORTS[sortKey].fn);
  const visible = sorted.slice(0, st.visible);
  return `
  <div class="page-head">
    <h1><span class="ic">${ic}</span>${titulo}</h1>
    ${desc ? `<p>${desc}</p>` : ''}
  </div>
  <div class="list-tools">
    <span class="count">${games.length} jogos encontrados</span>
    <select data-action="sort" aria-label="Ordenar por">
      ${Object.entries(SORTS).map(([k, v]) =>
        `<option value="${k}" ${k === sortKey ? 'selected' : ''}>${v.label}</option>`).join('')}
    </select>
  </div>
  ${visible.length ? `<div class="grid">${visible.map(gameCard).join('')}</div>` :
    `<div class="empty-search"><div class="big">🕳️</div><h3>Nenhum jogo encontrado</h3><p>Tente outra busca ou explore as categorias acima.</p></div>`}
  ${sorted.length > st.visible ? `<div style="text-align:center;margin-top:26px">
    <button class="btn btn-ghost" data-action="more">⬇️ Carregar mais (${sorted.length - st.visible} restantes)</button></div>` : ''}`;
}

/* ---------------- VISTA: início ---------------- */
function viewHome() {
  const g = state.games;
  const top = g.slice(0, 14);
  const byCat = (c, n) => g.filter(x => x.cats.includes(c)).slice(0, n);
  const heroes = g.filter(x => x.reviews > 60000).slice(0, 6);
  state.hero = { idx: 0, timer: null, list: heroes };
  const h = heroes[0];
  const catsComCount = CAT_NAV_ORDER.map(c => [c, g.filter(x => x.cats.includes(c)).length]);

  app.innerHTML = `
  <div class="dealbar"><div class="dealbar-track">
    ${(Array(2).fill(`<span>⚡ <b>US$ 30 MENOS</b> QUE NA STEAM EM TODOS OS JOGOS</span><span>🔑 CHAVES STEAM ORIGINAIS</span><span>💻 SOMENTE PC</span><span>⚡ ENTREGA INSTANTÂNEA</span><span>🌸 ANIME · 🏎️ CORRIDA · 🎯 FPS · ⚔️ RPG · 👻 TERROR</span>`)).join('')}
  </div></div>

  <div class="hero" id="heroBox">
    <div class="hero-bg" id="heroBg" style="background-image:url('${IMG.hero(h.appid)}'),url('${IMG.capsule(h.appid)}')"></div>
    <div class="hero-scan"></div>
    <button class="hero-arrow prev" data-action="hero-prev" aria-label="Anterior">‹</button>
    <button class="hero-arrow next" data-action="hero-next" aria-label="Próximo">›</button>
    <div class="hero-content">
      <span class="hero-kicker">🔥 EM ALTA NA INTERNET — SÓ NO GAMES T5</span>
      <h1 class="hero-title" id="heroTitle">${esc(h.nome)}</h1>
      <p class="hero-desc" id="heroDesc">${esc(h.desc)}</p>
      <div class="hero-actions">
        <div class="hero-price">
          <span class="old">${fmt(h.precoSteam)}</span>
          <span class="new" id="heroPrice">${fmt(h.preco)}</span>
        </div>
        <a class="btn btn-neon" href="#/jogo/${h.appid}">Ver oferta 🎮</a>
        <button class="btn btn-buy btn-sm" data-action="add" data-id="${h.appid}">🛒 Comprar agora</button>
      </div>
    </div>
    <div class="hero-dots" id="heroDots">
      ${heroes.map((x, i) => `<button class="hero-dot ${i === 0 ? 'active' : ''}" data-action="hero-dot" data-i="${i}" aria-label="Slide ${i + 1}"></button>`).join('')}
    </div>
  </div>

  <div class="stats">
    <div class="stat"><b>${g.length}+</b><span>JOGOS NO CATÁLOGO</span></div>
    <div class="stat"><b>${Object.keys(CATS).length}</b><span>CATEGORIAS</span></div>
    <div class="stat"><b>US$ 30</b><span>MENOS QUE A STEAM</span></div>
    <div class="stat"><b>24/7</b><span>SUPORTE E ENTREGA</span></div>
  </div>

  ${rowSection('rowTop', 'Em alta agora', '🔥', top, '#/categoria/ofertas')}
  ${rowSection('rowAnime', 'Anime — direto do Japão', '🌸', byCat('anime'), '#/categoria/anime')}
  ${rowSection('rowCorrida', 'Corrida & Velocidade', '🏎️', byCat('corrida'), '#/categoria/corrida')}
  ${rowSection('rowFPS', 'FPS — mira afiada', '🎯', byCat('fps'), '#/categoria/fps')}
  ${rowSection('rowTerror', 'Terror para jogar no escuro', '👻', byCat('terror'), '#/categoria/terror')}
  ${rowSection('rowEsportes', 'Esportes', '⚽', byCat('esportes'), '#/categoria/esportes')}

  <section class="save-banner">
    <h2>Por que comprar no <b>GamesT5</b>?</h2>
    <div class="big30">US$ 30</div>
    <p>É isso que você economiza em relação ao preço da Steam em cada jogo acima de US$ 30,99.<br>
    Jogos mais baratos? A partir de <strong style="color:var(--cyan)">US$ 0,99</strong>. Chaves originais, entrega instantânea, só para PC.</p>
    <div style="margin-top:18px"><a class="btn btn-neon" href="#/categoria/ofertas">Ver todas as ofertas 🔥</a></div>
  </section>

  ${rowSection('rowRPG', 'RPG & Aventura', '⚔️', byCat('rpg').concat(byCat('aventura')).slice(0, 14), '#/categoria/rpg')}
  ${rowSection('rowNovos', 'Lançamentos recentes', '🆕', g.slice().sort(SORTS['ano'].fn), '#/categoria/rpg')}

  <section class="section">
    <div class="section-head"><h2 class="section-title"><span class="ic">🧭</span>Navegue por categoria</h2></div>
    <div style="display:flex;flex-wrap:wrap;gap:10px">
      ${catsComCount.map(([c, n]) => `<a class="cat-chip" href="#/categoria/${c}">${catIc(c)} ${catNome(c)} <span class="n">${n}</span></a>`).join('')}
    </div>
  </section>`;
  startHeroTimer();
}

/* ---------------- hero carousel ---------------- */
function heroGo(i) {
  const H = state.hero;
  if (!H.list.length) return;
  H.idx = (i + H.list.length) % H.list.length;
  const g = H.list[H.idx];
  const bg = $('#heroBg'), t = $('#heroTitle'), d = $('#heroDesc'), p = $('#heroPrice');
  if (!bg) return;
  bg.style.backgroundImage = `url('${IMG.hero(g.appid)}'), url('${IMG.capsule(g.appid)}')`;
  t.textContent = g.nome;
  d.textContent = g.desc;
  p.textContent = fmt(g.preco);
  $$('#heroDots .hero-dot').forEach((el, k) => el.classList.toggle('active', k === H.idx));
  $$('.hero-content [data-id]').forEach(b => b.dataset.id = g.appid);
  $$('.hero-content a.btn')[0] && ($$('.hero-content a.btn')[0].href = '#/jogo/' + g.appid);
}
function startHeroTimer() {
  clearInterval(state.hero.timer);
  state.hero.timer = setInterval(() => heroGo(state.hero.idx + 1), 6500);
}

/* ---------------- VISTA: categoria / pesquisa / ofertas ---------------- */
function viewList(kind, param) {
  let games, titulo, ic, desc;
  if (kind === 'categoria') {
    if (param === 'ofertas') {
      titulo = 'Ofertas GamesT5'; ic = '🔥';
      desc = 'Todos os jogos com a economia calculada — de US$ 30 OFF (vs Steam) a preços a partir de US$ 0,99.';
      games = state.games.slice().sort(SORTS['eco'].fn);
    } else {
      const c = param;
      titulo = `${catIc(c)} ${catNome(c)}`; ic = catIc(c);
      games = state.games.filter(x => x.cats.includes(c));
      desc = `Os melhores jogos de ${catNome(c)} para PC — sempre abaixo do preço da Steam.`;
    }
  } else { // pesquisa
    const q = param.toLowerCase().trim();
    games = state.games.filter(x => x.nome.toLowerCase().includes(q) || catNome(x.cat).toLowerCase().includes(q));
    titulo = `Resultados para “${param}”`; ic = '🔎';
    desc = games.length ? `${games.length} jogos encontrados no catálogo GamesT5.` : '';
  }
  app.innerHTML = listView(titulo, ic, desc, games, kind === 'categoria' && param === 'ofertas' ? 'eco' : 'pop');
}

/* ---------------- VISTA: página do jogo ---------------- */
function viewGame(appid) {
  const g = state.byId.get(appid);
  if (!g) { view404(); return; }
  document.title = `${g.nome} — US$ ${fmt(g.preco)} no GamesT5 (US$ 30 menos que na Steam)`;

  const pct = g.precoSteam > 0 ? Math.round((1 - g.preco / g.precoSteam) * 100) : 0;
  const shots = ['capsule', 'header', 'hero', 'portrait'];
  const related = state.games.filter(x => x.cat === g.cat && x.appid !== g.appid).slice(0, 12);
  const alt = state.games.filter(x => x.cats.includes(g.cats[1] || '') && x.appid !== g.appid && !related.includes(x)).slice(0, 12);

  app.innerHTML = `
  <nav class="crumbs">
    <a href="#/">Início</a><span class="sep">›</span>
    <a href="#/categoria/${g.cat}">${catIc(g.cat)} ${catNome(g.cat)}</a><span class="sep">›</span>
    <span>${esc(g.nome)}</span>
  </nav>

  <div class="game-page">
    <div>
      <div class="gallery">
        <div class="main-shot" id="mainShot">${imgTag(g, 'hero')}</div>
        <div class="thumbs">
          ${shots.map((k, i) => `<button class="thumb ${i === 0 ? 'active' : ''}" data-action="thumb" data-src="${IMG[k](g.appid)}">
            <img src="${IMG[k](g.appid)}" onerror="this.parentNode.style.display='none'" alt="Imagem ${i + 1} de ${esc(g.nome)}" loading="lazy">
          </button>`).join('')}
        </div>
      </div>

      <div class="video-box">
        <h3>🎬 TRAILER & VÍDEOS</h3>
        <div class="video-frame">
          <iframe src="https://store.steampowered.com/widget/${g.appid}/" title="Trailer de ${esc(g.nome)} — Steam"
            loading="lazy" allowfullscreen sandbox="allow-scripts allow-same-origin allow-popups"></iframe>
        </div>
        <p class="video-note">O player oficial da Steam com o trailer do jogo. Não carregou?
          <a href="https://store.steampowered.com/app/${g.appid}" target="_blank" rel="noopener">Assistir na página da Steam ↗</a></p>
      </div>

      <div class="about-game">
        <h3>📄 SOBRE O JOGO</h3>
        <p>${esc(g.desc)}</p>
        ${g.tags && g.tags.length ? `<ul>${g.tags.map(t => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}
      </div>
    </div>

    <aside class="buybox">
      <h1 class="game-title">${esc(g.nome)}</h1>
      <div class="game-sub">
        <a class="tag-chip" href="#/categoria/${g.cat}">${catIc(g.cat)} ${catNome(g.cat)}</a>
        ${(g.cats.filter(c => c !== g.cat).slice(0, 2)).map(c => `<a class="tag-chip m" href="#/categoria/${c}">${catNome(c)}</a>`).join('')}
        <span class="tag-chip">${g.ano || 'PC'}</span>
        ${g.nota ? `<span class="nota-chip">★ ${g.nota}% positivo</span>` : ''}
      </div>

      <div class="price-card">
        <div class="price-row"><span>Preço na Steam:</span><span class="old">${fmt(g.precoSteam)}</span></div>
        <div class="price-row t5"><span>Aqui no GamesT5:</span><b>${fmt(g.preco)}</b></div>
        <span class="save-pill">💾 Você economiza ${fmt(g.economia)}${pct ? ` (-${pct}%)` : ''}</span>
      </div>

      <button class="btn btn-buy btn-lg" data-action="add" data-id="${g.appid}">🛒 Adicionar ao carrinho</button>
      <button class="btn btn-ghost btn-lg" data-action="go-cart">Ver carrinho 🧾</button>

      <div class="perks">
        <div><span class="p-ic">⚡</span> Entrega instantânea da chave por e-mail</div>
        <div><span class="p-ic">🔑</span> Chave Steam 100% original e global</div>
        <div><span class="p-ic">💻</span> Somente para PC (Windows) via Steam</div>
        <div><span class="p-ic">🛟</span> Suporte 24/7 e garantia GamesT5</div>
      </div>
      <p class="steam-ref">Referência oficial: <a href="https://store.steampowered.com/app/${g.appid}" target="_blank" rel="noopener">página do jogo na Steam ↗</a></p>
    </aside>
  </div>

  ${rowSection('rowRel', 'Jogos relacionados', catIc(g.cat), related.length ? related : alt, `#/categoria/${g.cat}`)}`;
}

/* ---------------- VISTA: carrinho ---------------- */
function viewCart() {
  const items = state.cart.map(id => state.byId.get(id)).filter(Boolean);
  if (!items.length) {
    app.innerHTML = `
    <div class="page-head"><h1><span class="ic">🧾</span> Seu carrinho</h1></div>
    <div class="cart-empty">
      <div class="big">🛒</div>
      <h3>Seu carrinho está vazio</h3>
      <p style="margin:10px 0 20px">Explore o catálogo e aproveite: tudo US$ 30 menos que na Steam!</p>
      <a class="btn btn-neon" href="#/">Ver jogos em alta 🔥</a>
    </div>`;
    return;
  }
  const totalSteam = items.reduce((s, g) => s + g.precoSteam, 0);
  const total = items.reduce((s, g) => s + g.preco, 0);
  const eco = totalSteam - total;
  app.innerHTML = `
  <div class="page-head"><h1><span class="ic">🧾</span> Seu carrinho</h1>
    <p>${items.length} jogo(s) — todos US$ 30 menos que na Steam (ou a partir de US$ 0,99)</p></div>
  <div class="cart-layout">
    <div class="cart-list">
      ${items.map(g => `
      <div class="cart-item">
        <a class="ci-img" href="#/jogo/${g.appid}">${imgTag(g, 'header')}</a>
        <div>
          <h4>${esc(g.nome)}</h4>
          <div class="ci-meta">${catIc(g.cat)} ${catNome(g.cat)} · ${g.ano || 'PC'} · Chave Steam (PC)</div>
        </div>
        <div class="ci-price">
          <b>${fmt(g.preco)}</b>
          <span class="ci-save">economiza ${fmt(g.economia)}</span>
          <button class="btn btn-danger btn-sm" style="margin-top:8px" data-action="remove" data-id="${g.appid}">Remover</button>
        </div>
      </div>`).join('')}
    </div>
    <aside class="summary">
      <h3>RESUMO DO PEDIDO</h3>
      <div class="s-row"><span>Preço na Steam:</span><b><s>${fmt(totalSteam)}</s></b></div>
      <div class="s-row"><span>Seu total no GamesT5:</span><b style="color:var(--cyan)">${fmt(total)}</b></div>
      <div class="s-row save"><span>Economia total:</span><b>-${fmt(eco)} 🎉</b></div>
      <div class="s-total"><span>Total</span><b>${fmt(total)}</b></div>
      <button class="btn btn-buy btn-lg" data-action="checkout">✅ Finalizar compra</button>
      <a class="btn btn-ghost" href="#/">Continuar comprando</a>
    </aside>
  </div>`;
}

function checkout() {
  const items = state.cart.map(id => state.byId.get(id)).filter(Boolean);
  const total = items.reduce((s, g) => s + g.preco, 0);
  const eco = items.reduce((s, g) => s + g.economia, 0);
  const code = 'GT5-' + Math.random().toString(36).slice(2, 8).toUpperCase();
  modal(`
    <div class="m-emoji">🎉</div>
    <h3>Pedido confirmado!</h3>
    <p>Compra de <strong>${items.length} jogo(s)</strong> no valor de <strong style="color:var(--cyan)">${fmt(total)}</strong> finalizada com sucesso.</p>
    <p style="margin-top:8px">💾 Você economizou <strong style="color:var(--lime)">${fmt(eco)}</strong> em relação à Steam.<br>
    As chaves Steam foram enviadas para o seu e-mail (simulado).</p>
    <div class="m-order">PEDIDO ${code}</div>
    <div class="m-actions">
      <button class="btn btn-neon" data-action="modal-close" style="flex:1">Continuar comprando</button>
    </div>`);
  state.cart = []; saveCart();
}

function view404() {
  app.innerHTML = `<div class="empty-search"><div class="big">👾</div>
  <h3>Ops! Página não encontrada</h3><p style="margin:12px 0 20px">O jogo que você procura pode ter voltado para a Dimensão 5.</p>
  <a class="btn btn-neon" href="#/">Voltar ao início</a></div>`;
}

/* ---------------- router ---------------- */
function route(keepScroll) {
  clearInterval(state.hero.timer);
  if (!state.games || !state.games.length) { // catálogo ainda carregando
    app.innerHTML = `<div class="loading">CARREGANDO CATÁLOGO NEON <span class="pulse"></span><span class="pulse"></span><span class="pulse"></span></div>`;
    return;
  }
  const hash = decodeURIComponent(location.hash.replace(/^#\/?/, ''));
  const [head, ...rest] = hash.split('/');
  const param = rest.join('/');
  if (!keepScroll) window.scrollTo({ top: 0 });
  document.title = 'GamesT5 — Jogos PC até US$ 30 mais baratos que na Steam';

  if (!head) { viewHome(); return; }
  if (head === 'jogo' && param) { viewGame(parseInt(param, 10)); return; }
  if (head === 'categoria' && param) { viewList('categoria', param); return; }
  if (head === 'pesquisa') { viewList('pesquisa', param || ''); return; }
  if (head === 'carrinho') { viewCart(); return; }
  view404();
}

/* ---------------- navegação fixa ---------------- */
function buildNav() {
  const counts = {};
  state.games.forEach(g => g.cats.forEach(c => { counts[c] = (counts[c] || 0) + 1; }));
  const nav = $('#catNav');
  nav.innerHTML = `<a class="cat-chip" href="#/">🏠 Início</a>` +
    CAT_NAV_ORDER.filter(c => counts[c]).map(c =>
      `<a class="cat-chip" href="#/categoria/${c}">${catIc(c)} ${catNome(c)} <span class="n">${counts[c] || 0}</span></a>`).join('');
  $('#footerCats').innerHTML = CAT_NAV_ORDER.filter(c => counts[c]).slice(0, 10).map(c =>
    `<a href="#/categoria/${c}">${catIc(c)} ${catNome(c)} (${counts[c]})</a>`).join('');
}
function markActiveCat() {
  const [, , param] = location.hash.split('/');
  $$('#catNav .cat-chip').forEach(a => a.classList.toggle('active',
    a.getAttribute('href') === location.hash && location.hash.startsWith('#/categoria/')));
  if (param) $$('#catNav .cat-chip').forEach(a =>
    a.classList.toggle('active', a.getAttribute('href') === `#/categoria/${param}`));
}

/* ---------------- eventos globais ---------------- */
document.addEventListener('click', e => {
  const el = e.target.closest('[data-action]');
  if (!el) return;
  const act = el.dataset.action;

  if (act === 'add') { e.preventDefault(); cartAdd(+el.dataset.id); }
  else if (act === 'remove') { cartRemove(+el.dataset.id); viewCart(); }
  else if (act === 'go-cart') location.hash = '#/carrinho';
  else if (act === 'checkout') checkout();
  else if (act === 'modal-close') closeModal();
  else if (act === 'overlay-close') { if (e.target === el) closeModal(); }
  else if (act === 'more') {
    state.pending = { sort: state.view.sort, visible: state.view.visible + 24 };
    route(true);
  }
  else if (act === 'row-prev')  $('#' + el.dataset.row).scrollBy({ left: -540, behavior: 'smooth' });
  else if (act === 'row-next')  $('#' + el.dataset.row).scrollBy({ left: 540, behavior: 'smooth' });
  else if (act === 'hero-prev') { heroGo(state.hero.idx - 1); startHeroTimer(); }
  else if (act === 'hero-next') { heroGo(state.hero.idx + 1); startHeroTimer(); }
  else if (act === 'hero-dot')  { heroGo(+el.dataset.i); startHeroTimer(); }
  else if (act === 'thumb') {
    $('#mainShot').innerHTML = `<img src="${el.dataset.src}" onerror="G5_imgErr(this)" data-nome="" alt="Imagem do jogo">`;
    $$('.thumb').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
  }
});

document.addEventListener('change', e => {
  if (e.target.matches('[data-action="sort"]')) {
    state.pending = { sort: e.target.value, visible: state.view.visible };
    route(true);
  }
});

$('#searchForm').addEventListener('submit', e => {
  e.preventDefault();
  const q = $('#searchInput').value.trim();
  if (q) location.hash = '#/pesquisa/' + encodeURIComponent(q);
});
$('#topDealBtn').addEventListener('click', () => { location.hash = '#/categoria/ofertas'; });

window.addEventListener('hashchange', route);

/* ---------------- boot ---------------- */
(async function init() {
  app.innerHTML = `<div class="loading">CARREGANDO CATÁLOGO NEON <span class="pulse"></span><span class="pulse"></span><span class="pulse"></span></div>`;
  try {
    const res = await fetch('data/games.json');
    state.games = await res.json();
    state.games.forEach(g => state.byId.set(g.appid, g));
  } catch (err) {
    app.innerHTML = `<div class="empty-search"><div class="big">⚠️</div><h3>Não foi possível carregar o catálogo</h3><p>${esc(String(err))}</p></div>`;
    return;
  }
  loadCart();
  buildNav();
  route();
  markActiveCat();
  window.addEventListener('hashchange', markActiveCat);
})();

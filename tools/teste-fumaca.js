/* Teste de fumaça do GamesT5 com jsdom — carrega a página real do servidor local. */
const { JSDOM, ResourceLoader } = require('jsdom');
const fs = require('fs');

const sleep = ms => new Promise(r => setTimeout(r, ms));

class LocalOnly extends ResourceLoader {
  fetch(url, options) {
    if (url.startsWith('http://localhost:3000')) {
      const p = url.replace('http://localhost:3000', '/home/user/Gui').split('?')[0];
      try { return Promise.resolve(Buffer.from(fs.readFileSync(p))); }
      catch { return Promise.resolve(Buffer.from('')); }
    }
    if (url.startsWith('file://')) return super.fetch(url, options);
    return Promise.resolve(Buffer.from('')); // ignora fontes/CDNs externos
  }
}

(async () => {
  const gamesData = fs.readFileSync('/home/user/Gui/data/games.json', 'utf8');
  const dom = await JSDOM.fromFile('/home/user/Gui/index.html', {
    url: 'http://localhost:3000/',
    runScripts: 'dangerously',
    resources: new LocalOnly(),
    pretendToBeVisual: true,
    beforeParse(window) {
      window.fetch = (u) => {
        const path = String(u).replace(/^https?:\/\/localhost:3000/, '').replace(/^(?!\/)/, '/');
        const body = path === '/data/games.json' ? gamesData : null;
        return Promise.resolve({
          ok: !!body, status: body ? 200 : 404,
          json: async () => body ? JSON.parse(body) : null,
          text: async () => body,
        });
      };
    },
  });
  const { window } = dom;
  const { document } = window;
  await sleep(400);
  // espera o catálogo carregar de fato
  for (let i = 0; i < 30 && !document.querySelectorAll('.game-card').length; i++) await sleep(100);
  const waitFor = async (fn, tries) => {
    for (let i = 0; i < (tries || 30); i++) { if (fn()) return true; await sleep(80); }
    return false;
  };
  const go = async (hash, fn) => { window.location.hash = hash; return waitFor(fn); };

  const results = [];
  const check = (nome, cond) => { results.push([cond ? 'PASS' : 'FAIL', nome]); console.log(cond ? 'PASS' : 'FAIL', '—', nome); };
  window.addEventListener('error', e => console.log('WINDOW ERROR:', e.message));

  // ---------- home ----------
  check('home: cards renderizados', document.querySelectorAll('.game-card').length >= 40);
  check('home: nav de categorias', document.querySelectorAll('#catNav .cat-chip').length > 10);
  check('home: hero presente', !!document.querySelector('.hero-title'));
  check('home: marquee US$ 30', document.body.textContent.includes('US$ 30 MENOS'));
  const badge = document.querySelector('#cartBadge');

  // ---------- página do jogo ----------
  await go('#/jogo/1245620', () => document.title.includes('ELDEN RING'));
  check('jogo: título atualizado (Elden Ring)', document.title.includes('ELDEN RING'));
  check('jogo: buybox com preço', document.body.textContent.includes('Aqui no GamesT5:'));
  check('jogo: economia US$ 30,00', document.body.textContent.includes('US$ 30,00'));
  check('jogo: trailer iframe Steam', !!document.querySelector('.video-frame iframe[src*="store.steampowered.com"]'));
  check('jogo: thumbs de imagens', document.querySelectorAll('.thumb').length === 4);
  check('jogo: relacionados', document.querySelectorAll('#rowRel .game-card').length >= 4);

  // ---------- categoria ----------
  await go('#/categoria/anime', () => document.querySelectorAll('.game-card').length >= 20);
  check('categoria anime: resultados', document.querySelectorAll('.game-card').length >= 20);
  check('categoria anime: título', document.body.textContent.includes('Anime'));

  // ---------- ordenação + carregar mais ----------
  await go('#/categoria/fps', () => document.querySelectorAll('.game-card').length >= 20);
  const before = document.querySelectorAll('.game-card').length;
  const moreBtn = document.querySelector('[data-action="more"]');
  if (moreBtn) {
    moreBtn.click();
    await waitFor(() => document.querySelectorAll('.game-card').length > before);
    const after = document.querySelectorAll('.game-card').length;
    check('carregar mais: aumenta a lista', after > before);
  } else check('carregar mais: botão presente', false);

  // ---------- pesquisa ----------
  await go('#/pesquisa/' + encodeURIComponent('dragon'), () => document.querySelectorAll('.game-card').length >= 3);
  check('pesquisa: acha Dragon Ball', document.querySelectorAll('.game-card').length >= 3);

  // ---------- carrinho ----------
  await go('#/', () => !!document.querySelector('.game-card [data-action="add"]'));
  const buy = document.querySelector('.game-card [data-action="add"]');
  if (!buy) { console.log('DEBUG: hash =', window.location.hash, '| title =', document.title, '| cards =', document.querySelectorAll('.game-card').length, '| body[0..300] =', document.body.textContent.slice(0, 300)); process.exit(3); }
  buy.click();
  await sleep(50);
  const cart = JSON.parse(window.localStorage.getItem('gt5cart') || '[]');
  check('carrinho: item adicionado', cart.length === 1);
  check('carrinho: badge visível', badge.hidden === false && badge.textContent === '1');
  await go('#/carrinho', () => document.querySelectorAll('.cart-item').length === 1);
  check('carrinho: página lista item', document.querySelectorAll('.cart-item').length === 1);
  check('carrinho: resumo com economia', document.body.textContent.includes('Economia total'));
  document.querySelector('[data-action="checkout"]').click();
  await sleep(50);
  check('checkout: modal de confirmação', document.body.textContent.includes('Pedido confirmado!'));
  check('checkout: carrinho limpo', JSON.parse(window.localStorage.getItem('gt5cart')).length === 0);

  // ---------- imagens Steam ----------
  await go('#/', () => !!document.querySelector('.card-media img'));
  const img = document.querySelector('.card-media img');
  check('imagens: URL Steam CDN correta', !!img && (img.getAttribute('src') || '').includes('cdn.cloudflare.steamstatic.com/steam/apps/'));

  // ---------- regra de preço ----------
  const G5 = JSON.parse(gamesData);
  const okPrice = G5.every(g => g.precoSteam - g.preco >= 29.99 || g.preco === 0.99);
  check('regra: US$ 30 menos (mín. 0,99)', okPrice);

  let fail = 0;
  for (const [st, nome] of results) { console.log(st, '—', nome); if (st === 'FAIL') fail++; }
  console.log(fail === 0 ? '\nTODOS OS TESTES PASSARAM ✔' : `\n${fail} teste(s) FALHARAM ✘`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('ERRO NO TESTE:', e); process.exit(2); });

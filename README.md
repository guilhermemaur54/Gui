# 🎮 GamesT5 — Store Neon

Loja de jogos para PC com **tema neon**, estilo arcade futurista, que vende **todos os tipos de jogos em alta na internet** — anime, corrida, FPS, RPG, terror, esportes e muito mais.

> 💎 **Regra de ouro da loja:** todo jogo custa **US$ 30,00 menos que o preço da Steam** (mínimo US$ 0,99). Somente jogos de PC disponíveis na Steam.

## ✨ Funcionalidades

- **599 jogos famosos** no catálogo, em **22 categorias** (Anime 🌸, FPS 🎯, Corrida 🏎️, RPG ⚔️, Terror 👻, Battle Royale 🪂, Souls-like 🔥, Luta 🥊, Esportes ⚽…)
- **Página própria para cada jogo** (`#/jogo/{appid}`) com:
  - Galeria de imagens (capsule, header, library hero e portrait) servidas do CDN oficial da Steam com *fallback* automático
  - **Trailer/vídeo oficial** embutido via widget da Steam
  - Ficha de preço: preço Steam riscado, preço GamesT5 neon e selo "Você economiza US$ 30,00"
  - Descrição em português, recursos (co-op, conquistas, controle…), jogos relacionados
- **Home neon** com carrossel hero, marquee de ofertas, fileiras por categoria, estatísticas e banner de economia
- **Busca instantânea** por nome e **navegação por categoria** com contadores
- **Ordenação** (populares, melhor avaliados, lançamentos, maior economia, preço) e **paginação "Carregar mais"**
- **Carrinho** com persistência (localStorage), resumo de economia total e checkout simulado com número de pedido
- Design 100% responsivo (desktop, tablet, telemóvel)

## 🚀 Como rodar

É um site 100% estático — qualquer servidor de arquivos funciona:

```bash
python3 -m http.server 3000
# ou
npx serve .
```

Depois abra `http://localhost:3000`.

## 🗂️ Estrutura

```
index.html          → página única (SPA) com rotas em hash
css/style.css       → tema neon completo
js/app.js           → roteador, catálogo, carrinho, galeria, busca
data/games.json     → catálogo gerado (599 jogos)
tools/gerar_catalogo.py → gerador do catálogo a partir do dataset Steam
tools/teste-fumaca.js   → teste de fumaça (jsdom) das rotas, carrinho e regras
```

## 📊 Dados do catálogo

Gerados a partir do dataset público **Steam Games Dataset 2024** (Kaggle, ~71 mil jogos — espelho em `github.com/Darakuu/FAD_SteamGames_2025`), com:

- Seleção dos títulos mais populares por categoria (por nº de reviews da Steam)
- Jogos famosos ausentes do dataset adicionados manualmente (ELDEN RING, Sekiro, Cuphead, Marvel's Spider-Man 1/2, Battlefield 1/V/2042, S.T.A.L.K.E.R. 2, NIGHTREIGN)
- Exclusão de demos, DLCs, soundtracks, apps não-game, conteúdo adulto e jogos gratuitos
- Preço de referência em USD + cálculo GamesT5 (`preço − 30`, piso `0,99`)
- Descrições manuais para ~100 títulos famosos + templates em português por categoria

Para regenerar:

```bash
python3 tools/gerar_catalogo.py /caminho/steam_games.csv
```

## 🧪 Testes

```bash
npm i jsdom   # no diretório de testes
node tools/teste-fumaca.js
```

Cobre: renderização da home, página do jogo (título, buybox, trailer, thumbs, relacionados), categorias, ordenação, "carregar mais", busca, carrinho (adicionar, badge, resumo, checkout) e a regra de preços.

## ⚖️ Nota

Loja fictícia de demonstração. Preços de referência da loja americana da Steam (USD). Imagens e vídeos © dos respectivos estúdios, servidos diretamente pelos servidores da Steam/Valve.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GamesT5 — gerador do catálogo de jogos (data/games.json).

Fonte: dataset público "Steam Games Dataset 2024" (Kaggle, espelhado em
github.com/Darakuu/FAD_SteamGames_2025 -> src/steam_games.csv, ~71k jogos).

Uso:
    python3 tools/gerar_catalogo.py /caminho/steam_games.csv

Regras do site:
  * Somente jogos pagos para PC (Windows) lançados na Steam;
  * Preço GamesT5 = preço Steam - US$ 30,00 (mínimo US$ 0,99);
  * Catálogo de 500+ títulos famosos balanceado por categoria
    (anime, fps, corrida, rpg, terror, ...).
"""
import csv, ast, json, re, sys, os, unicodedata

csv.field_size_limit(10**8)
SRC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/steam_games.csv'
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'games.json')

NON_GAME_GENRES = {
    'Animation & Modeling','Design & Illustration','Photo Editing','Utilities',
    'Web Publishing','Game Development','Audio Production','Video Production',
    'Education','Software Training','Accounting','Movie','Documentary','Episodic',
    'Short','Tutorial','Free to Play','Nudity','Sexual Content','Hentai',
}
JUNK_NAME = re.compile(
    r'\b(demo|playtest|dlc|soundtrack|ost|sdk|dedicated server|beta test|'
    r'test server|expansion pack|art book|wallpaper|closed testing|'
    r'sound track|upgrade pack|playable teaser)\b', re.I)

def parse_list(s):
    try:
        v = ast.literal_eval(s)
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []

def norm(t):
    t = unicodedata.normalize('NFKD', t)
    return ''.join(c for c in t if not unicodedata.combining(c)).lower()

# ------------------------------------------------------------------ 1. parse
games = {}
with open(SRC, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        try:
            appid = int(row['steam_appid'])
            price = float(row['price_initial (USD)'] or 0)
            revs = int(row['total_reviews'] or 0)
        except Exception:
            continue
        if row['is_released'] != 'True' or row['is_free'] == 'True': continue
        if price < 1.99 or 'windows' not in row['platforms']: continue
        # OBS: a coluna required_age deste dataset está corrompida (valores não
        # são idades), por isso não filtramos por ela. Conteúdo adulto já é
        # excluído pelos gêneros 'Nudity'/'Sexual Content'/'Hentai' abaixo.
        if 'Sexual Content' in row['categories'] or 'Hentai' in row['genres'] or 'Nudity' in row['genres']:
            continue
        # Correção de preços errados no dataset (is_free=False mas preço 0)
        PRICE_FIX = {271590: 29.99}  # Grand Theft Auto V
        if price < 1.99 and appid in PRICE_FIX:
            price = PRICE_FIX[appid]
        genres = [g for g in parse_list(row['genres']) if g not in NON_GAME_GENRES]
        if not genres: continue
        name = row['name'].strip()
        if not name or JUNK_NAME.search(name): continue
        if not row['categories']: continue
        g = {'appid': appid, 'nome': name, 'price': price, 'revs': revs,
             'genres': genres, 'cats_raw': parse_list(row['categories']),
             'dev': (parse_list(row['developers']) or ['—'])[0][:40],
             'nota': float(row['positive_percentual'] or 0)}
        m = re.match(r'(\d{4})-', row['release_date'])
        g['ano'] = int(m.group(1)) if m else 0
        key = norm(re.sub(r'[^\w\s]', '', name))
        if key not in games or games[key]['revs'] < revs:
            games[key] = g

# ------------------------------------------------------------------ extras
# Jogos famosos ausentes do dataset, adicionados manualmente (appids verificados).
EXTRA = {
 1245620: dict(nome='ELDEN RING', price=59.99, ano=2022, cat='souls-like',
   cats={'souls-like','rpg','mundo-aberto','acao'}, revs=700000, nota=92, dev='FromSoftware',
   cats_raw=['Single-player','Multi-player','Co-op','Steam Achievements','Full controller support']),
 814380: dict(nome='Sekiro: Shadows Die Twice - GOTY Edition', price=59.99, ano=2019, cat='souls-like',
   cats={'souls-like','acao','aventura'}, revs=260000, nota=95, dev='FromSoftware',
   cats_raw=['Single-player','Steam Achievements','Full controller support']),
 268910: dict(nome='Cuphead', price=19.99, ano=2017, cat='plataforma',
   cats={'plataforma','acao','indie','coop'}, revs=120000, nota=96, dev='StudioMDHR',
   cats_raw=['Single-player','Co-op','Steam Achievements','Full controller support']),
 1817070: dict(nome="Marvel's Spider-Man Remastered", price=59.99, ano=2022, cat='mundo-aberto',
   cats={'mundo-aberto','acao','aventura'}, revs=95000, nota=95, dev='Nixxes Software',
   cats_raw=['Single-player','Steam Achievements','Full controller support','Steam Cloud']),
 2651280: dict(nome="Marvel's Spider-Man 2", price=59.99, ano=2025, cat='mundo-aberto',
   cats={'mundo-aberto','acao','aventura'}, revs=30000, nota=92, dev='Nixxes Software',
   cats_raw=['Single-player','Steam Achievements','Full controller support']),
 1517290: dict(nome='Battlefield 2042', price=59.99, ano=2021, cat='fps',
   cats={'fps','acao','coop'}, revs=150000, nota=55, dev='DICE',
   cats_raw=['Multi-player','Online PvP','Co-op','Steam Achievements']),
 1238810: dict(nome='Battlefield V', price=39.99, ano=2018, cat='fps',
   cats={'fps','acao','coop'}, revs=130000, nota=68, dev='DICE',
   cats_raw=['Multi-player','Online PvP','Co-op','Steam Achievements']),
 1238840: dict(nome='Battlefield 1', price=19.99, ano=2016, cat='fps',
   cats={'fps','acao','coop'}, revs=120000, nota=78, dev='DICE',
   cats_raw=['Multi-player','Online PvP','Co-op','Steam Achievements']),
 1643320: dict(nome='S.T.A.L.K.E.R. 2: Heart of Chornobyl', price=59.99, ano=2024, cat='fps',
   cats={'fps','sobrevivencia','terror','mundo-aberto'}, revs=80000, nota=79, dev='GSC Game World',
   cats_raw=['Single-player','Steam Achievements','Full controller support']),
 2622380: dict(nome='ELDEN RING NIGHTREIGN', price=39.99, ano=2025, cat='souls-like',
   cats={'souls-like','acao','coop'}, revs=45000, nota=74, dev='FromSoftware',
   cats_raw=['Multi-player','Co-op','Online Co-Op','Steam Achievements']),
}
for appid, e in EXTRA.items():
    if appid in games: continue
    games[appid] = {'appid': appid, 'nome': e['nome'], 'price': e['price'], 'revs': e['revs'],
        'genres': [], 'cats_raw': e['cats_raw'], 'dev': e['dev'], 'nota': e['nota'],
        'ano': e['ano'], '_extra': True, '_cat': e['cat'], '_cats': e['cats']}

# ------------------------------------------------------------------ 2. categorias
ANIME = ['dragon ball','naruto','boruto','one piece','attack on titan','shingeki','demon slayer',
 'kimetsu','jujutsu kaisen','my hero academia','one\'s justice','persona','sword art online',
 'fairy tail','bleach','jojo\'s bizarre','gundam','yu-gi-oh','digimon','danganronpa',
 'doki doki literature','hyperdimension neptunia','neptunia','senran kagura','tales of',
 'code vein','nier','drakengard','guilty gear','blazblue','melty blood','under night',
 'granblue','fate/stay','fate extella','fate grand order','fate/samurai','steins;gate','steins gate',
 'clannad','kanon','little busters','atelier','trails of cold steel','the legend of heroes',
 'disgaea','monster hunter','mobile suit','one punch man','seven deadly sins','nanatsu',
 'tokyo ghoul','fire force','hatsune miku','kantai collection','azur lane','mega man','megaman',
 'shin megami tensei','nocturne','soul hackers','rune factory','story of seasons','harvest moon',
 'sakuna','mary skelter','criminal girls','nekopara','huniepop','sekai project','akiba',
 'shin chan','doraemon','saint seiya','inuyasha','golden kamuy','haikyu','kill la kill',
 'gurren lagann','re:zero','konosuba','overlord','youjo senki','eiyuden','suikoden',
 'dynasty warriors','samurai warriors','warriors orochi','pirate warriors','xenoverse','kakarot',
 'fighterz','jump force','project x zone','shantae','idea factory','compile heart','nis america',
 'xseed games','marvelous','kadokawa','spike chunsoft','arc system works','bushiroad','dmm games',
 'gust','falcom','atlus','vanillaware','13 sentinels','odin sphere','unicorn overlord',
 'dragon quest','final fantasy','octopath','star ocean','valkyria chronicles','higurashi',
 'umineko','planetarian','muv-luv','chaos;head','robotics;notes','zero escape','somnium files',
 'yuzusoft','toradora','angel beats','va-11','storm 4','ultimate ninja']

FIGHTING = ['street fighter','tekken','mortal kombat','guilty gear','blazblue','king of fighters',
 'injustice','dead or alive','soulcalibur','soul calibur','virtua fighter','melty blood',
 'skullgirls','brawlhalla','fighterz','under night','samurai shodown','granblue fantasy versus',
 'punch planet','mma','ufc','wwe','aew','netherrealm','wrestling','boxing','kung fu','karate',
 'fightin\' herds','rivals of aether','all-star brawl','battle for the grid','footsies','fighting']

FPS = ['call of duty','counter-strike','battlefield','doom','halo','destiny 2','overwatch',
 'borderlands','metro','wolfenstein','payday','left 4 dead','back 4 blood','rainbow six',
 'escape from tarkov','tarkov','ready or not','titanfall','half-life','black mesa','the finals',
 'xdefiant','roboquest','dusk','amid evil','boltgun','darktide','vermintide','deep rock galactic',
 'killing floor','pavlov','cry of fear','superhot','serious sam','painkiller','quake',
 'unreal tournament','shooter','first-person','dying light','far cry','bioshock',
 'deus ex','system shock','prey','dishonored','arma','squad','insurgency','hell let loose',
 'post scriptum','rising storm','red orchestra','day of defeat','swat','s.t.a.l.k.e.r.','stalker',
 'chernobylite','crysis','f.e.a.r.','robocop']

TERROR = ['resident evil','silent hill','dead by daylight','phasmophobia','outlast','amnesia',
 'soma','layers of fear','five nights','fnaf','bendy','poppy playtime','little nightmares',
 'alan wake','dead space','alien isolation','darkwood','devour','lethal company','madison',
 'the evil within','visage','horror','halloween','slasher','creepy','nightmare','haunted',
 'pacify','blair witch','inside the backrooms','forewarned','demonologist','ghost watchers',
 'in silence','labyrinthine','dark deception','specimen zero','home sweet home','araya',
 'still wakes the deep','mortuary','the quarry','frank stone','chilla','forensic','don\'t escape',
 'exorcist','psychological horror']

SOBREV = ['rust','ark','valheim','the forest','sons of the forest','green hell','7 days to die',
 'subnautica','don\'t starve','raft','grounded','conan exiles','dayz','survival','stranded deep',
 'v rising','enshrouded','icarus','the long dark','project zomboid','this war of mine','frostpunk',
 'scum','miscreated','h1z1','generation zero','the isle','path of titans','beasts of bermuda',
 'medieval dynasty','bellwright','nightingale','abiotic factor','the planet crafter','palworld']

BATTLE = ['battle royale','pubg','fall guys','apex legends','warzone','super animal royale',
 'stumble guys','crab game','ultimate chicken horse','naraka']

SOULS = ['dark souls','demon\'s souls','elden ring','sekiro','lies of p','nioh','wo long',
 'lords of the fallen','the surge','remnant','code vein','blasphemous','thymesia','steelrising',
 'mortal shell','salt and sanctuary','dragon\'s dogma','first berserker','khazan','wuchang',
 'stellar blade','phantom blade']

METROIDVANIA = ['metroidvania','hollow knight','ori and','blasphemous','dead cells','axiom verge',
 'ender lilies','nine sols','grimvalor','castlevania','bloodstained','prince of persia',
 'islets','haiku the robot','sheepo','oshiro','record of lodoss','foregone','bzzzt']

ROGUE = ['roguelike','roguelite','rogue-lite','hades','risk of rain','slay the spire',
 'binding of isaac','enter the gungeon','ftl','darkest dungeon','vampire survivors',
 'balatro','noita','skul','curse of the dead gods','gunfire reborn','brotato','spelunky',
 'wizard of legend','moonlighter','undermine','crown trick','one step from eden','loop hero',
 'rogue legacy','hotline miami','nuclear throne','streets of rogue','dungeon of the endless',
 'for the king','death road to canada','descenders','peglin']

CORRIDA_KW = ['f1','forza','need for speed','trackmania','assetto corsa','project cars',
 'dirt','colin mcrae','wrc','motogp','moto gp','nascar','formula','burnout','grid','hot wheels',
 'art of rally','carx','drift','racing','race','kart','crazy taxi','road redemption','distance',
 'redout','xenon racer','speedway','mudrunner','snowrunner','the crew','le mans','my summer car',
 'mon bazou','wreckfest','beamng','jdm']

PLATAFORMA = ['celeste','ori and','rayman','sonic','cuphead','shovel knight','katana zero',
 'a hat in time','psychonauts','inside','limbo','braid','fez','super meat boy','crypt of the necrodancer',
 'double dragon','castlevania','mega man','trine','crash bandicoot','spyro','yooka','platformer',
 'jumper','antonblast','pizza tower','penarium','neon abyss','dandara','gris','the messenger',
 'blue fire','haiku the robot','spelunky','dead cells','rogue legacy']

MUNDO = ['open world','grand theft auto','gta','watch dogs','assassin\'s creed','far cry',
 'horizon','ghost of tsushima','cyberpunk 2077','the witcher','red dead redemption','mad max',
 'just cause','sleeping dogs','yakuza','like a dragon','days gone','dying light','state of decay',
 'saints row','mafia','no man\'s sky','elder scrolls','skyrim','oblivion','fallout','mount & blade',
 'kingdom come','dragon\'s dogma','sea of thieves','skull and bones','atlas','starfield',
 'the elder scrolls','baldur\'s gate']

ZUMBI = ['zombie','dead island','left 4 dead','world war z','dying light','days gone',
 'state of decay','overkill','killing floor','7 days to die','how to survive',
 'no more room in hell','undead','night of the dead','yet another zombie','the walking dead',
 'back 4 blood','they are billions','into the dead']

PUZZLE = ['portal','tetris','baba is you','the witness','monument','human fall flat','chuchel',
 'botanicula','machinarium','samorost','world of goo','limbo','inside','the room','unravel',
 'a little to the left','unpacking','wilmot','dorfromantik','islanders','townscaper','shapez',
 'hexcells','stephen\'s sausage','hidden object','match 3','mahjong','sudoku','solitaire',
 'the talos principle','superliminal','puzzle']

SANDBOX = ['garry\'s mod','minecraft','sandbox','space engineers','medieval engineers',
 'brick rigs','scrap mechanic','people playground','teardown','trailmakers','besiege',
 'instruments of destruction','wobbly life','gmod']

CATWORDS = {
 'anime': ANIME, 'luta': FIGHTING, 'fps': FPS, 'terror': TERROR, 'sobrevivencia': SOBREV,
 'battle-royale': BATTLE, 'souls-like': SOULS, 'metroidvania': METROIDVANIA, 'roguelike': ROGUE,
 'corrida': CORRIDA_KW, 'plataforma': PLATAFORMA, 'mundo-aberto': MUNDO, 'zumbis': ZUMBI,
 'puzzle': PUZZLE, 'sandbox': SANDBOX,
}
RE_WORDS = {}
for c, words in CATWORDS.items():
    parts = []
    for w in sorted(set(words), key=len, reverse=True):
        wn = norm(w)
        if re.search(r'[ /\'\-:;.]', wn):
            parts.append(re.escape(wn))
        else:
            parts.append(r'(?<![a-z0-9])' + re.escape(wn) + r'(?![a-z0-9])')
    RE_WORDS[c] = re.compile('|'.join(parts))

GENRE2CAT = {'sports':'esportes','racing':'corrida','massively multiplayer':'mmo',
 'strategy':'estrategia','simulation':'simulacao','rpg':'rpg','action':'acao',
 'adventure':'aventura','puzzle':'puzzle','indie':'indie'}

PRIO = ['battle-royale','anime','souls-like','metroidvania','luta','fps','terror','zumbis',
 'sobrevivencia','corrida','esportes','roguelike','plataforma','mundo-aberto','rpg','mmo',
 'estrategia','simulacao','puzzle','sandbox','aventura','acao','coop','indie']

def catset(g):
    blob = norm(g['nome'] + ' | ' + ' | '.join(g['genres']) + ' | ' + ' | '.join(g['cats_raw'])
                + ' | ' + g['dev'])
    cats = set()
    for c, rx in RE_WORDS.items():
        if rx.search(blob): cats.add(c)
    for gr in g['genres']:
        c = GENRE2CAT.get(norm(gr))
        if c: cats.add(c)
    nc = [norm(c) for c in g['cats_raw']]
    if any('co-op' in x or x == 'multi-player' or 'pvp' in x for x in nc): cats.add('coop')
    return cats

for g in games.values():
    if g.get('_extra'):
        g['cats'] = g['_cats']; g['cat'] = g['_cat']
    else:
        g['cats'] = catset(g)
        g['cat'] = next((p for p in PRIO if p in g['cats']), 'acao')

# ------------------------------------------------------------------ 3. seleção
QUOTAS = {'anime':65,'fps':45,'rpg':45,'acao':45,'corrida':32,'terror':30,'estrategia':30,
 'simulacao':30,'aventura':28,'esportes':26,'sobrevivencia':26,'mundo-aberto':22,'plataforma':20,
 'luta':20,'roguelike':18,'puzzle':18,'metroidvania':14,'souls-like':14,'battle-royale':12,
 'zumbis':14,'mmo':18,'sandbox':12}

by_cat = {}
for g in games.values():
    if g['revs'] >= 3:
        by_cat.setdefault(g['cat'], []).append(g)

picked = {}
def take(cat, n):
    pool = sorted(by_cat.get(cat, []), key=lambda x: (-x['revs'], -x['ano']))
    chosen = 0
    for g in pool:
        if g['appid'] in picked: continue
        picked[g['appid']] = g; chosen += 1
        if chosen >= n: break

for c in sorted(QUOTAS, key=lambda k: QUOTAS[k]):
    take(c, QUOTAS[c])
take('anime', 10); take('corrida', 8); take('metroidvania', 6)
resto = sorted((g for g in games.values() if g['appid'] not in picked), key=lambda x: -x['revs'])
for g in resto:
    if len(picked) >= 570: break
    if g['revs'] >= 40: picked[g['appid']] = g

print('selecionados:', len(picked))
cnt = {}
for g in picked.values(): cnt[g['cat']] = cnt.get(g['cat'], 0) + 1
print('por cat:', dict(sorted(cnt.items(), key=lambda kv: -kv[1])))

FAMOUS = ['ELDEN RING','CYBERPUNK','BLACK MYTH','PALWORLD','HOGWARTS','BALDUR','GRAND THEFT AUTO',
 'RED DEAD','DRAGON BALL','NARUTO','FORZA','EA SPORTS FC','RESIDENT EVIL','MONSTER HUNTER',
 'PERSONA','FINAL FANTASY','HOLLOW KNIGHT','TEKKEN','MORTAL KOMBAT','STREET FIGHTER','HALO',
 'ASSASSIN','TOMB RAIDER','GOD OF WAR','SPIDER-MAN','GHOST OF TSUSHIMA','STARFIELD','BATTLEFIELD',
 'VALHEIM','RUST','TERRARIA','STARDEW','HADES','CELESTE','CUPHEAD']
names = {norm(g['nome']) for g in picked.values()}
print('famosos ausentes:', [f for f in FAMOUS if not any(norm(f) in n for n in names)])

# ------------------------------------------------------------------ 4. descrições
HAND = {
271590:"Explore Los Santos e Blaine County no fenômeno do mundo aberto da Rockstar. Assaltos ousados, perseguições alucinantes, GTA Online com conteúdo constante e uma das histórias mais premiadas dos videogames.",
1174180:"A épica história do forasteiro Arthur Morgan no crepúsculo do Velho Oeste. Mundo aberto gigantesco, gráficos de tirar o fôlego e a narrativa magistral da Rockstar em Red Dead Redemption 2.",
1091500:"Night City te espera em Cyberpunk 2077: RPG de mundo aberto da CD Projekt Red onde você é um mercenário cibernético atrás do implante lendário. Gráficos de nova geração e uma cidade viva de verdade.",
1245620:"Erga-se, Maculado. ELDEN RING é o RPG de ação em mundo aberto da FromSoftware com direção de mundo de George R. R. Martin. Torrent, masmorras colossais e chefes devastadores no melhor jogo da geração.",
1086940:"O RPG definitivo da Larian: Baldur's Gate 3 venceu o GOTY 2023 com liberdade total de escolha, combate tático baseado em D&D 5e, cooperativo online e companheiros inesquecíveis.",
990080:"Viva seus primeiros anos em Hogwarts em um mundo aberto mágico: aprenda feitiços, domine o voo de vassoura, enfrente magos das trevas e descubra os segredos do castelo.",
1623730:"Capture Pals, construa sua base e sobreviva no fenômeno viral Palworld — mundo aberto de sobrevivência e criação de criaturas com combate, fazendas, armas e multiplayer.",
553850:"HELLDIVERS 2: junte-se à democracia gerenciada neste cooperativo de tiro que virou fenômeno mundial. Estratégia, humor e explosões em equipe de até 4 jogadores.",
2195250:"EA SPORTS FC 24 traz mais de 19 mil jogadores licenciados, HyperMotionV e o Ultimate Team mais realista de sempre. O futebol como você conhece, agora com o nome FC.",
2669320:"EA SPORTS FC 25: a nova geração do futebol virtual com FC IQ, modo Rush 5v5 e jogabilidade ainda mais fluida. Milhares de clubes, ligas e jogadores autênticos.",
1551360:"Dirija pelo vibrante México em Forza Horizon 5 — o festival de corrida em mundo aberto mais bonito já feito. Centenas de carros, clima dinâmico e multiplayer sem parar.",
105600:"Cave, construa, lute e explore em Terraria: o sandbox 2D de aventura com milhares de itens, chefes épicos e mundo gerado infinitamente. Uma obra-prima com mais de uma década de atualizações gratuitas.",
413150:"Herde a fazenda do avô e construa sua nova vida em Stardew Valley: vida no campo, mineração, pesca, romance e mistério no RPG de fazenda mais amado da Steam.",
252490:"Só os fortes sobrevivem em Rust: o multiplayer de sobrevivência implacável onde você constrói, saqueia e enfrenta outros jogadores num mundo hostil e sem piedade.",
739630:"Cace fantasmas com até 3 amigos em Phasmophobia: o cooperativo de terror psicológico com equipamento paranormal realista que definiu o gênero no PC.",
381210:"Sobreviva ao massacre ou seja o Assassino em Dead by Daylight: 4v1 assimétrico de terror com dezenas de assassinos icônicos e cruzamentos com clássicos do cinema.",
1145360:"Desafie o deus dos mortos em Hades: o roguelike de ação premiado da Supergiant onde cada fuga do Submundo te deixa mais forte. Combate frenético e narrativa brilhante.",
367520:"Explore as ruínas de um reino de insetos em Hollow Knight: metroidvania desenhado à mão com combate preciso, chefes memoráveis e um dos mundos mais bonitos dos indies.",
945360:"Descubra quem é o impostor em Among Us: o jogo social de dedução e sabotagem que uniu a internet. Partidas de 4 a 15 jogadores online ou local.",
1097150:"Cai, rola e sobreviva! Fall Guys é a battle royale de plataformas mais divertida do PC, com dezenas de minijogos caóticos para até 60 jogadores.",
582010:"Cace criaturas colossais, forje equipamentos lendários e defenda Astera em Monster Hunter: World — a caçada definitiva com mundo vivo e cooperação para 4 caçadores.",
1446780:"Monster Hunter Rise: caçadas verticais com o Wirebug, Palamutes e caçadas frenéticas. O hunt mais ágil da série, com cooperação online e a expansão Sunbreak.",
524220:"NieR:Automata — a obra-prima de Yoko Taro. 2B, 9S e A2 lutam pelos androides numa narrativa filosófica com dezenas de finais e um dos melhores soundtracks já compostos.",
1687950:"Vista a máscara do Fantasma de Tóquio: Persona 5 Royal é o JRPG estiloso por excelência, com vida de estudante, palácios oníricos e mais de 100 horas de estilo impecável.",
814380:"Honra inquebrável em Sekiro: Shadows Die Twice — o GOTY 2019 da FromSoftware. Shinobi com gancho de garra, sistema de postura e duelos de espada letais no Japão feudal fantasioso.",
374320:"O fim do fogo. Dark Souls III encerra a trilogia com combate afiado, chefes icônicos e Lothric em chamas. Prepare-se para morrer, Undongo.",
570940:"Retorne a Lordran na remasterização do clássico que criou um gênero. Dark Souls Remastered com 60fps, multiplayer e a tensão de sempre.",
2358720:"Enfrente o Rei Macaco em Black Myth: Wukong — a sensação chinesa de ação baseada em Jornada ao Oeste, com gráficos UE5, transformações e chefes espetaculares.",
2050650:"O remake definitivo de Resident Evil 4: Leon Kennedy resgata a filha do presidente numa aldeia possuída. Terror de ação reinventado com o RE Engine.",
631560:"DRAGON BALL FighterZ: o jogo de luta 2.5D da Arc System Works com combos aéreos cinematográficos e o visual de anime mais fiel já feito. Escolha seu time de 3 guerreiros Z.",
851850:"Reviva o mangá inteiro em DRAGON BALL Z: KAKAROT — do Saiyan ao Buu, com RPG de mundo aberto, treinos, pescarias e as batalhas mais épicas de Goku.",
454650:"Defenda a linha do tempo em DRAGON BALL XENOVERSE 2: crie seu personagem, junte-se ao Time Patrol e lute online com dezenas de transformações.",
633230:"NARUTO TO BORUTO: SHINOBI STRIKER — multiplayer 4v4 online com ninjas, jutsus e o universo Boruto. Crie seu próprio shinobi e domine os elementos.",
349040:"NARUTO SHIPPUDEN: Ultimate Ninja STORM 4 — a batalha final da saga com o maior elenco da série, combates cinematográficos e as guerras ninjas mais épicas.",
1088710:"Zarpe com o Chapéu de Palha em One Piece: Pirate Warriors 4 — musou com 4 jogadores, arco de Wano e os golpes mais icônicos do anime.",
1490570:"Demon Slayer -Kimetsu no Yaiba- The Hinokami Chronicles: reviva o anime com gráficos impressionantes e duelos de nichirin nos modos História e Versus.",
1384160:"GUILTY GEAR -STRIVE-: o versus-fighting da Arc System Works com rock pesado, sistema de roman cancel e netcode impecável. O rei dos jogos de luta modernos.",
1113560:"NieR Replicant ver.1.22474487139...: a origem da série, remasterizada. Um irmão em busca da cura da irmã num mundo à beira do colapso — narrativa que ninguém esquece.",
606360:"Tales of Arise: o JRPG da banda dupla entre Dahna e Rena, com combate linear fluido, personagens carismáticos e visual de anime em Unreal Engine.",
1462040:"FINAL FANTASY VII REMAKE INTERGRADE: Midgar reimaginada em escala espetacular, combate híbrido ação/comando e o episódio INTERmission com Yuffie.",
1172380:"Um Padawan sobrevivente da Ordem 66. Star Wars Jedi: Fallen Order — aventura de ação estilo metroidvania com sabre de luz e o droide BD-1.",
1774580:"Star Wars Jedi: Survivor: cinco anos depois, Cal Kestis enfrenta o Império com novas forças, o planeta Koboh e combate de sabre expandido.",
2369390:"Far Cry 6: liberte Yara do tirano Antón Castillo (Giancarlo Esposito) com armas improvisadas, fórmula suprema e co-op online no mundo aberto caribenho.",
552520:"Far Cry 5: Hope County, Montana, sob o culto de Eden's Gate. O mundo aberto mais reativo da série, com co-op e o melhor editor de mapas.",
812140:"Assassin's Creed Odyssey: torne-se um lendário espartano na Grécia Antiga — guerra do Peloponeso, escolhas narrativas, navio próprio e um dos maiores mapas da série.",
2208920:"Assassin's Creed Valhalla: lidere invasões vikings na Inglaterra da era das trevas. Saques, raids, Asgard e RPG de mundo aberto gigantesco.",
582160:"Assassin's Creed Origins: o nascimento da Irmandade no Egito Ptolomaico. Bayek e Senu num mundo aberto deslumbrante que reinventou a série.",
750920:"Shadow of the Tomb Raider: o final da trilogia de origem de Lara Croft na América Latina. Sobrevivência, tumbas lendárias e a transformação em Tomb Raider.",
391220:"Rise of the Tomb Raider: Lara na Sibéria atrás da fonte imortal. Sobrevivência extrema, cavernas crípticas e visuais premiados.",
203160:"Tomb Raider (2013): o renascimento de Lara Croft. Naufrágio, sobrevivência brutal e a origem da maior exploradora dos videogames.",
1259420:"Days Gone: dois anos após uma pandemia, o caçador de recompensas Deacon St. John enfrenta hordas de Freakers na natureza selvagem do Oregon.",
1151640:"Horizon Zero Dawn: Aloy caça máquinas-feras gigantes num mundo pós-apocalíptico exuberante. Premiadíssimo, com a expansão The Frozen Wilds.",
2215430:"Ghost of Tsushima DIRECTOR'S CUT: defenda Tsushima da invasão mongol como o Fantasma. Combate de katana, vento-guia e o modo Legends multiplayer.",
1817070:"Marvel's Spider-Man Remastered: balançar por Nova York nunca foi tão bom. Peter Parker contra o Sexteto Sinistro com os visuais do PC e DLSS.",
1593500:"God of War: Kratos e Atreus nas terras nórdicas. Câmera contínua, machado Leviatã e uma das melhores histórias de pai e filho já contadas.",
1659420:"UNCHARTED: Legacy of Thieves Collection: Chloe e Nadine partem para a Índia em busca do Presa de Ganesha — a produção cinematográfica da Naughty Dog no PC.",
1190460:"Death Stranding: conecte uma América fragmentada como Sam Porter Bridges. O jogo mais estranho e belo de Hideo Kojima, agora em versão definitiva.",
292030:"O RPG que definiu uma geração: The Witcher 3 Wild Hunt, com Geralt de Rivia, Blood and Wine e Hearts of Stone. Mais de 800 prêmios de Jogo do Ano.",
377160:"Fallout 4: saia do Vault 111 para o Commonwealth. Construção de assentamentos, power armor, Dogmeat e centenas de horas de pós-apocalipse.",
275850:"No Man's Sky: 18 quintilhões de planetas procedurais, construção de bases, VR e anos de atualizações gratuitas. Explore, negocie, lute e sobreviva no universo.",
489830:"The Elder Scrolls V: Skyrim Special Edition: o Dragonborn, fus roh dah e centenas de mods. O RPG de fantasia mais influente de todos os tempos.",
208650:"Batman: Arkham Knight: Gotham sob ameaça do Cavaleiro de Espinhos. Batmóvel dirigível, Freeflow Combat e o final da trilogia da Rocksteady.",
234140:"Mad Max: sobreviva à Terra Devastada com o Interceptor, combate veicular brutal e fortalezas no deserto pós-apocalíptico dos filmes.",
307690:"Sleeping Dogs Definitive Edition: Wei Shen se infiltra nas Tríades de Hong Kong. Combate marcial, perseguições e uma das cidades mais vibrantes do gênero.",
638970:"Yakuza 0: Kamurocho e Sotenbori nos anos 80, os primórdios de Kiryu e Majima. Brawling estilizado, karaoke, negócios imobiliários e pura emoção japonesa.",
1230810:"Yakuza: Like a Dragon — Ichiban Kasuga, o herói mais improvável de Yokohama, num RPG por turnos com classes malucas, humor e muito drama.",
1030840:"Mafia: Definitive Edition: a recriação completa de Lost Heaven nos anos 30. A ascensão de Tommy Angelo no crime organizado, remade pela Hangar 13.",
360430:"Mafia III: New Bordeaux, 1968. Lincoln Clay vinga sua família contra a máfia de Marcano no mundo aberto mais adulto da série.",
517630:"Just Cause 4: Rico Rodriguez e o gancho asa na fictícia Solís. Tornados, tempestades e destruição total em mundo aberto.",
218620:"PAYDAY 2: reúna a gangue e planeje o assalto perfeito. Cooperativo de 4 jogadores com centenas de heists, armas e builds — um clássico do co-op no PC.",
976730:"Halo: The Master Chief Collection: a saga completa do Master Chief — de Combat Evolved a Reach, com multiplayer clássico e 60fps no PC.",
1240440:"Halo Infinite: o Master Chief contra o Banished em Zeta Halo, com o gancho de garra e o multiplayer mais fluido da série.",
1517290:"Battlefield 2042: guerra total com 128 jogadores, tornados dinâmicos e Specialists em mapas gigantescos.",
1238810:"Battlefield V: Volta à Segunda Guerra com fortificações, esquadrões e o modo Firestorm battle royale nos cenários mais destrutíveis.",
1238840:"Battlefield 1: as trincheiras da Primeira Guerra Mundial como nunca vistas — cavalaria, zepelins e operações épicas com 64 jogadores.",
311210:"Call of Duty: Black Ops III: campanha futurista, Zombies completo e o multiplayer mais jogado da franquia no PC.",
1174370:"STAR WARS Battlefront II: heróis, naves e as três eras de Star Wars. Modos multiplayer gigantes e a campanha de Iden Versio.",
548430:"Deep Rock Galactic: 4 anões mineradores em cavernas procedurais alienígenas. Co-op total, Rock and Stone! O co-op FPS mais querido da Steam.",
892970:"Valheim: o décimo mundo nórdico. Viking de sobrevivência em cooperação — construa salões, derrote Eikthyr e navegue pelos mares do mundo.",
1203620:"Enshrouded: sobreviva no mundo voxel de Embervale, construa fortalezas e desça às Shrouds em cooperação com até 16 jogadores.",
242760:"The Forest: seu filho desaparece após um acidente de avião numa península canibal. Sobrevivência, construção de bases e horror com IA impecável.",
1326470:"Sons of the Forest: a sequência do survival horror da Endnight. Nova ilha, canibais mais inteligentes, Kelvin, Virgínia e terror em co-op.",
346110:"ARK: Survival Evolved: dome dinossauros, construa tribos e sobreviva na ilha. Mais de 100 criaturas e mapas de expansão lendários.",
322330:"Don't Starve Together: o co-op gótico de sobrevivência da Klei. Fome, loucura e criaturas de pesadelo com arte inconfundível.",
648800:"Raft: sobreviva no mar com uma balsa em expansão. Pesca, mergulho, ilhas e co-op com amigos no survival mais tenso-relaxante do PC.",
962130:"Grounded: encolhido ao tamanho de uma formiga no quintal. Sobrevivência com aranhas gigantes, bases em garrafas e co-op de 4.",
526870:"Satisfactory: construa fábricas colossais num planeta alienígena em primeira pessoa. O simulador de automação da Coffee Stain com esteiras infinitas.",
427520:"Factorio: lance o foguete automatizando tudo. A obra-prima do factory sim — blueprints, trens infinitos e lógica industrial pura.",
281990:"Stellaris: o grand strategy espacial da Paradox. Construa um império galáctico, encontre leviatãs e domine a Via Láctea.",
236850:"Europa Universalis IV: o grand strategy definitivo de 1444 a 1821. Comércio, diplomacia, guerra e a reescrita da história mundial.",
289070:"Sid Meier's Civilization VI: construa um império que resista ao tempo. Cidades com distritos, maravilhas, multiplayer e 6 modos de vitória.",
1466860:"Age of Empires IV: o RTS lendário renasce com 8 civilizações, campanhas cinematográficas e multiplayer competitivo da Microsoft.",
813780:"Age of Empires II: Definitive Edition: o RTS mais amado remasterizado em 4K, com novas civilizações e multiplayer ativo décadas depois.",
39210:"FINAL FANTASY XIV Online: o MMORPG premiado com a melhor história da série. Eorzea, raids de 24 pessoas, jobs únicos e a expansão Endwalker.",
1627720:"Lies of P: Pinóquio sombrio na Belle Époque da cidade de Krat. Soulslike afiado com armas montáveis e uma história sobre mentiras e humanidade.",
1501750:"Lords of the Fallen: duas realidades — Axiom e Umbral. Soulslike com combate pesado, lanterna mística e cooperação completa.",
1448440:"Wo Long: Fallen Dynasty: a Team Ninja na China dos Três Reinos. Combate de espada chinês, demônios e o espírito divino ao seu lado.",
1325200:"Nioh 2: um caçador de yokai no Japão Sengoku. Ki, posturas e a profundidade do combate da Team Ninja no soulslike mais técnico.",
251570:"7 Days to Die: o survival zumbi com hordas a cada 7 dias. Construa, minere, defenda — agora na versão 1.0 após uma década de atualizações.",
227300:"Euro Truck Simulator 2: entregas pela Europa em caminhões licenciados. Relaxamento total, DLCs de mapas e a maior comunidade de mods de simuladores.",
864380:"BeamNG.drive: a simulação de física veicular mais realista do mundo — cada amassado, suspensão e motor simulado em tempo real. Sandbox de crashes único.",
244210:"Assetto Corsa: a simulação de corrida mais precisa do PC. Física de cronômetro, carros licenciados e milhares de mods da comunidade.",
960090:"Bloons TD 6: a tower defense mais popular do PC — macacos, heróis, boss events e centenas de mapas em 3D.",
322170:"Geometry Dash: um toque, ritmo e mortes infinitas. O platformer de ritmo mais desafiador do PC, com editor de níveis da comunidade.",
412410:"Danganronpa 1•2 Reload: os julgamentos de assassinato da Hope's Peak Academy. Visual novel de mistério, desespero e personagens inesquecíveis.",
550:"Left 4 Dead 2: o co-op zombie shooter da Valve que nunca morre. 4 sobreviventes, hordas de Infectados e o Versus mais divertido da história.",
359550:"Tom Clancy's Rainbow Six Siege: o tático 5v5 com destruição ambiental — ataque e defesa, operators únicos e o FPS mais estratégico do esports.",
1174370:"STAR WARS Battlefront II: de Podrace a Endor — heróis, veículos e as três eras de Star Wars no multiplayer mais bonito da galáxia.",
268910:"Cuphead: ação e plataformas desenhadas à mão no estilo cartoon dos anos 30, com boss fights absurdos e trilha jazzística ao vivo. Dificuldade lendária, charme infinito — inclui The Delicious Last Course.",
2651280:"Marvel's Spider-Man 2: Peter Parker e Miles Morales juntos contra Venom e Kraven. Duas aranhas, Nova York expandida e o balanço mais espetacular já feito.",
1643320:"S.T.A.L.K.E.R. 2: Heart of Chornobyl: volte à zona de exclusão num FPS de sobrevivência brutal, com A-Life 2.0, artefatos mutantes e um dos mundos mais imersivos do ano.",
2622380:"ELDEN RING NIGHTREIGN: o novo capítulo co-op da FromSoftware. Expedições de 3 jogadores, heróis únicos e o combate soulslike mais rápido já feito nas Terras Intermédias reimaginadas.",
}

CAT_ORDER = ['anime','fps','corrida','rpg','acao','aventura','terror','esportes','estrategia',
 'simulacao','sobrevivencia','mundo-aberto','battle-royale','luta','plataforma','roguelike',
 'metroidvania','souls-like','puzzle','sandbox','zumbis','mmo','coop','indie']

TMPL = {
 'anime':["{n} traz a energia do anime direto para o PC: combates estilizados, personagens carismáticos e a fidelidade visual que os fãs esperam.",
  "Em {n}, você mergulha numa história no melhor estilo japonês, com animações de alta qualidade, trilha sonora marcante e batalhas épicas.",
  "Fãs de anime, atenção: {n} entrega ação intensa, gráficos vibrantes e momentos icônicos recriados com carinho — um dos títulos japoneses mais procurados do PC."],
 'fps':["{n} coloca você no centro do tiroteio: armas realistas, mapas competitivos e partidas que exigem reflexo e estratégia.",
  "Precisão, ritmo e adrenalina. Em {n}, cada partida é diferente: evolua sua build, domine os mapas e mostre sua mira.",
  "Prepare a mira: {n} entrega ação em primeira pessoa com progressão de armas, modos variados e comunidade gigante no PC."],
 'rpg':["{n} é um RPG profundo com progressão de personagem, escolhas que moldam a história e um mundo repleto de segredos.",
  "Monte sua build, evolua habilidades e tome decisões que mudam o destino do mundo em {n} — RPG de outro nível.",
  "{n} combina exploração, diálogos ramificados e evolução constante: o RPG perfeito para se perder por dezenas de horas."],
 'acao':["{n} é ação pura: combates intensos, cenários espetaculares e momentos de tirar o fôlego do início ao fim.",
  "Em {n}, cada encontro é um teste de reflexo e estratégia. Combate afiado, visuais impactantes e ritmo alucinante.",
  "Explosões, perseguições e combates memoráveis: {n} entrega a dose perfeita de ação no PC."],
 'aventura':["Explore um mundo cheio de mistérios em {n}: quebra-cabeças, descobertas e uma narrativa que prende do começo ao fim.",
  "{n} é uma jornada inesquecível por cenários deslumbrantes, com exploração recompensadora e personagens marcantes.",
  "Aventure-se em {n}: segredos escondidos, paisagens incríveis e uma história que evolui a cada capítulo."],
 'terror':["Apague a lanterna... {n} é terror puro: atmosfera opressiva, sustos inteligentes e tensão que não te solta até o final.",
  "{n} é o jogo de terror que a internet está jogando: suspense psicológico, som impecável e cenários que arrepian.",
  "Se você gosta de medo de verdade, {n} entrega: atmosfera sombria, inimigos aterrorizantes e suspense de outro nível."],
 'corrida':["Acelere! {n} traz física realista, carros lendários e circuitos desafiadores para os amantes de velocidade.",
  "{n} coloca você ao volante dos maiores carros do mundo, com personalização completa e sensação de velocidade impecável.",
  "Velocidade, derrapagem e pódios: {n} é uma das experiências de corrida mais completas do PC."],
 'esportes':["{n} traz o esporte com máxima fidelidade: times licenciados, física realista e modos competitivos para jogar com os amigos.",
  "Sinta o estádio! {n} entrega gráficos de nova geração, jogabilidade refinada e todas as equipes que você conhece.",
  "Campeonatos, carreira e online competitivo: {n} é a escolha número um para fãs de esporte no PC."],
 'estrategia':["Comande exércitos e construa impérios em {n}: decisões táticas, gerenciamento de recursos e batalhas épicas.",
  "{n} desafia sua mente: planeje cada movimento, pesquise tecnologias e derrote adversários na estratégia mais completa.",
  "Um lance errado e o reino cai: {n} é estratégia pura, com profundidade infinita e partidas inesquecíveis."],
 'simulacao':["{n} é a simulação definitiva: realismo impressionante, controle total e horas de gameplay relaxante ou desafiador.",
  "Sinta o realismo de {n}: mecânicas detalhadas, cenários fiéis ao mundo real e uma comunidade apaixonada.",
  "Do planejamento à execução, {n} simula cada detalhe com precisão — o favorito dos fãs de simuladores."],
 'sobrevivencia':["Colete, construa, sobreviva. {n} desafia você a permanecer vivo num mundo hostil, sozinho ou com amigos.",
  "Em {n}, cada recurso importa: monte sua base, enfrente criaturas e veja quanto tempo você aguenta.",
  "{n} é sobrevivência bruta: fome, clima, inimigos e outros jogadores — o teste definitivo dos seus nervos."],
 'mundo-aberto':["Um mundo gigante para explorar em {n}: missões secundárias, segredos, veículos e liberdade total.",
  "{n} é liberdade em forma de jogo: mundo aberto repleto de atividades, história marcante e dezenas de horas de conteúdo.",
  "Do horizonte aos detalhes: {n} entrega um dos mundos abertos mais ricos do PC, com exploração recompensadora."],
 'battle-royale':["100 entram, 1 sai. {n} é battle royale no estado puro: zona encolhendo, loot estratégico e tiro no último segundo.",
  "{n} é o battle royale que domina as streams: partidas tensas, competitivo acirrado e vitórias para gritar.",
  "Pouse, saqueie, sobreviva: {n} traz a fórmula battle royale com mecânicas únicas e comunidade gigante."],
 'luta':["{n} é luta de verdade: frames apertados, combos criativos e competitivo online acirrado. Escolha seu lutador e domine o ringue.",
  "Perfeição em cada golpe: {n} é o jogo de luta que os profissionais escolhem, com netcode sólido e roster repleto de estilos.",
  "Prepare os dedos: {n} entrega versus-fighting de altíssimo nível, com tutoriais profundos e comunidade ativa."],
 'plataforma':["Salte, desvie e repita: {n} é platforming de alta precisão com level design brilhante e dificuldade justa.",
  "{n} traz a nostalgia das plataformas modernizada: controles precisos, trilha excelente e fases criativas.",
  "Um platformer para todos os níveis: {n} é fácil de aprender, difícil de dominar e impossível de largar."],
 'roguelike':["Morra, aprenda, repita: {n} é o roguelike viciante que transforma cada derrota em progresso. Builds novas a cada run.",
  "{n} renasce a cada partida: aleatoriedade inteligente, builds criativas e o famoso 'só mais uma run' que vira madrugada.",
  "O roguelike do momento: {n} combina ação rápida, sinergias absurdas e desafio constante."],
 'metroidvania':["Explore, desbloqueie, volte: {n} é metroidvania de manual, com mapa interconectado e segredos em cada canto.",
  "{n} é a exploração em estado puro: habilidades que abrem caminhos, chefes memoráveis e um mundo feito para surpreender.",
  "Labirintos, segredos e progressão perfeita: {n} é uma aula de metroidvania para quem ama explorar."],
 'souls-like':["Prepare-se para morrer. {n} é soulslike com combate punitivo, chefes colossais e a recompensa mais doce do PC: vencer.",
  "{n} desafia seus reflexos e sua paciência: combate preciso, boss fights épicos e atmosfera sombria impecável.",
  "Cada vitória tem gosto de conquista: {n} é o soulslike que os fãs de desafio esperavam."],
 'puzzle':["Enigmas brilhantes esperam por você em {n}: lógica, criatividade e a satisfação única de resolver o impossível.",
  "{n} é o puzzle game que faz o cérebro ferver: mecânicas inovadoras, dificuldade progressiva e soluções elegantes.",
  "Pense fora da caixa: {n} reinventa o gênero puzzle com desafios inteligentes e apresentação impecável."],
 'sandbox':["Sem regras, sem limites: {n} é sandbox criativo onde a única fronteira é sua imaginação. Construa, destrua, experimente.",
  "{n} é o playground definitivo do PC: física maluca, ferramentas infinitas e momentos hilários — sozinho ou com amigos.",
  "Crie seu próprio divertimento em {n}: sandbox aberto com possibilidades infinitas e comunidade criadora gigante."],
 'zumbis':["Os mortos caminham. {n} coloca você contra hordas de zumbis num mundo onde cada munição conta e cada erro custa caro.",
  "{n} é o definitivo jogo de zumbis no PC: hordas gigantes, sobrevivência brutal e pânico garantido com os amigos.",
  "Sobreviva ao apocalipse em {n}: zumbis por todos os lados, bases para defender e co-op para enfrentar o fim do mundo."],
 'mmo':["Um mundo inteiro online em {n}: guildas, raids, economia de servidor e amizades que atravessam expansões.",
  "{n} é o MMORPG que consome seu tempo com prazer: quests épicas, dungeons co-op e um mundo vivo 24 horas por dia.",
  "Crie sua lenda online em {n}: classes, talentos, PvP e um dos mundos persistentes mais ativos do PC."],
 'coop':["Chame a galera! {n} é co-op do jeito certo: desafios pensados para equipe, comunicação e muitas risadas.",
  "{n} brilha no multiplayer: cooperação real, momentos épicos e a certeza de que sozinho você não chegaria tão longe.",
  "Melhor com amigos: {n} entrega co-op memorável com desafios escaláveis e horas de diversão em equipe."],
 'indie':["{n} é aquele indie que ganha o coração de todo mundo: mecânica única, arte marcante e execução impecável.",
  "Pequeno no nome, gigante na entrega: {n} é uma das joias independentes mais bem avaliadas do PC.",
  "{n} prova que orçamento não define qualidade: gameplay afiado, identidade visual própria e criatividade sobrando."],
}

def mkel(g):
    t = TMPL.get(g['cat']) or TMPL['acao']
    return t[hash(g['appid']) % len(t)].format(n=g['nome'])

def feats(g):
    f = []
    nc = [norm(c) for c in g['cats_raw']]
    has = lambda s: any(s in x for x in nc)
    if has('single-player'): f.append('Modo história / single-player')
    if has('multi-player'): f.append('Multijogador online')
    if any('co-op' in x for x in nc): f.append('Cooperativo (co-op)')
    if any('pvp' in x for x in nc): f.append('PvP online')
    if has('achievements'): f.append('Conquistas Steam')
    if has('controller'): f.append('Suporte a controle')
    if has('steam cloud'): f.append('Save na nuvem (Steam Cloud)')
    if has('remote play'): f.append('Remote Play')
    if any('workshop' in x for x in nc): f.append('Suporte à Steam Workshop')
    return f[:5]

out = []
for g in picked.values():
    cats = [c for c in CAT_ORDER if c in g['cats']][:4]
    if g['cat'] not in cats: cats = [g['cat']] + cats[:3]
    preco = round(max(g['price'] - 30, 0.99), 2)
    out.append({
        'appid': g['appid'], 'nome': g['nome'], 'cat': g['cat'], 'cats': cats,
        'precoSteam': round(g['price'], 2), 'preco': preco,
        'economia': round(g['price'] - preco, 2), 'ano': g['ano'],
        'nota': int(round(g['nota'])), 'reviews': g['revs'], 'dev': g['dev'],
        'desc': HAND.get(g['appid'], mkel(g)), 'tags': feats(g),
    })
out.sort(key=lambda x: -x['reviews'])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('OK ->', OUT, len(out), 'jogos;', round(os.path.getsize(OUT)/1024), 'KB')

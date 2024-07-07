# GAME CLASS CODE
import lxml.etree
import urllib
import numpy as np
from collections import namedtuple
from IPython.display import Markdown, clear_output

class MahjongGame4P:
    def __init__(self, html_game):
        self.html_game = html_game

        self.css = "<style>red{background:radial-gradient(red,black);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}\
            rot{width:1.59em;transform:rotate(270deg)translateX(0.23em);display:inline-block;margin:0em -0.23em 0em -0.36em;}\
            #table{background-color:lightgray;color:black;line-height:1em;position:relative;font-size:30px;width:500px;height:500px;}\
            #dora_shown{font-size:25px;position:absolute;top:40%;left:50%;transform:translateX(-50%);}\
            #game_stats{line-height:1.2em;font-size:15px;text-align:center;position:absolute;top:48%;left:50%;transform:translateX(-50%);}\
            #east_stats{font-size:15px;position:absolute;top:60%;left:50%;transform:translateX(-50%);}\
            #east_river{position:absolute;top:65%;left:50%;transform:translateX(-2.45em);}\
            #east_hand{position:absolute;bottom:10%;left:0%;transform:translateX(250px)translateX(-50%);}\
            #east_meld{position:absolute;bottom:0.5%;right:0.5%;}\
            #south_stats{font-size:15px;position:absolute;bottom:50%;left:60%;transform:translateY(50%)translateX(-50%)rotate(270deg)translateY(50%);}\
            #south_river{position:absolute;bottom:50%;right:35%;transform:translateY(50%)translateX(50%)rotate(270deg)translateY(50%)translateX(50%)translateX(-2.45em);}\
            #south_hand{position:absolute;bottom:50%;right:10%;transform:translateY(50%)translateX(50%)rotate(270deg)translateY(-50%);}\
            #south_meld{position:absolute;top:0.5%;right:0.5%;transform:translateY(-50%)translateX(50%)rotate(270deg)translateX(-50%)translateY(-50%);}\
            #west_stats{font-size:15px;position:absolute;bottom:60%;left:50%;transform:translateX(-50%)rotate(180deg);}\
            #west_river{position:absolute;bottom:65%;right:50%;transform:rotate(180deg)translateX(-2.45em);}\
            #west_hand{position:absolute;top:10%;left:0%;transform:translateX(250px)translateX(-50%)rotate(180deg);}\
            #west_meld{position:absolute;top:0.5%;left:0.5%;transform:rotate(180deg);}\
            #north_stats{font-size:15px;position:absolute;top:50%;right:60%;transform:translateY(-50%)translateX(50%)rotate(90deg)translateY(50%);}\
            #north_river{position:absolute;top:50%;left:35%;transform:translateY(-50%)translateX(-50%)rotate(90deg)translateY(50%)translateX(50%)translateX(-2.45em);}\
            #north_hand{position:absolute;top:50%;left:10.0%;transform:translateY(-50%)translateX(-50%)rotate(90deg)translateY(-50%);}\
            #north_meld{position:absolute;bottom:0.5%;left:0.5%;transform:translateY(50%)translateX(-50%)rotate(90deg)translateX(-50%)translateY(-50%);}</style>"

        self.version = "2.3"
        self.player_stats = []
        self.game_rounds = []
        self.parse()

    def parse(self):
        riichi_next = False
        html = lxml.etree.fromstring(self.html_game)
        for element in html.xpath("/mjloggm")[0].iter():
            match element.tag:
                case "mjloggm":
                    assert self.version == element.get('ver')
                    # print(f"{element.tag} version {element.get('ver')}")
                case "SHUFFLE":
                    self.seed = element.get("seed")
                case "UN":
                    if not self.player_stats:
                        PlayerStat = namedtuple("player_stat", ["name", "dan", "rate", "sx"])
                        p_dans = list(map(int, element.get("dan").split(',')))
                        p_rates = list(map(float, element.get("rate").split(',')))
                        p_sxs = element.get("sx").split(',')
                        self.player_stats = [
                            PlayerStat(urllib.parse.unquote(element.get("n0")), p_dans[0], p_rates[0], p_sxs[0]),
                            PlayerStat(urllib.parse.unquote(element.get("n1")), p_dans[1], p_rates[1], p_sxs[1]),
                            PlayerStat(urllib.parse.unquote(element.get("n2")), p_dans[2], p_rates[2], p_sxs[2]),
                            PlayerStat(urllib.parse.unquote(element.get("n3")), p_dans[3], p_rates[3], p_sxs[3]),
                        ]
                case "GO":  # Ignore
                    pass
                case "TAIKYOKU":  # Ignore
                    pass
                case "BYE":  # Players disconnecting, Ignore
                    pass
                case "INIT":
                    seed = list(map(int, element.get("seed").split(",")))
                    haipais = list(map((lambda s: sorted(map(int, element.get(f"hai{s}").split(",")))), range(4)))
                    self.game_rounds.append([{
                        "action": "init",
                        "kyoku": seed[0], "honba": seed[1], "kyoutaku": seed[2], "dice": seed[3:5], "dora": seed[5],
                        "ten": list(map(int, element.get("ten").split(","))),
                        "oya": int(element.get("oya")), "hai": haipais,
                    }])
                case "DORA":  # New doras from kan
                    self.game_rounds[-1].append({
                        "action": "dora",  "tile": element.get("hai")
                    })
                case "REACH":  # Riichi
                    match int(element.get("step")):
                        case 1:  # Declaration
                            riichi_next = True
                        case 2:  # Betting 1000
                            self.game_rounds[-1].append({
                                "action": "score_update", "reason": "riichi", 
                                "ten": list(map(int, element.get("ten").split(","))),
                            })
                        case _:  # Should not happen
                            raise Exception
                case "AGARI":  # Ron / Tsumo
                    yaku_list = [
                        "門前清自摸和","立直","一発","槍槓","嶺上開花","海底摸月","河底撈魚","平和","断幺九","一盃口",
                        "自風 東","自風 南","自風 西","自風 北","場風 東","場風 南","場風 西","場風 北","役牌 白","役牌 發","役牌 中",
                        "両立直","七対子","混全帯幺九","一気通貫","三色同順","三色同刻","三槓子","対々和","三暗刻","小三元","混老頭",
                        "二盃口","純全帯幺九","混一色","清一色","人和","天和","地和","大三元","四暗刻","四暗刻単騎","字一色","緑一色",
                        "清老頭","九蓮宝燈","純正九蓮宝燈","国士無双","国士無双１３面","大四喜","小四喜","四槓子","ドラ","裏ドラ","赤ドラ"]
                    if element.get("yaku") is None:
                        yaku = list(map(int, element.get("yakuman").split(",")))
                        yaku = dict((yaku_list[yaku_id], 1) for yaku_id in yaku)
                    else:
                        yaku = list(map(int, element.get("yaku").split(",")))
                        yaku = dict((yaku_list[yaku[n]], yaku[n+1]) for n in range(0, len(yaku), 2))
                    player = int(element.get("who"))
                    from_player = int(element.get("fromWho"))
                    sc = list(map(int, element.get("sc").split(",")))
                    ten = list((sc[n] + sc[n+1] for n in range(0, len(sc), 2)))
                    hai = list(map(int, element.get("hai").split(","))) + [int(element.get("machi"))]
                    self.game_rounds[-1].append({
                        "action": "score_update", "reason": "agari", "who": player, "from_who": from_player, "yaku": yaku,
                        "ten": ten, "hai": hai
                    })
                case "RYUUKYOKU":  # Game draw
                    sc = list(map(int, element.get("sc").split(",")))
                    ten = list((sc[n] + sc[n+1] for n in range(0, len(sc), 2)))
                    self.game_rounds[-1].append({
                        "action": "score_update", "reason": "ryuukyoku", "ten": ten,
                    })
                case "N":  # Melds
                    player = int(element.get("who"))
                    m = int(element.get("m"))
                    if (m >> 2 & 0b1):  # CHII
                        chii_id = m >> 10
                        chii_val = chii_id % 21  # 123, 213, 234, 324, 423, 345 ...
                        chii_type = chii_id // 21  # 0: manzu, 1: pinzu, 2: soozu
                        mid_val = chii_val // 3  # 0 -> 1m, 1 -> 2m ...
                        chii_a, chii_b, chii_c = chii_val % 3, ((chii_val + 1) % 3), ((chii_val + 2) % 3)  # 0: 123, 1: 213, 2: 312
                        tile_stolen = (chii_a + mid_val + (chii_type * 9)) * 4 + (m >> (2 * chii_a + 3) & 0b11)
                        tile_meld_1 = (chii_b + mid_val + (chii_type * 9)) * 4 + (m >> (2 * chii_b + 3) & 0b11)
                        tile_meld_2 = (chii_c + mid_val + (chii_type * 9)) * 4 + (m >> (2 * chii_c + 3) & 0b11)
                        from_player = (player - 1) % 4
                        self.game_rounds[-1].append({
                            "action": "meld_chii", "m": m, "who": player, "from_who": from_player,
                            "tile_stolen": tile_stolen, 
                            "tile_meld_1": tile_meld_1, 
                            "tile_meld_2": tile_meld_2
                        })
                    elif (m >> 3 & 0b1):  # PON
                        pon_id = m >> 9 
                        pon_val = (pon_id // 3) * 4
                        pon_tile = pon_id % 3
                        tile_types = list(range(pon_val, pon_val + 4))
                        tile_kakan = pon_val + (m >> 5 & 0b11)
                        tile_stolen = pon_val + pon_tile + ((m >> 5 & 0b11) <= pon_tile)
                        tile_types.remove(tile_kakan)
                        tile_types.remove(tile_stolen)
                        from_player = (player + (m & 0b11)) % 4
                        self.game_rounds[-1].append({
                            "action": "meld_pon", "m": m, "who": player, "from_who": from_player,
                            "tile_stolen": tile_stolen,
                            "tile_meld_1": tile_types[0],
                            "tile_meld_2": tile_types[1]
                        })
                    elif (m >> 4 & 0b1):  # KAKAN
                        pon_m = m ^ 0b11000
                        pon_id = m >> 9
                        pon_val = (pon_id // 3) * 4
                        pon_tile = pon_id % 3
                        tile_types = list(range(pon_val, pon_val + 4))
                        tile_kakan = pon_val + (m >> 5 & 0b11)
                        tile_stolen = pon_val + pon_tile + ((m >> 5 & 0b11) <= pon_tile)
                        tile_types.remove(tile_kakan)
                        tile_types.remove(tile_stolen)
                        from_player = (player + (m & 0b11)) % 4
                        self.game_rounds[-1].append({
                            "action": "meld_kakan", "m": m, "pon_m": pon_m, "who": player, "from_who": from_player,
                            "tile_stolen": tile_stolen,
                            "tile_meld_1": tile_types[0],
                            "tile_meld_2": tile_types[1],
                            "tile_kakan": tile_kakan
                        })
                    elif (m & 0b11):  # MINKAN
                        tile_stolen = m >> 8
                        from_player = (player + (m & 0b11)) % 4
                        tile_meld_1 = ((tile_stolen // 4) * 4) + ((tile_stolen + 1) % 4)
                        tile_meld_2 = ((tile_stolen // 4) * 4) + ((tile_stolen + 2) % 4)
                        tile_meld_3 = ((tile_stolen // 4) * 4) + ((tile_stolen + 3) % 4)
                        self.game_rounds[-1].append({
                            "action": "meld_minkan", "m": m, "who": player, "from_who": from_player,
                            "tile_stolen": tile_stolen,
                            "tile_meld_1": tile_meld_1,
                            "tile_meld_2": tile_meld_2,
                            "tile_meld_3": tile_meld_3
                        })
                    elif not (m & 0b11111111):  # ANKAN
                        tile_ankan = m >> 8
                        self.game_rounds[-1].append({
                            "action": "meld_ankan", "m": m, "who": player,
                            "tile_meld_1": tile_ankan,
                            "tile_meld_2": tile_ankan + 1,
                            "tile_meld_3": tile_ankan + 2,
                            "tile_meld_4": tile_ankan + 3,
                        })
                    else: 
                        raise Exception  # Not supposed to happen
                case _:  # Common action
                    alphabet, tile = element.tag[0], element.tag[1:]
                    match alphabet:
                        case "T": player, action = 0, "draw"
                        case "U": player, action = 1, "draw"
                        case "V": player, action = 2, "draw"
                        case "W": player, action = 3, "draw"
                        case "D": player, action = 0, "throw"
                        case "E": player, action = 1, "throw"
                        case "F": player, action = 2, "throw"
                        case "G": player, action = 3, "throw"
                        case _: raise Exception  # Not supposed to happen
                    self.game_rounds[-1].append({
                        "action": "riichi" if riichi_next else action, "who": int(player), "tile": int(tile),
                    })
                    riichi_next = False
                    # print(element.tag, element.attrib)

    def render(self):
        winds = ['東', '南', '西', '北']
        body = f"<div id=table><div id=dora_shown>{(''.join(map(self.id2str, self.dora)))+('🀫'*(5-len(self.dora)))}</div>\
        	<div id=game_stats>{'四麻赤'}<br>{winds[self.kyoku//4]}{self.kyoku%4+1}局<br>{self.honba}本場{self.kyoutaku}供託</div>"
        for p, wind in ((0, "east"), (1, "south"), (2, "west"), (3, "north")):
            river = list(map(self.id2str, self.river[p]))
            if self.riichi[p] is not None:
                if len(river) > self.riichi[p]:
                    river[self.riichi[p]] = f"<rot>{river[self.riichi[p]]}</rot>"
            river.insert(12, "<br>")
            river.insert(6, "<br>")
            river = ''.join(river)
            body += f"\
            	<div id={wind}_stats>{'<b>' if self.turn == p else ''}{winds[(p-self.oya)%4]}家 {self.ten[p]*100}{' 立直' if self.riichi[p] else ''}{'</b>' if self.turn == p else ''}</div>\
            	<div id={wind}_river>{river}</div>\
            	<div id={wind}_hand>{''.join(map(self.id2str, self.hai[p]))}{f' {self.id2str(self.tile_held[p])}' if self.tile_held[p] else ''}</div>\
            	<div id={wind}_meld>{' '.join(map(self.meld2str, self.meld[p]))}</div>"
        display(Markdown(self.css + body))
    
    def select_round(self, round_num):
        self.round = self.game_rounds[round_num]
        setup = self.round.pop(0)
        assert setup["action"] == "init"
        self.kyoku = setup["kyoku"]
        self.honba = setup["honba"]
        self.kyoutaku = setup["kyoutaku"]
        self.dora = [setup["dora"]]
        self.ten = setup["ten"]
        self.oya = self.turn = setup["oya"]
        self.hai = setup["hai"]
        self.win_tiles = []
        self.riichi = [None, None, None, None]
        self.tile_held = [None, None, None, None]
        self.river = [[], [], [], []]
        self.meld = [[], [], [], []]
    
    def step(self, move=None, verbose=True):  # Returns 1 on round end
        if move is None:
            move = self.round.pop(0)
        if verbose:
            print(move)
        match move["action"]:
            case "draw":
                self.turn = turn = move["who"]
                self.tile_held[turn] = move["tile"]
            case "throw":
                self.turn = turn = move["who"]
                if self.tile_held[turn] is not None:
                    self.hai[turn].append(self.tile_held[turn])
                    self.tile_held[turn] = None
                self.hai[turn].remove(move["tile"])
                self.river[turn].append(move["tile"])
                self.hai[turn].sort()
            case "riichi":
                self.turn = turn = move["who"]
                if self.tile_held[turn] is not None:
                    self.hai[turn].append(self.tile_held[turn])
                    self.tile_held[turn] = None
                self.hai[turn].remove(move["tile"])
                self.riichi[turn] = len(self.river[turn])  # To index the sideways tile
                self.river[turn].append(move["tile"])
                self.hai[turn].sort()
            case "meld_chii":
                self.turn = turn = move["who"]
                tile_stolen = self.river[move["from_who"]].pop()
                assert tile_stolen == move["tile_stolen"]
                self.hai[turn].remove(move["tile_meld_1"])
                self.hai[turn].remove(move["tile_meld_2"])
                self.meld[turn].insert(0, move)
            case "meld_pon":
                self.turn = turn = move["who"]
                tile_stolen = self.river[move["from_who"]].pop()
                assert tile_stolen == move["tile_stolen"]
                self.hai[turn].remove(move["tile_meld_1"])
                self.hai[turn].remove(move["tile_meld_2"])
                self.meld[turn].insert(0, move)
            case "meld_kakan":
                self.turn = turn = move["who"]
                if self.tile_held[turn] is not None:
                    self.hai[turn].append(self.tile_held[turn])
                    self.tile_held[turn] = None
                self.hai[turn].remove(move["tile_kakan"])
                meld_pon = list(filter((lambda d: d["m"] == move["pon_m"]), self.meld[turn]))[0]
                self.meld[turn][self.meld[turn].index(meld_pon)] = move
            case "meld_ankan":
                self.turn = turn = move["who"]
                if self.tile_held[turn] is not None:
                    self.hai[turn].append(self.tile_held[turn])
                    self.tile_held[turn] = None
                self.hai[turn].remove(move["tile_meld_1"])
                self.hai[turn].remove(move["tile_meld_2"])
                self.hai[turn].remove(move["tile_meld_3"])
                self.hai[turn].remove(move["tile_meld_4"])
                self.meld[turn].insert(0, move)
            case "meld_minkan":
                self.turn = turn = move["who"]
                tile_stolen = self.river[move["from_who"]].pop()
                assert tile_stolen == move["tile_stolen"]
                self.hai[turn].remove(move["tile_meld_1"])
                self.hai[turn].remove(move["tile_meld_2"])
                self.hai[turn].remove(move["tile_meld_3"])
                self.meld[turn].insert(0, move)
            case "score_update":
                self.ten = move["ten"]
                match move["reason"]:
                    case "riichi":
                        self.kyoutaku += 1
                    case "ryuukyoku":
                        pass
                    case "agari":
                        self.win_tiles = move["hai"]
                    case _:  # Not supposed to happen
                        raise Exception
            case _:
                pass
        if len(self.round) == 0:
            return move, 1
        else:
            return move, 0

    def meld2str(self, meld):
        if meld["action"] in ("meld_chii", "meld_pon"):
            sideways_index = ((meld["who"] - meld["from_who"]) % 4) - 1  # Only work for 3 tiles
            meld_str = list(map(self.id2str, sorted([meld["tile_meld_1"], meld["tile_meld_2"]])))
            meld_str.insert(sideways_index, f"<rot>{self.id2str(meld['tile_stolen'])}</rot>")
            meld_str = "".join(meld_str)
            return meld_str
        elif meld["action"] == "meld_minkan":
            sideways_index = ((meld["who"] - meld["from_who"]) % 4) - 1  # Only work for 3 tiles
            sideways_index = 3 if sideways_index == 2 else sideways_index
            meld_str = list(map(self.id2str, sorted([meld["tile_meld_1"], meld["tile_meld_2"], meld["tile_meld_3"]])))
            meld_str.insert(sideways_index, f"<rot>{self.id2str(meld['tile_stolen'])}</rot>")
            meld_str = "".join(meld_str)
            return meld_str
        elif meld["action"] == "meld_ankan":
            tile_type = meld["tile_meld_1"] // 4
            meld_str = f"🀫{self.id2str(tile_type * 4)}{self.id2str(tile_type * 4 + 1)}🀫"
            return meld_str
        elif meld["action"] == "meld_kakan":
            sideways_index = ((meld["who"] - meld["from_who"]) % 4) - 1  # Only work for 3 tiles
            meld_str = list(map(self.id2str, sorted([meld["tile_meld_1"], meld["tile_meld_2"]])))
            meld_str.insert(sideways_index, f"<rot>{self.id2str(meld['tile_stolen'])}{self.id2str(meld['tile_kakan'])}</rot>")
            meld_str = "".join(meld_str)
            return meld_str
        else:
            raise Exception

    def id2str(self, tile_id):
        tile_strlist = "🀇🀇🀇🀇🀈🀈🀈🀈🀉🀉🀉🀉🀊🀊🀊🀊🀋🀋🀋🀋🀌🀌🀌🀌🀍🀍🀍🀍🀎🀎🀎🀎🀏🀏🀏🀏" \
                     + "🀙🀙🀙🀙🀚🀚🀚🀚🀛🀛🀛🀛🀜🀜🀜🀜🀝🀝🀝🀝🀞🀞🀞🀞🀟🀟🀟🀟🀠🀠🀠🀠🀡🀡🀡🀡" \
                     + "🀐🀐🀐🀐🀑🀑🀑🀑🀒🀒🀒🀒🀓🀓🀓🀓🀔🀔🀔🀔🀕🀕🀕🀕🀖🀖🀖🀖🀗🀗🀗🀗🀘🀘🀘🀘" \
                     + "🀀🀀🀀🀀🀁🀁🀁🀁🀂🀂🀂🀂🀃🀃🀃🀃🀆🀆🀆🀆🀅🀅🀅🀅"  # 🀄︎🀫
        if tile_id in [16, 52, 88]:  # Red 5s
            tile = f"<red>{tile_strlist[tile_id]}</red>"
        elif tile_id in [132, 133, 134, 135]:  # 🀄︎
            tile = "🀄︎"
        else:
            tile = tile_strlist[tile_id]
        if tile_id in self.win_tiles:
            return f"<b>{tile}</b>"
        else:
            return tile

def shift(seq, n):
    n = n % len(seq)
    return seq[n:] + seq[:n]

def mjg2imgstate(mjg):
    hand_arr = np.zeros((4, 4, 9), dtype=np.uint8)  # Player, tile type, amount of tiles, tile value
    hand_red5_arr = np.zeros(3, dtype=np.uint8)
    hand_arr[np.array(
        mjg.hai[mjg.turn]) // 36, 
        np.array(mjg.hai[mjg.turn]) % 4, 
        np.array(mjg.hai[mjg.turn]) // 4 % 9] = 1
    hand_red5_arr[0] = 16 in mjg.hai[mjg.turn]
    hand_red5_arr[1] = 52 in mjg.hai[mjg.turn]
    hand_red5_arr[2] = 88 in mjg.hai[mjg.turn]
    hand_arr.sort(axis=1)
    # print(hand_arr)
    # print(hand_red5_arr)

    river_arr = np.zeros((4, 4, 24, 9), dtype=np.int8)  # Player, tile type, river, tile value
    river_red5_arr = np.zeros((4, 24), dtype=np.uint8)
    for n in shift([0, 1, 2, 3], mjg.turn):
        river = np.array(mjg.river[n], dtype=np.uint8)
        river_arr[n, river // 36, np.arange(len(river)), river // 4 % 9] = 1
        river_red5_arr[n, :len(mjg.river[n])] = list(map(lambda i: int(i in (16, 52, 88)), mjg.river[n]))
    # print(river_arr)
    # print(river_red5_arr)

    river_riichi_arr = np.zeros((4, 24), dtype=np.uint8)
    for n, riichi in enumerate(shift(mjg.riichi, mjg.turn)):
        if riichi is not None:
            river_riichi_arr[n, riichi] = 1
    # print(river_riichi_arr)

    meld_arr = np.zeros((4, 4, 4, 9), dtype=np.uint8)  # Player, tile type, amount of tiles, tile value
    meld_red5_arr = np.zeros((4, 3), dtype=np.uint8)
    meld_throw_arr = np.zeros((4, 4, 4, 9), dtype=np.uint8)  # Player, tile type, amount of tiles, tile value
    meld_throw_red5_arr = np.zeros((4, 3), dtype=np.uint8)
    for n, meld_list in enumerate(shift(mjg.meld, mjg.turn)):
        for meld in meld_list:
            for meld_type in ["tile_stolen", "tile_meld_1", "tile_meld_2", "tile_meld_3", "tile_meld_4", "tile_kakan"]:
                if meld_type in meld:
                    meld_arr[n, meld[meld_type] // 36, meld[meld_type] % 4, meld[meld_type] // 4 % 9] = 1
                    if meld[meld_type] == 16:
                        meld_red5_arr[n, 0] = 1
                    if meld[meld_type] == 52:
                        meld_red5_arr[n, 1] = 1
                    if meld[meld_type] == 88:
                        meld_red5_arr[n, 2] = 1
                if "tile_stolen" in meld:
                    tile = meld["tile_stolen"]
                    meld_throw_arr[meld["from_who"], tile // 36, tile % 4, tile // 4 % 9] = 1
                    if tile == 16:
                        meld_throw_red5_arr[n, 0] = 1
                    if tile == 52:
                        meld_throw_red5_arr[n, 1] = 1
                    if tile == 88:
                        meld_throw_red5_arr[n, 2] = 1
    meld_arr.sort(axis=2)
    meld_throw_arr.sort(axis=2)
    # print(meld_arr)
    # print(meld_red5_arr)
    # print(meld_throw_arr)
    # print(meld_throw_red5_arr)

    dora = np.array(mjg.dora, dtype=np.uint8)
    dora_arr = np.zeros((4, 4, 9), dtype=np.uint8)
    dora_arr[dora // 36, dora % 4, dora // 4 % 9] = 1
    # print(dora_arr)
    
    score_arr = np.array(shift(mjg.ten, mjg.turn), dtype=np.int16)
    score_y_arr = np.array(shift(mjg.round[-1]["ten"], mjg.turn), dtype=np.int16)
    # print(score_arr)
    # print(score_y_arr)
    
    pool_arr = np.array((mjg.honba + mjg.kyoutaku * 10), dtype=np.uint8)
    # print(pool_arr)
    
    winds_arr = np.zeros((2, 9), dtype=np.uint8)
    winds_arr[1, mjg.kyoku // 4] = 1
    winds_arr[0, (mjg.turn - mjg.oya) % 4] = 1
    # print(winds_arr)

    return dict(
        x_hand=hand_arr,
        x_hand_red=hand_red5_arr,
        x_river=river_arr,
        x_river_red=river_red5_arr,
        x_river_riichi=river_riichi_arr,
        x_meld=meld_arr,
        x_meld_red5=meld_red5_arr,
        x_meld_throw=meld_throw_arr,
        x_meld_throw_red=meld_throw_red5_arr,
        x_dora=dora_arr,
        x_score=score_arr,
        x_pool=pool_arr,
        x_winds=winds_arr,
        y=score_y_arr
    )

from torch.utils.data import Dataset, DataLoader
import torch
import numpy as np
import glob

class MahjongDataset(Dataset):
    def __init__(self, data_paths, load=True):
        self.x_dict = {
            "x_hand": None, 
            "x_hand_red": None, 
            "x_river": None, 
            "x_river_red": None, 
            "x_river_riichi": None, 
            "x_meld": None, 
            "x_meld_red5": None, 
            "x_meld_throw": None, 
            "x_meld_throw_red": None, 
            "x_dora": None, 
            "x_score": None, 
            "x_pool": None, 
            "x_winds": None}
        self.y = None
        self.loads = list(map(np.load, data_paths))
        self.loads = [np.load(path) for path in data_paths]

        if load:
            self.load_index = -1
            self.load_next()

    def unload(self):
        self.y = None
        self.x = None
        for key in self.x_dict.keys():
            self.x_dict[key] = None
    
    def load_next(self):
        self.load_index += 1
        self.load_index %= len(self.loads)
        self.y = self.loads[self.load_index]["y"].astype(np.float32)
        for key in self.x_dict.keys():
            self.x_dict[key] = self.loads[self.load_index][key].astype(np.float32)
        self.post_load()
    
    def post_load(self):
        # Data pre-processing
        # Divide by 250 to average out the score values
        self.y /= 250
        self.x_dict["x_score"] /= 250
        self.x_dict["x_pool"] /= 250
        # To predict score difference at the end of the round
        self.y -= self.x_dict["x_score"]
        # Resize all input to B, X, 24, 9
        self.x_dict["x_hand"] = np.repeat(self.x_dict["x_hand"], 6, -2)
        self.x_dict["x_hand_red"] = np.expand_dims(self.x_dict["x_hand_red"], (-1, -2))
        self.x_dict["x_hand_red"] = np.repeat(self.x_dict["x_hand_red"], 9, -1)
        self.x_dict["x_hand_red"] = np.repeat(self.x_dict["x_hand_red"], 24, -2)
        self.x_dict["x_river"] = np.reshape(self.x_dict["x_river"], (*self.x_dict["x_river"].shape[:1], -1, *self.x_dict["x_river"].shape[3:]))
        self.x_dict["x_river_red"] = np.expand_dims(self.x_dict["x_river_red"], -1)
        self.x_dict["x_river_red"] = np.repeat(self.x_dict["x_river_red"], 9, -1)
        self.x_dict["x_river_riichi"] = np.expand_dims(self.x_dict["x_river_riichi"], -1)
        self.x_dict["x_river_riichi"] = np.repeat(self.x_dict["x_river_riichi"], 9, -1)
        self.x_dict["x_meld"] = np.reshape(self.x_dict["x_meld"], (*self.x_dict["x_meld"].shape[:1], -1, *self.x_dict["x_meld"].shape[3:]))
        self.x_dict["x_meld"] = np.repeat(self.x_dict["x_meld"], 6, -2)
        self.x_dict["x_meld_red5"] = np.reshape(self.x_dict["x_meld_red5"], (self.x_dict["x_meld_red5"].shape[0], -1))
        self.x_dict["x_meld_red5"] = np.expand_dims(self.x_dict["x_meld_red5"], (-1, -2))
        self.x_dict["x_meld_red5"] = np.repeat(self.x_dict["x_meld_red5"], 9, -1)
        self.x_dict["x_meld_red5"] = np.repeat(self.x_dict["x_meld_red5"], 24, -2)
        self.x_dict["x_meld_throw"] = np.reshape(self.x_dict["x_meld_throw"], (self.x_dict["x_meld_throw"].shape[0], -1, *self.x_dict["x_meld_throw"].shape[3:]))
        self.x_dict["x_meld_throw"] = np.repeat(self.x_dict["x_meld_throw"], 6, -2)
        self.x_dict["x_meld_throw_red"] = np.reshape(self.x_dict["x_meld_throw_red"], (self.x_dict["x_meld_throw_red"].shape[0], -1))
        self.x_dict["x_meld_throw_red"] = np.expand_dims(self.x_dict["x_meld_throw_red"], (-1, -2))
        self.x_dict["x_meld_throw_red"] = np.repeat(self.x_dict["x_meld_throw_red"], 9, -1)
        self.x_dict["x_meld_throw_red"] = np.repeat(self.x_dict["x_meld_throw_red"], 24, -2)
        self.x_dict["x_dora"] = np.repeat(self.x_dict["x_dora"], 6, -2)
        self.x_dict["x_score"] = np.expand_dims(self.x_dict["x_score"], (-1, -2))
        self.x_dict["x_score"] = np.repeat(self.x_dict["x_score"], 9, -1)
        self.x_dict["x_score"] = np.repeat(self.x_dict["x_score"], 24, -2)
        self.x_dict["x_pool"] = np.expand_dims(self.x_dict["x_pool"], (-1, -2, -3))
        self.x_dict["x_pool"] = np.repeat(self.x_dict["x_pool"], 9, -1)
        self.x_dict["x_pool"] = np.repeat(self.x_dict["x_pool"], 24, -2)
        self.x_dict["x_winds"] = np.expand_dims(self.x_dict["x_winds"], -2)
        self.x_dict["x_winds"] = np.repeat(self.x_dict["x_winds"], 24, -2)
        
        # for varname in self.x_dict.keys():
        #     print(varname, self.x_dict[varname].shape)

        self.x = np.concatenate(list(self.x_dict.values()), axis=1)

        # Unload dict to save memory
        for key in self.x_dict.keys():
            self.x_dict[key] = None
    
    def __len__(self):
        return len(self.y)
    
    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        return self.x[idx], self.y[idx]
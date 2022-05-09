from __future__ import annotations
import re
import zhon.pinyin
import unicodedata
from typing import *
from collections import defaultdict
from functools import lru_cache, partial

# fmt: off
LEFT_MAPPINGS: Dict[str, str] = {
    '、': ',',  # Chinese enumeration comma
    '。': '.',
    '，': ',',
    '；': ';',
    '？': '?',
    '！': '!',
    '》': '"',
    '」': '"',
    '）': ')',
    '】': ']',
}
RIGHT_MAPPINGS: Dict[str, str] = {
    '《': '"',
    '「': '"',
    '（': '(',
    '【': '['
}
# fmt: on


def remove_chinese_punctuation_marks(pinyin: str) -> str:
    for mark in list(RIGHT_MAPPINGS.keys()) + list(LEFT_MAPPINGS.keys()):
        pinyin = pinyin.replace(mark, '')
    return pinyin


def romanize_punctuation_marks(pinyin: str) -> str:
    for chinese_mark, regular_mark in LEFT_MAPPINGS.items():
        pinyin = re.sub(f'{chinese_mark}(\\w)', f'{regular_mark} \\1', pinyin)
        pinyin = re.sub(chinese_mark, regular_mark, pinyin)

    for chinese_mark, regular_mark in RIGHT_MAPPINGS.items():
        pinyin = re.sub(f'(\\w){chinese_mark}', f'\\1 {regular_mark}', pinyin)
        pinyin = re.sub(chinese_mark, regular_mark, pinyin)

    return pinyin


def extract_normalized_pinyin(pinyin: str) -> List[str]:
    """
    Splits normalized pinyin (see normalize_pinyin) into syllables
    """
    # NOTE: numbered_syllable catches syllables without tonal numbers as well,
    # but we want to make sure they are there
    return [s for s in re.findall(zhon.pinyin.numbered_syllable, pinyin, re.I) if s[-1].isnumeric()]


def normalize_pinyin(pinyin: str, remove_punctuation: bool = False) -> str:
    """
    Normalizes a pinyin string to a format with numbers for all tones 1-5 (including neutral)
    and spaces between words e.g:
        wo3 hen3 xi3huan1 ni3.

    Tries to handle all kinds of pinyin found in various sources
    Details:
    * TODO: Converts color umlaut representation to v's. e.g. nu:3 -> nv3
    * TODO: Converts ng -> en (ng is not standard, not in cedcit and doesn't work in pinyin typing)
    * Detects if pinyin has tonal numbers or tonal (diacritical) marks

    NOTE: right now only works for ChinesePod
    """
    # Remove extra whitespace
    pinyin = pinyin.strip()
    pinyin = pinyin.replace('u:', 'v').replace('U:', 'V')
    pinyin = pinyin.replace('uu', 'v').replace('UU', 'V')
    pinyin = pinyin.replace('lue', 'lve').replace('nue', 'nve')

    def _repl(match):
        return syllable_diacritial_to_number(match.group(0))

    pinyin = re.sub(zhon.pinyin.syllable, _repl, pinyin, flags=re.I)

    pinyin = romanize_punctuation_marks(pinyin)
    if remove_punctuation:
        pinyin = re.sub(r'[^\w\d]', ' ', pinyin)
        pinyin = re.sub(r' +', ' ', pinyin)
        pinyin = pinyin.strip()

    return pinyin


DIACRITICAL_TABLE = {0x304: ord('1'), 0x301: ord('2'), 0x30C: ord('3'), 0x300: ord('4')}


def has_diacriticals(s: str) -> bool:
    # TODO: use sets?
    normalized = unicodedata.normalize('NFD', s)
    for c in DIACRITICAL_TABLE.keys():
        if chr(c) in normalized:
            return True
    return False


def _translate_diacritical_to_number(s: str) -> str:
    return unicodedata.normalize('NFD', s).translate(DIACRITICAL_TABLE)


def syllable_diacritial_to_number(s: str) -> str:
    """
    Converts a single pinyin syllable from diacritical tone marks to tonal number
    Source: https://stackoverflow.com/questions/42854588/get-tone-number-from-pinyin
    """
    translated = _translate_diacritical_to_number(s)
    translated = translated.replace('ü', 'v').replace('Ü', 'V')
    # Move the number to the end of the string
    for n in [1, 2, 3, 4, 5]:
        if str(n) not in translated:
            continue
        idx = translated.index(str(n))
        return translated[:idx] + translated[idx + 1 :] + str(n)

    # If we didn't return in the loop, must be a neutral tone
    return translated + '5'


PINYIN_TONE_MARKS = {
    'a': 'āáǎà',
    'e': 'ēéěè',
    'i': 'īíǐì',
    'o': 'ōóǒò',
    'u': 'ūúǔù',
    'ü': 'ǖǘǚǜ',
    'A': 'ĀÁǍÀ',
    'E': 'ĒÉĚÈ',
    'I': 'ĪÍǏÌ',
    'O': 'ŌÓǑÒ',
    'U': 'ŪÚǓÙ',
    'Ü': 'ǕǗǙǛ',
}


def _convert_to_diacritial_callback(m: Match, remove_tonal_number: bool = True) -> str:
    tone = int(m.group(3)) % 5
    r = m.group(1).replace('v', 'ü').replace('V', 'Ü')
    # for multple vowels, use first one if it is a/e/o, otherwise use second one
    pos = 0
    if len(r) > 1 and not r[0] in 'aeoAEO':
        pos = 1
    if tone != 0:
        r = r[0:pos] + PINYIN_TONE_MARKS[r[pos]][tone - 1] + r[pos + 1 :]
    converted = r + m.group(2)
    if not remove_tonal_number:
        converted += m.group(3)
    return converted


def normalized_to_diacritical(pinyin: str) -> str:
    return re.sub(r'([aeiouüvÜr]{1,3})(n?g?r?)([012345])', _convert_to_diacritial_callback, pinyin, flags=re.IGNORECASE,)


def normalized_to_diacritical_plus_tonal_numbers(pinyin: str) -> str:
    return re.sub(
        r'([aeiouüvÜ]{1,3})(n?g?r?)([012345])',
        partial(_convert_to_diacritial_callback, remove_tonal_number=False),
        pinyin,
        flags=re.IGNORECASE,
    )


__all__ = [
    'normalized_to_diacritical',
    'normalized_to_diacritical_plus_tonal_numbers',
    'normalize_pinyin',
    'remove_chinese_punctuation_marks',
    'romanize_punctuation_marks',
    'extract_normalized_pinyin',
]


wade_giles_pinyin_pairs = [
    ('shaan', 'shan'),
    ('a', 'a'),
    ('a', 'ai'),
    ('an', 'an'),
    ('ang', 'ang'),
    ('ao', 'ao'),
    ('cha', 'zha'),
    ('cha', 'cha'),
    ('chai', 'zhai'),
    ('chai', 'chai'),
    ('chan', 'zhan'),
    ('chan', 'chan'),
    ('chang', 'zhang'),
    ('chang', 'chang'),
    ('chao', 'zhao'),
    ('chao', 'chao'),
    ('che', 'zhe'),
    ('che', 'che'),
    ('chen', 'zhen'),
    ('chen', 'chen'),
    ('cheng', 'zheng'),
    ('cheng', 'cheng'),
    ('chi', 'ji'),
    ('chi', 'qi'),
    ('chia', 'jia'),
    ('chia', 'qia'),
    ('chiang', 'jiang'),
    ('chiang', 'qiang'),
    ('chiao', 'jiao'),
    ('chiao', 'qiao'),
    ('chieh', 'jie'),
    ('chieh', 'qie'),
    ('chien', 'jian'),
    ('chien', 'qian'),
    ('chih', 'zhi'),
    ('chih', 'chi'),
    ('chin', 'jin'),
    ('chin', 'qin'),
    ('ching', 'jing'),
    ('ching', 'qing'),
    ('chiu', 'jiu'),
    ('chiu', 'qiu'),
    ('chiung', 'jiong'),
    ('chiung', 'qiong'),
    ('cho', 'zhuo'),
    ('cho', 'chuo'),
    ('chou', 'zhou'),
    ('chou', 'chou'),
    ('chu', 'zhu'),
    ('chu', 'chu'),
    ('chu', 'ju'),
    ('chu', 'jv'),
    ('chu', 'qu'),
    ('chu', 'qv'),
    ('chua', 'zhua'),
    ('chuai', 'zhuai'),
    ('chuai', 'chuai'),
    ('chuan', 'zhuan'),
    ('chuan', 'chuan'),
    ('chuan', 'juan'),
    ('chuan', 'jvan'),
    ('chuan', 'quan'),
    ('chuan', 'qvan'),
    ('chuang', 'zhuang'),
    ('chuang', 'chuang'),
    ('chueh', 'jue'),
    ('chueh', 'jve'),
    ('chueh', 'que'),
    ('chueh', 'qve'),
    ('chui', 'zhui'),
    ('chui', 'chui'),
    ('chun', 'zhun'),
    ('chun', 'chun'),
    ('chun', 'jun'),
    ('chun', 'jvn'),
    ('chun', 'qun'),
    ('chun', 'qvn'),
    ('chung', 'zhong'),
    ('chung', 'chong'),
    ('en', 'en'),
    ('erh', 'er'),
    ('erh', 'r'),
    ('fa', 'fa'),
    ('fan', 'fan'),
    ('fang', 'fang'),
    ('fei', 'fei'),
    ('fen', 'fen'),
    ('feng', 'feng'),
    ('fo', 'fo'),
    ('fou', 'fou'),
    ('fu', 'fu'),
    ('ha', 'ha'),
    ('hai', 'hai'),
    ('han', 'han'),
    ('hang', 'hang'),
    ('hao', 'hao'),
    ('hei', 'hei'),
    ('hen', 'hen'),
    ('heng', 'heng'),
    ('ho', 'he'),
    ('hou', 'hou'),
    ('hsi', 'xi'),
    ('hsia', 'xia'),
    ('hsiang', 'xiang'),
    ('hsiao', 'xiao'),
    ('hsieh', 'xie'),
    ('hsien', 'xian'),
    ('hsin', 'xin'),
    ('hsing', 'xing'),
    ('hsiu', 'xiu'),
    ('hsiung', 'xiong'),
    ('hsu', 'xu'),
    ('hsu', 'xv'),
    ('hsuan', 'xuan'),
    ('hsuan', 'xvan'),
    ('hsueh', 'xue'),
    ('hsueh', 'xve'),
    ('hsun', 'xun'),
    ('hsun', 'xvn'),
    ('hu', 'hu'),
    ('hua', 'hua'),
    ('huai', 'huai'),
    ('huan', 'huan'),
    ('huang', 'huang'),
    ('hui', 'hui'),
    ('hun', 'hun'),
    ('hung', 'hong'),
    ('huo', 'huo'),
    ('i', 'yi'),
    ('jan', 'ran'),
    ('jang', 'rang'),
    ('jao', 'rao'),
    ('je', 're'),
    ('jen', 'ren'),
    ('jeng', 'reng'),
    ('jih', 'ri'),
    ('jo', 'ruo'),
    ('jou', 'rou'),
    ('ju', 'ru'),
    ('juan', 'ruan'),
    ('jui', 'rui'),
    ('jun', 'run'),
    ('jung', 'rong'),
    ('ka', 'ga'),
    ('ka', 'ka'),
    ('kai', 'gai'),
    ('kai', 'kai'),
    ('kan', 'gan'),
    ('kan', 'kan'),
    ('kang', 'gang'),
    ('kang', 'kang'),
    ('kao', 'gao'),
    ('kao', 'kao'),
    ('ken', 'gen'),
    ('ken', 'ken'),
    ('keng', 'geng'),
    ('keng', 'keng'),
    ('ko', 'ge'),
    ('ko', 'ke'),
    ('kou', 'gou'),
    ('kou', 'kou'),
    ('ku', 'gu'),
    ('ku', 'ku'),
    ('kua', 'gua'),
    ('kua', 'kua'),
    ('kuai', 'guai'),
    ('kuai', 'kuai'),
    ('kuan', 'guan'),
    ('kuan', 'kuan'),
    ('kuang', 'guang'),
    ('kuang', 'kuang'),
    ('kuei', 'gui'),
    ('kuei', 'kui'),
    ('kun', 'gun'),
    ('kun', 'kun'),
    ('kung', 'gong'),
    ('kung', 'kong'),
    ('kuo', 'guo'),
    ('kuo', 'kuo'),
    ('la', 'la'),
    ('lai', 'lai'),
    ('lan', 'lan'),
    ('lang', 'lang'),
    ('lao', 'lao'),
    ('le', 'le'),
    ('lei', 'lei'),
    ('leng', 'leng'),
    ('li', 'li'),
    ('liang', 'liang'),
    ('liao', 'liao'),
    ('lieh', 'lie'),
    ('lien', 'lian'),
    ('lin', 'lin'),
    ('ling', 'ling'),
    ('liu', 'liu'),
    ('lo', 'luo'),
    ('lou', 'lou'),
    ('lu', 'lu'),
    ('lu', 'lv'),
    ('luan', 'luan'),
    ('luan', 'lvan'),
    ('lueh', 'lue'),
    ('lueh', 'lve'),
    ('lun', 'lun'),
    ('lun', 'lvn'),
    ('lung', 'long'),
    ('ma', 'ma'),
    ('mai', 'mai'),
    ('man', 'man'),
    ('mang', 'mang'),
    ('mao', 'mao'),
    ('mei', 'mei'),
    ('men', 'men'),
    ('meng', 'meng'),
    ('me', 'me'),
    ('mi', 'mi'),
    ('miao', 'miao'),
    ('mieh', 'mie'),
    ('mien', 'mian'),
    ('min', 'min'),
    ('ming', 'ming'),
    ('miu', 'miu'),
    ('mo', 'mo'),
    ('mou', 'mou'),
    ('mu', 'mu'),
    ('na', 'na'),
    ('nai', 'nai'),
    ('nan', 'nan'),
    ('nang', 'nang'),
    ('nao', 'nao'),
    ('ne', 'ne'),
    ('nei', 'nei'),
    ('nen', 'nen'),
    ('neng', 'neng'),
    ('ni', 'ni'),
    ('niang', 'niang'),
    ('niao', 'niao'),
    ('nieh', 'nie'),
    ('nien', 'nian'),
    ('nin', 'nin'),
    ('ning', 'ning'),
    ('niu', 'niu'),
    ('no', 'nuo'),
    ('nou', 'nou'),
    ('nu', 'nu'),
    ('nu', 'nv'),
    ('nuan', 'nuan'),
    ('nuan', 'nvan'),
    ('nueh', 'nue'),
    ('nueh', 'nve'),
    ('nung', 'nong'),
    ('o', 'e'),
    ('ou', 'ou'),
    ('pa', 'ba'),
    ('pa', 'pa'),
    ('pai', 'bai'),
    ('pai', 'pai'),
    ('pan', 'ban'),
    ('pan', 'pan'),
    ('pang', 'bang'),
    ('pang', 'pang'),
    ('pao', 'bao'),
    ('pao', 'pao'),
    ('pei', 'bei'),
    ('pei', 'pei'),
    ('pen', 'ben'),
    ('pen', 'pen'),
    ('peng', 'beng'),
    ('peng', 'peng'),
    ('pi', 'bi'),
    ('pi', 'pi'),
    ('piao', 'biao'),
    ('piao', 'piao'),
    ('pieh', 'bie'),
    ('pieh', 'pie'),
    ('pien', 'bian'),
    ('pien', 'pian'),
    ('pin', 'bin'),
    ('pin', 'pin'),
    ('ping', 'bing'),
    ('ping', 'ping'),
    ('po', 'bo'),
    ('po', 'po'),
    ('pou', 'pou'),
    ('pu', 'bu'),
    ('pu', 'pu'),
    ('sa', 'sa'),
    ('sai', 'sai'),
    ('san', 'san'),
    ('sang', 'sang'),
    ('sao', 'sao'),
    ('se', 'se'),
    ('sen', 'sen'),
    ('seng', 'seng'),
    ('sha', 'sha'),
    ('shai', 'shai'),
    ('shan', 'shan'),
    ('shang', 'shang'),
    ('shao', 'shao'),
    ('she', 'she'),
    ('shen', 'shen'),
    ('sheng', 'sheng'),
    ('shih', 'shi'),
    ('shou', 'shou'),
    ('shu', 'shu'),
    ('shua', 'shua'),
    ('shuai', 'shuai'),
    ('shuan', 'shuan'),
    ('shuang', 'shuang'),
    ('shui', 'shui'),
    ('shun', 'shun'),
    ('shuo', 'shuo'),
    ('so', 'suo'),
    ('sou', 'sou'),
    ('ssu', 'si'),
    ('su', 'su'),
    ('suan', 'suan'),
    ('sui', 'sui'),
    ('sun', 'sun'),
    ('sung', 'song'),
    ('ta', 'da'),
    ('ta', 'ta'),
    ('tai', 'dai'),
    ('tai', 'tai'),
    ('tan', 'dan'),
    ('tan', 'tan'),
    ('tang', 'dang'),
    ('tang', 'tang'),
    ('tao', 'dao'),
    ('tao', 'tao'),
    ('te', 'de'),
    ('te', 'te'),
    ('teng', 'deng'),
    ('teng', 'teng'),
    ('ti', 'di'),
    ('ti', 'ti'),
    ('tiao', 'diao'),
    ('tiao', 'tiao'),
    ('tieh', 'die'),
    ('toeh', 'tie'),
    ('tien', 'dian'),
    ('tien', 'tian'),
    ('ting', 'ding'),
    ('ting', 'ting'),
    ('tiu', 'diu'),
    ('do', 'duo'),  # added this myself, as I saw "Long Keduo" -> "Long Kodo"
    ('to', 'duo'),
    ('to', 'tuo'),
    ('tou', 'dou'),
    ('tou', 'tou'),
    ('tu', 'du'),
    ('tu', 'tu'),
    ('tuan', 'duan'),
    ('tuan', 'tuan'),
    ('tui', 'dui'),
    ('tui', 'tui'),
    ('tun', 'dun'),
    ('tun', 'tun'),
    ('tung', 'dong'),
    ('tung', 'tong'),
    ('tsa', 'za'),
    ('tsa', 'ca'),
    ('tsai', 'zai'),
    ('tsai', 'cai'),
    ('tsan', 'zan'),
    ('tsan', 'can'),
    ('tsang', 'zang'),
    ('tsang', 'cang'),
    ('tsao', 'zao'),
    ('tsao', 'cao'),
    ('tse', 'ze'),
    ('tse', 'ce'),
    ('tsei', 'zei'),
    ('tsen', 'zen'),
    ('tsen', 'cen'),
    ('tseng', 'zeng'),
    ('tseng', 'ceng'),
    ('tso', 'zuo'),
    ('tso', 'cuo'),
    ('tsou', 'zou'),
    ('tsou', 'cou'),
    ('tsu', 'zu'),
    ('tsu', 'cu'),
    ('tsuan', 'zuan'),
    ('tsuan', 'cuan'),
    ('tsui', 'zui'),
    ('tsui', 'cui'),
    ('tsun', 'zun'),
    ('tsun', 'cun'),
    ('tsung', 'zong'),
    ('tsung', 'cong'),
    ('tzu', 'zi'),
    ('tzu', 'ci'),
    ('wa', 'wa'),
    ('wai', 'wai'),
    ('wan', 'wan'),
    ('wang', 'wang'),
    ('wei', 'wei'),
    ('wen', 'wen'),
    ('weng', 'weng'),
    ('wo', 'wo'),
    ('wu', 'wu'),
    ('ya', 'ya'),
    ('yai', 'yai'),
    ('yang', 'yang'),
    ('yao', 'yao'),
    ('yeh', 'ye'),
    ('yen', 'yan'),
    ('yin', 'yin'),
    ('ying', 'ying'),
    ('yo', 'yo'),
    ('yu', 'you'),
    ('yu', 'yu'),
    ('yuan', 'yuan'),
    ('yueh', 'yue'),
    ('yun', 'yun'),
    ('yung', 'yong'),
]

PINYIN_SYLLABLES = list(sorted(list(set([py for wg, py in wade_giles_pinyin_pairs]))))
WADE_GILES_SYLLABLES = list(sorted(list(set([wg for wg, py in wade_giles_pinyin_pairs]))))

pinyin_wade_giles_conversion_table = defaultdict(list)
wade_giles_pinyin_conversion_table = defaultdict(list)
for wg, py in wade_giles_pinyin_pairs:
    pinyin_wade_giles_conversion_table[py].append(wg)
    wade_giles_pinyin_conversion_table[wg].append(py)

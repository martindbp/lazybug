HANZI_WINDOW_SIZE = 10

POS_WINDOW_SIZE = 2

def 得(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('DE'):
        if next_psos[1].startswith('Cba'):
            if prev_psos[-1].startswith('VC'):
                return 'dei3'
            else:
                return 'de5'
        else:
            if prev_psos[-1].startswith('VD'):
                if prev_psos[0].startswith('N'):
                    return 'de5'
                else:
                    return 'dei3'
            else:
                if prev_psos[0].startswith('Ncd'):
                    if next_psos[0].startswith('Dfa'):
                        return 'de5'
                    else:
                        return 'de5'
                else:
                    if next_psos[1].startswith('DE'):
                        return 'de5'
                    else:
                        return 'de5'
    else:
        if pos.startswith('D'):
            if next_psos[1].startswith('VH'):
                return 'de5'
            else:
                if prev_psos[-1].startswith('DE'):
                    return 'de5'
                else:
                    if next_psos[0].startswith('VF'):
                        return 'de2'
                    else:
                        return 'dei3'
        else:
            if prev_psos[-1].startswith('DE'):
                if prev_psos[0].startswith('N'):
                    return 'dei3'
                else:
                    return 'de5'
            else:
                if next_psos[0].startswith('Neu'):
                    return 'dei3'
                else:
                    if prev_psos[-1].startswith('V'):
                        return 'de5'
                    else:
                        return 'de2'


def 好(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('VJ'):
        return 'hao3'
    else:
        return 'hao3'


def 难(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('V'):
        return 'nan2'
    else:
        return 'nan4'


def 长(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('Dfa'):
        return 'chang2'
    else:
        if prev_psos[-1].startswith('VH'):
            if next_psos[0].startswith('I'):
                return 'zhang3'
            else:
                return 'chang2'
        else:
            if next_psos[0].startswith('Q'):
                return 'chang2'
            else:
                if prev_psos[0].startswith('Nep'):
                    return 'chang2'
                else:
                    return 'zhang3'


def 干(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[0].startswith('T'):
        return 'gan4'
    else:
        return 'gan4'


def 没(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('VC'):
        return 'mei2'
    else:
        return 'mei2'


def 还(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('VD'):
        return 'huan2'
    else:
        return 'hai2'


def 过(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('V'):
        return 'guo4'
    else:
        return 'guo5'


def 为(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('V'):
        return 'wei2'
    else:
        return 'wei4'


def 啊(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('_'):
        if next_psos[1].startswith('Q'):
            return 'a4'
        else:
            if next_psos[1].startswith('Dk'):
                return 'a4'
            else:
                return 'a3'
    else:
        if pos.startswith('T'):
            if next_psos[1].startswith('Neqa'):
                return 'a1'
            else:
                return 'a5'
        else:
            if prev_psos[0].startswith('Q'):
                return 'a4'
            else:
                return 'a1'


def 把(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('Nf'):
        return 'ba3'
    else:
        return 'ba3'


def 打(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('Nf'):
        return 'da2'
    else:
        return 'da3'


def 要(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('VB'):
        return 'yao1'
    else:
        return 'yao4'


def 发(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('Nh'):
        return 'fa4'
    else:
        return 'fa1'


def 和(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('$'):
        if pos.startswith('P'):
            return 'huo4'
        else:
            return 'he2'
    else:
        if prev_psos[0].startswith('^'):
            return 'he2'
        else:
            return 'he2'


def 看(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('DE'):
        return 'kan1'
    else:
        return 'kan4'


def 着(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('V'):
        return 'zhao2'
    else:
        return 'zhe5'


def 种(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('VC'):
        return 'zhong4'
    else:
        return 'zhong3'


def 地(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('N'):
        return 'di4'
    else:
        return 'de5'


def 切(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('V'):
        if next_psos[1].startswith('S'):
            return 'qie4'
        else:
            return 'qie1'
    else:
        return 'qie4'


def 更(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('Nb'):
        if prev_psos[-1].startswith('N'):
            return 'geng1'
        else:
            return 'geng4'
    else:
        if prev_psos[-1].startswith('Nc'):
            return 'geng4'
        else:
            return 'geng4'


def 吧(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[0].startswith('T'):
        return 'ba1'
    else:
        return 'ba5'


def 尽(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[0].startswith('VC'):
        return 'jin3'
    else:
        return 'jin4'


def 中(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('VJ'):
        return 'zhong4'
    else:
        return 'zhong1'


def 哇(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('Na'):
        if pos.startswith('Q'):
            return 'wa1'
        else:
            return 'wa5'
    else:
        if next_psos[1].startswith('Q'):
            return 'wa5'
        else:
            if next_psos[1].startswith('Neu'):
                return 'wa5'
            else:
                return 'wa1'


def 哪(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('T'):
        return 'na5'
    else:
        return 'na3'


def 倒(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('SHI'):
        return 'dao3'
    else:
        if next_psos[1].startswith('Dfa'):
            return 'dao3'
        else:
            if next_psos[1].startswith('Nf'):
                return 'dao3'
            else:
                return 'dao4'


def 哦(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('Dk'):
        if pos.startswith('I'):
            return 'o4'
        else:
            return 'o4'
    else:
        if prev_psos[-1].startswith('V'):
            if next_psos[1].startswith('Nh'):
                return 'e2'
            else:
                return 'o5'
        else:
            if next_psos[1].startswith('N'):
                if next_psos[1].startswith('Nep'):
                    return 'e2'
                else:
                    return 'o4'
            else:
                if next_psos[1].startswith('VH'):
                    return 'e2'
                else:
                    return 'o5'


def 相(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('V'):
        return 'xiang4'
    else:
        return 'xiang1'


def 只(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('Neu'):
        return 'zhi1'
    else:
        return 'zhi3'


def 行(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('N'):
        return 'hang2'
    else:
        return 'xing2'


def 当(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('V'):
        return 'dang1'
    else:
        return 'dang1'


def 蒙(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('P'):
        return 'meng2'
    else:
        return 'meng1'


def 句(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('VE'):
        return 'ju4'
    else:
        return 'ju4'


def 背(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('VG'):
        return 'bei1'
    else:
        return 'bei4'


def 抢(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('Nh'):
        return 'qiang3'
    else:
        return 'qiang1'


def 藏(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('P'):
        return 'zang4'
    else:
        return 'cang2'


def 教(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[0].startswith('Q'):
        return 'jiao4'
    else:
        return 'jiao1'


def 唉(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('Nh'):
        return 'ai1'
    else:
        return 'ai1'


def 差(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('V'):
        return 'chai1'
    else:
        return 'cha4'


def 场(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('VHC'):
        return 'chang2'
    else:
        return 'chang3'


def 熬(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('N'):
        return 'ao1'
    else:
        return 'ao2'


def 系(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('N'):
        return 'xi4'
    else:
        return 'ji4'


def 转(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[0].startswith('Na'):
        return 'zhuan3'
    else:
        return 'zhuan4'


def 喂(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('V'):
        return 'wei2'
    else:
        return 'wei4'


def 露(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('Q'):
        return 'lu4'
    else:
        return 'lou4'


def 撒(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('N'):
        return 'sa1'
    else:
        return 'sa3'


def 供(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('N'):
        return 'gong1'
    else:
        return 'gong4'


def 咳(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[-1].startswith('N'):
        return 'ke2'
    else:
        return 'hai1'


def 令(prev_psos, pos, next_psos, prev_words, next_words):
    if prev_psos[0].startswith('Na'):
        return 'ling3'
    else:
        return 'ling4'


def 数(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('N'):
        return 'shu4'
    else:
        return 'shu3'


def 冲(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('$'):
        return 'chong1'
    else:
        return 'chong4'


def 量(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('Na'):
        return 'liang4'
    else:
        return 'liang2'


def 钻(prev_psos, pos, next_psos, prev_words, next_words):
    if pos.startswith('VC'):
        return 'zuan1'
    else:
        return 'zuan4'


def 趟(prev_psos, pos, next_psos, prev_words, next_words):
    if next_psos[1].startswith('V'):
        return 'tang1'
    else:
        return 'tang4'
single_readings = {
	"的": "de5",
	"了": "le5",
	"都": "dou1",
	"我": "wo3",
	"去": "qu4",
	"不": "bu4",
	"跑": "pao3",
	"快": "kuai4",
	"做": "zuo4",
	"走": "zou3",
	"他": "ta1",
	"天": "tian1",
	"冷": "leng3",
	"你": "ni3",
	"多": "duo1",
	"穿": "chuan1",
	"说": "shuo1",
	"很": "hen3",
	"踢": "ti1",
	"这": "zhe4",
	"字": "zi4",
	"写": "xie3",
	"几": "ji3",
	"次": "ci4",
	"她": "ta1",
	"唱": "chang4",
	"太": "tai4",
	"慢": "man4",
	"车": "che1",
	"按": "an4",
	"拍": "pai1",
	"可": "ke3",
	"是": "shi4",
	"出": "chu1",
	"吗": "ma5",
	"往": "wang3",
	"前": "qian2",
	"那": "na4",
	"用": "yong4",
	"到": "dao4",
	"就": "jiu4",
	"散": "san4",
	"各": "ge4",
	"妈": "ma1",
	"路": "lu4",
	"边": "bian1",
	"租": "zu1",
	"十": "shi2",
	"个": "ge4",
	"跟": "gen1",
	"声": "sheng1",
	"在": "zai4",
	"久": "jiu3",
	"小": "xiao3",
	"倔": "jue2",
	"起": "qi3",
	"给": "gei3",
	"呢": "ne5",
	"见": "jian4",
	"面": "mian4",
	"脸": "lian3",
	"上": "shang4",
	"又": "you4",
	"一": "yi1",
	"等": "deng3",
	"也": "ye3",
	"鸫": "dong1",
	"爱": "ai4",
	"先": "xian1",
	"变": "bian4",
	"身": "shen1",
	"烫": "tang4",
	"卷": "juan3",
	"摸": "mo1",
	"来": "lai2",
	"刨": "bao4",
	"而": "er2",
	"动": "dong4",
	"块": "kuai4",
	"再": "zai4",
	"两": "liang3",
	"啥": "sha2",
	"件": "jian4",
	"爸": "ba4",
	"但": "dan4",
	"呜": "wu1",
	"别": "bie2",
	"哭": "ku1",
	"将": "jiang1",
	"会": "hui4",
	"向": "xiang4",
	"省": "sheng3",
	"部": "bu4",
	"委": "wei3",
	"从": "cong2",
	"月": "yue4",
	"号": "hao4",
	"全": "quan2",
	"国": "guo2",
	"型": "xing2",
	"自": "zi4",
	"年": "nian2",
	"应": "ying1",
	"超": "chao1",
	"薄": "bao2",
	"最": "zui4",
	"光": "guang1",
	"分": "fen1",
	"钟": "zhong1",
	"完": "wan2",
	"对": "dui4",
	"呀": "ya5",
	"人": "ren2",
	"大": "da4",
	"想": "xiang3",
	"住": "zhu4",
	"下": "xia4",
	"八": "ba1",
	"套": "tao4",
	"代": "dai4",
	"生": "sheng1",
	"养": "yang3",
	"每": "mei3",
	"像": "xiang4",
	"醉": "zui4",
	"酒": "jiu3",
	"有": "you3",
	"篇": "pian1",
	"送": "song4",
	"之": "zhi1",
	"西": "xi1",
	"辞": "ci2",
	"唯": "wei2",
	"流": "liu2",
	"让": "rang4",
	"必": "bi4",
	"克": "ke4",
	"于": "yu2",
	"其": "qi2",
	"坐": "zuo4",
	"连": "lian2",
	"成": "cheng2",
	"风": "feng1",
	"般": "ban1",
	"四": "si4",
	"以": "yi3",
	"里": "li3",
	"话": "hua4",
	"问": "wen4",
	"缘": "yuan2",
	"娶": "qu3",
	"红": "hong2",
	"墙": "qiang2",
	"抹": "mo3",
	"白": "bai2",
	"床": "chuang2",
	"粒": "li4",
	"饭": "fan4",
	"颗": "ke1",
	"使": "shi3",
	"狗": "gou3",
	"真": "zhen1",
	"乖": "guai1",
	"心": "xin1",
	"口": "kou3",
	"睡": "shui4",
	"哎": "ai1",
	"才": "cai2",
	"早": "zao3",
	"台": "tai2",
	"晚": "wan3",
	"放": "fang4",
	"高": "gao1",
	"嘛": "ma5",
	"末": "mo4",
	"哈": "ha1",
	"六": "liu4",
	"股": "gu3",
	"所": "suo3",
	"却": "que4",
	"此": "ci3",
	"众": "zhong4",
	"融": "rong2",
	"合": "he2",
	"刚": "gang1",
	"推": "tui1",
	"受": "shou4",
	"挑": "tiao1",
	"染": "ran3",
	"并": "bing4",
	"能": "neng2",
	"点": "dian3",
	"强": "qiang2",
	"它": "ta1",
	"集": "ji2",
	"仍": "reng2",
	"家": "jia1",
	"堆": "dui1",
	"敢": "gan3",
	"们": "men5",
	"提": "ti2",
	"拌": "ban4",
	"被": "bei4",
	"饿": "e4",
	"吃": "chi1",
	"菜": "cai4",
	"帮": "bang1",
	"挂": "gua4",
	"屋": "wu1",
	"室": "shi4",
	"内": "nei4",
	"嘘": "xu1",
	"亦": "yi4",
	"开": "kai1",
	"选": "xuan3",
	"啦": "la5",
	"位": "wei4",
	"门": "men2",
	"与": "yu3",
	"蛮": "man2",
	"懂": "dong3",
	"些": "xie1",
	"则": "ze2",
	"化": "hua4",
	"何": "he2",
	"乐": "le4",
	"听": "ting1",
	"持": "chi2",
	"诸": "zhu1",
	"事": "shi4",
	"顺": "shun4",
	"带": "dai4",
	"求": "qiu2",
	"签": "qian1",
	"拜": "bai4",
	"信": "xin4",
	"算": "suan4",
	"新": "xin1",
	"宁": "ning4",
	"无": "wu2",
	"挺": "ting3",
	"常": "chang2",
	"找": "zhao3",
	"灵": "ling2",
	"曾": "ceng2",
	"时": "shi2",
	"破": "po4",
	"准": "zhun3",
	"越": "yue4",
	"神": "shen2",
	"总": "zong3",
	"因": "yin1",
	"果": "guo3",
	"乱": "luan4",
	"造": "zao4",
	"靠": "kao4",
	"拿": "na2",
	"手": "shou3",
	"梦": "meng4",
	"某": "mou3",
	"愿": "yuan4",
	"错": "cuo4",
	"网": "wang3",
	"周": "zhou1",
	"披": "pi1",
	"捧": "peng3",
	"换": "huan4",
	"学": "xue2",
	"火": "huo3",
	"奇": "qi2",
	"缺": "que1",
	"较": "jiao4",
	"初": "chu1",
	"具": "ju4",
	"及": "ji2",
	"低": "di1",
	"段": "duan4",
	"后": "hou4",
	"泡": "pao4",
	"穷": "qiong2",
	"响": "xiang3",
	"揭": "jie1",
	"锅": "guo1",
	"少": "shao3",
	"谁": "shei2",
	"赚": "zhuan4",
	"比": "bi3",
	"挣": "zheng4",
	"钱": "qian2",
	"够": "gou4",
	"买": "mai3",
	"房": "fang2",
	"急": "ji2",
	"沉": "chen2",
	"气": "qi4",
	"迟": "chi2",
	"条": "tiao2",
	"接": "jie1",
	"据": "ju4",
	"跌": "die1",
	"涨": "zhang3",
	"怪": "guai4",
	"虚": "xu1",
	"建": "jian4",
	"炒": "chao3",
	"咦": "yi2",
	"掰": "bai1",
	"喝": "he1",
	"瓶": "ping2",
	"二": "er4",
	"回": "hui2",
	"铁": "tie3",
	"坏": "huai4",
	"沾": "zhan1",
	"滴": "di1",
	"扔": "reng1",
	"外": "wai4",
	"讲": "jiang3",
	"撞": "zhuang4",
	"性": "xing4",
	"脑": "nao3",
	"病": "bing4",
	"通": "tong1",
	"杯": "bei1",
	"慌": "huang1",
	"戒": "jie4",
	"任": "ren4",
	"夜": "ye4",
	"糟": "zao1",
	"记": "ji4",
	"照": "zhao4",
	"症": "zheng4",
	"整": "zheng3",
	"守": "shou3",
	"苦": "ku3",
	"赶": "gan3",
	"特": "te4",
	"怕": "pa4",
	"锁": "suo3",
	"头": "tou2",
	"扛": "kang2",
	"同": "tong2",
	"磕": "ke1",
	"老": "lao3",
	"百": "bai3",
	"善": "shan4",
	"孝": "xiao4",
	"累": "lei4",
	"辣": "la4",
	"吹": "chui1",
	"烧": "shao1",
	"半": "ban4",
	"疼": "teng2",
	"热": "re4",
	"扯": "che3",
	"举": "ju3",
	"擦": "ca1",
	"哟": "yo1",
	"旺": "wang4",
	"疮": "chuang1",
	"臭": "chou4",
	"眼": "yan3",
	"惨": "can3",
	"咽": "yan4",
	"片": "pian4",
	"员": "yuan2",
	"满": "man3",
	"街": "jie1",
	"晕": "yun1",
	"卖": "mai4",
	"挤": "ji3",
	"站": "zhan4",
	"餐": "can1",
	"班": "ban1",
	"份": "fen4",
	"工": "gong1",
	"均": "jun1",
	"美": "mei3",
	"贵": "gui4",
	"恒": "heng2",
	"永": "yong3",
	"轻": "qing1",
	"招": "zhao1",
	"惹": "re3",
	"金": "jin1",
	"既": "ji4",
	"婚": "hun1",
	"结": "jie2",
	"叫": "jiao4",
	"牙": "ya2",
	"戴": "dai4",
	"饶": "rao2",
	"搬": "ban1",
	"胖": "pang4",
	"灾": "zai1",
	"名": "ming2",
	"假": "jia3",
	"骂": "ma4",
	"岁": "sui4",
	"管": "guan3",
	"严": "yan2",
	"玩": "wan2",
	"妻": "qi1",
	"三": "san1",
	"父": "fu4",
	"嫁": "jia4",
	"夫": "fu1",
	"亡": "wang2",
	"子": "zi3",
	"未": "wei4",
	"归": "gui1",
	"专": "zhuan1",
	"煮": "zhu3",
	"忘": "wang4",
	"聊": "liao2",
	"猫": "mao1",
	"患": "huan4",
	"笔": "bi3",
	"花": "hua1",
	"批": "pi1",
	"吵": "chao3",
	"联": "lian2",
	"七": "qi1",
	"读": "du2",
	"粗": "cu1",
	"搞": "gao3",
	"害": "hai4",
	"丑": "chou3",
	"或": "huo4",
	"词": "ci2",
	"埋": "mai2",
	"音": "yin1",
	"该": "gai1",
	"鲜": "xian1",
	"作": "zuo4",
	"硬": "ying4",
	"远": "yuan3",
	"帅": "shuai4",
	"五": "wu3",
	"捡": "jian3",
	"宝": "bao3",
	"抱": "bao4",
	"亲": "qin1",
	"贯": "guan4",
	"牛": "niu2",
	"座": "zuo4",
	"左": "zuo3",
	"犬": "quan3",
	"右": "you4",
	"草": "cao3",
	"深": "shen1",
	"治": "zhi4",
	"浅": "qian3",
	"力": "li4",
	"请": "qing3",
	"叹": "tan4",
	"礼": "li3",
	"情": "qing2",
	"意": "yi4",
	"重": "zhong4",
	"千": "qian1",
	"充": "chong1",
	"尚": "shang4",
	"项": "xiang4",
	"凑": "cou4",
	"收": "shou1",
	"止": "zhi3",
	"颁": "ban1",
	"念": "nian4",
	"横": "heng2",
	"竖": "shu4",
	"撇": "pie3",
	"捺": "na4",
	"折": "zhe2",
	"桥": "qiao2",
	"关": "guan1",
	"环": "huan2",
	"水": "shui3",
	"产": "chan3",
	"陡": "dou3",
	"爬": "pa2",
	"城": "cheng2",
	"耗": "hao4",
	"线": "xian4",
	"侧": "ce4",
	"米": "mi3",
	"付": "fu4",
	"祝": "zhu4",
	"九": "jiu3",
	"您": "nin2",
	"汤": "tang1",
	"锤": "chui2",
	"雇": "gu4",
	"步": "bu4",
	"办": "ban4",
	"迷": "mi2",
	"爽": "shuang3",
	"吸": "xi1",
	"碗": "wan3",
	"番": "fan1",
	"遍": "bian4",
	"山": "shan1",
	"间": "jian1",
	"圆": "yuan2",
	"序": "xu4",
	"色": "se4",
	"款": "kuan3",
	"趁": "chen4",
	"样": "yang4",
	"反": "fan3",
	"抓": "zhua1",
	"书": "shu1",
	"尺": "chi3",
	"顿": "dun4",
	"民": "min2",
	"桌": "zhuo1",
	"张": "zhang1",
	"嘴": "zui3",
	"拉": "la1",
	"由": "you2",
	"呗": "bei5",
	"随": "sui2",
	"吼": "hou3",
	"演": "yan3",
	"奖": "jiang3",
	"表": "biao3",
	"冬": "dong1",
	"药": "yao4",
	"闹": "nao4",
	"懒": "lan3",
	"正": "zheng4",
	"泳": "yong3",
	"适": "shi4",
	"练": "lian4",
	"市": "shi4",
	"耳": "er3",
	"实": "shi2",
	"知": "zhi1",
	"跳": "tiao4",
	"财": "cai2",
	"逗": "dou4",
	"粮": "liang2",
	"掉": "diao4",
	"沟": "gou1",
	"痣": "zhi4",
	"乘": "cheng2",
	"树": "shu4",
	"祭": "ji4",
	"扫": "sao3",
	"割": "ge1",
	"肉": "rou4",
	"杀": "sha1",
	"鸡": "ji1",
	"灌": "guan4",
	"贴": "tie1",
	"已": "yi3",
	"逝": "shi4",
	"睁": "zheng1",
	"呆": "dai1",
	"谈": "tan2",
	"忙": "mang2",
	"板": "ban3",
	"托": "tuo1",
	"票": "piao4",
	"加": "jia1",
	"扭": "niu3",
	"男": "nan2",
	"女": "nv3",
	"纹": "wen2",
	"忠": "zhong1",
	"仁": "ren2",
	"义": "yi4",
	"忍": "ren3",
	"毛": "mao2",
	"图": "tu2",
	"瘾": "yin3",
	"洗": "xi3",
	"亏": "kui1",
	"戏": "xi4",
	"笑": "xiao4",
	"额": "e2",
	"晓": "xiao3",
	"曰": "yue1",
	"妙": "miao4",
	"盐": "yan2",
	"绝": "jue2",
	"乍": "zha4",
	"冒": "mao4",
	"棒": "bang4",
	"装": "zhuang1",
	"噢": "o1",
	"歌": "ge1",
	"酸": "suan1",
	"胡": "hu2",
	"极": "ji2",
	"咯": "lo5",
	"隔": "ge2",
	"顶": "ding3",
	"压": "ya1",
	"瞎": "xia1",
	"剩": "sheng4",
	"衣": "yi1",
	"淘": "tao2",
	"略": "lve4",
	"瞧": "qiao2",
	"辆": "liang4",
	"死": "si3",
	"瞒": "man2",
	"湿": "shi1",
	"甩": "shuai3",
	"短": "duan3",
	"箱": "xiang1",
	"尾": "wei3",
	"酷": "ku4",
	"劝": "quan4",
	"进": "jin4",
	"福": "fu2",
	"吓": "xia4",
	"荤": "hun1",
	"欢": "huan1",
	"现": "xian4",
	"骗": "pian4",
	"闲": "xian2",
	"者": "zhe3",
	"升": "sheng1",
	"职": "zhi2",
	"群": "qun2",
	"离": "li2",
	"幅": "fu2",
	"画": "hua4",
	"陷": "xian4",
	"清": "qing1",
	"护": "hu4",
	"争": "zheng1",
	"摆": "bai3",
	"喘": "chuan3",
	"拼": "pin1",
	"命": "ming4",
	"嗨": "hai1",
	"陪": "pei2",
	"非": "fei1",
	"抖": "dou3",
	"称": "cheng1",
	"寻": "xun2",
	"王": "wang2",
	"谜": "mi2",
	"脚": "jiao3",
	"踩": "cai3",
	"净": "jing4",
	"娘": "niang2",
	"素": "su4",
	"夸": "kua1",
	"围": "wei2",
	"圈": "quan1",
	"逼": "bi1",
	"绑": "bang3",
	"弄": "nong4",
	"烦": "fan2",
	"副": "fu4",
	"盼": "pan4",
	"盯": "ding1",
	"服": "fu2",
	"级": "ji2",
	"闯": "chuang3",
	"思": "si1",
	"刻": "ke4",
	"赌": "du3",
	"牌": "pai2",
	"玄": "xuan2",
	"引": "yin3",
	"北": "bei3",
	"烂": "lan4",
	"叩": "kou4",
	"绕": "rao4",
	"答": "da2",
	"丢": "diu1",
	"傻": "sha3",
	"包": "bao1",
	"平": "ping2",
	"蠢": "chun3",
	"即": "ji2",
	"依": "yi1",
	"活": "huo2",
	"届": "jie4",
	"掷": "zhi4",
	"宽": "kuan1",
	"类": "lei4",
	"本": "ben3",
	"牵": "qian1",
	"耍": "shua3",
	"逛": "guang4",
	"登": "deng1",
	"碎": "sui4",
	"程": "cheng2",
	"订": "ding4",
	"厅": "ting1",
	"定": "ding4",
	"万": "wan4",
	"贪": "tan1",
	"店": "dian4",
	"货": "huo4",
	"仿": "fang3",
	"价": "jia4",
	"眨": "zha3",
	"原": "yuan2",
	"单": "dan1",
	"富": "fu4",
	"黑": "hei1",
	"香": "xiang1",
	"盒": "he2",
	"弱": "ruo4",
	"派": "pai4",
	"拳": "quan2",
	"刀": "dao1",
	"广": "guang3",
	"炫": "xuan4",
	"磨": "mo2",
	"替": "ti4",
	"电": "dian4",
	"配": "pei4",
	"旧": "jiu4",
	"废": "fei4",
	"区": "qu1",
	"笨": "ben4",
	"熊": "xiong2",
	"怀": "huai2",
	"痛": "tong4",
	"纸": "zhi3",
	"鬼": "gui3",
	"蛇": "she2",
	"鸟": "niao3",
	"冰": "bing1",
	"谢": "xie4",
	"另": "ling4",
	"底": "di3",
	"处": "chu4",
	"姓": "xing4",
	"母": "mu3",
	"资": "zi1",
	"排": "pai2",
	"辈": "bei4",
	"土": "tu3",
	"兵": "bing1",
	"飞": "fei1",
	"婷": "ting2",
	"萍": "ping2",
	"菲": "fei1",
	"若": "ruo4",
	"族": "zu2",
	"党": "dang3",
	"约": "yue1",
	"期": "qi1",
	"陆": "lu4",
	"境": "jing4",
	"入": "ru4",
	"创": "chuang4",
	"迈": "mai4",
	"理": "li3",
	"占": "zhan4",
	"顾": "gu4",
	"日": "ri4",
	"糖": "tang2",
	"茶": "cha2",
	"酱": "jiang4",
	"醋": "cu4",
	"业": "ye4",
	"困": "kun4",
	"借": "jie4",
	"闷": "men1",
	"愁": "chou2",
	"泼": "po1",
	"勇": "yong3",
	"谋": "mou2",
	"如": "ru2",
	"计": "ji4",
	"恩": "en1",
	"经": "jing1",
	"元": "yuan2",
	"甲": "jia3",
	"方": "fang1",
	"乙": "yi3",
	"朝": "chao2",
	"烈": "lie4",
	"度": "du4",
	"黄": "huang2",
	"甜": "tian2",
	"偏": "pian1",
	"纯": "chun2",
	"咸": "xian2",
	"吐": "tu4",
	"斤": "jin1",
	"闻": "wen2",
	"暖": "nuan3",
	"壶": "hu2",
	"伴": "ban4",
	"迫": "po4",
	"盖": "gai4",
	"跪": "gui4",
	"摊": "tan1",
	"截": "jie2",
	"窄": "zhai3",
	"裹": "guo3",
	"改": "gai3",
	"吊": "diao4",
	"根": "gen1",
	"筋": "jin1",
	"便": "bian4",
	"谍": "die2",
	"稳": "wen3",
	"居": "ju1",
	"节": "jie2",
	"野": "ye3",
	"校": "xiao4",
	"鱼": "yu2",
	"翘": "qiao4",
	"尖": "jian1",
	"留": "liu2",
	"细": "xi4",
	"猜": "cai1",
	"至": "zhi4",
	"赴": "fu4",
	"聚": "ju4",
	"闰": "run4",
	"双": "shuang1",
	"镜": "jing4",
	"曲": "qu3",
	"梅": "mei2",
	"龙": "long2",
	"鹿": "lu4",
	"角": "jiao3",
	"鹰": "ying1",
	"试": "shi4",
	"游": "you2",
	"农": "nong2",
	"牧": "mu4",
	"村": "cun1",
	"近": "jin4",
	"考": "kao3",
	"易": "yi4",
	"混": "hun4",
	"稍": "shao1",
	"挡": "dang3",
	"拆": "chai1",
	"物": "wu4",
	"稀": "xi1",
	"落": "luo4",
	"雁": "yan4",
	"凭": "ping2",
	"传": "chuan2",
	"呛": "qiang4",
	"惯": "guan4",
	"肚": "du4",
	"球": "qiu2",
	"空": "kong1",
	"鞋": "xie2",
	"投": "tou2",
	"斩": "zhan3",
	"味": "wei4",
	"料": "liao4",
	"道": "dao4",
	"互": "hu4",
	"嗜": "shi4",
	"葱": "cong1",
	"题": "ti2",
	"滑": "hua2",
	"沿": "yan2",
	"油": "you2",
	"羹": "geng1",
	"技": "ji4",
	"喊": "han3",
	"达": "da2",
	"童": "tong2",
	"咱": "zan2",
	"云": "yun2",
	"咬": "yao3",
	"窗": "chuang1",
	"设": "she4",
	"倍": "bei4",
	"厂": "chang3",
	"查": "cha2",
	"毒": "du2",
	"赢": "ying2",
	"除": "chu2",
	"法": "fa3",
	"支": "zhi1",
	"值": "zhi2",
	"江": "jiang1",
	"碟": "die2",
	"巧": "qiao3",
	"销": "xiao1",
	"馋": "chan2",
	"直": "zhi2",
	"钗": "chai1",
	"解": "jie3",
	"嚷": "rang3",
	"繁": "fan2",
	"简": "jian3",
	"版": "ban3",
	"邮": "you2",
	"取": "qu3",
	"习": "xi2",
	"东": "dong1",
	"龟": "gui1",
	"链": "lian4",
	"指": "zhi3",
	"且": "qie3",
	"俊": "jun4",
	"颇": "po1",
	"攒": "zan3",
	"架": "jia4",
	"海": "hai3",
	"蓝": "lan2",
	"掏": "tao1",
	"厚": "hou4",
	"叠": "die2",
	"页": "ye4",
	"封": "feng1",
	"负": "fu4",
	"码": "ma3",
	"堑": "qian4",
	"智": "zhi4",
	"交": "jiao1",
	"精": "jing1",
	"羊": "yang2",
	"哼": "heng1",
	"扣": "kou4",
	"英": "ying1",
	"体": "ti3",
	"罪": "zui4",
	"亮": "liang4",
	"猛": "meng3",
	"抬": "tai2",
	"助": "zhu4",
	"烟": "yan1",
	"船": "chuan2",
	"锏": "jian3",
	"钓": "diao4",
	"蹲": "dun1",
	"判": "pan4",
	"社": "she4",
	"失": "shi1",
	"胃": "wei4",
	"饱": "bao3",
	"停": "ting2",
	"嘿": "hei1",
	"潜": "qian2",
	"追": "zhui1",
	"腻": "ni4",
	"痒": "yang3",
	"针": "zhen1",
	"狠": "hen3",
	"爆": "bao4",
	"剪": "jian3",
	"抽": "chou1",
	"界": "jie4",
	"垒": "lei3",
	"李": "li3",
	"楼": "lou2",
	"鼓": "gu3",
	"静": "jing4",
	"陈": "chen2",
	"层": "ceng2",
	"脱": "tuo1",
	"紧": "jin3",
	"偷": "tou1",
	"摇": "yao2",
	"罚": "fa2",
	"庙": "miao4",
	"绿": "lv4",
	"奶": "nai3",
	"哄": "hong3",
	"串": "chuan4",
	"拎": "lin1",
	"玉": "yu4",
	"哨": "shao4",
	"课": "ke4",
	"饼": "bing3",
	"洒": "sa3",
	"凶": "xiong1",
	"伤": "shang1",
	"拔": "ba2",
	"烤": "kao3",
	"费": "fei4",
	"姜": "jiang1",
	"降": "jiang4",
	"季": "ji4",
	"告": "gao4",
	"暗": "an4",
	"布": "bu4",
	"输": "shu1",
	"耶": "ye1",
	"灯": "deng1",
	"栏": "lan2",
	"零": "ling2",
	"粉": "fen3",
	"编": "bian1",
	"偶": "ou3",
	"紫": "zi3",
	"首": "shou3",
	"弹": "tan2",
	"瘦": "shou4",
	"壮": "zhuang4",
	"填": "tian2",
	"队": "dui4",
	"苏": "su1",
	"织": "zhi1",
	"笼": "long2",
	"阴": "yin1",
	"雨": "yu3",
	"皱": "zhou4",
	"南": "nan2",
	"需": "xu1",
	"轮": "lun2",
	"洞": "dong4",
	"补": "bu3",
	"松": "song1",
	"骑": "qi2",
	"修": "xiu1",
	"诗": "shi1",
	"列": "lie4",
	"桶": "tong3",
	"待": "dai1",
	"嚼": "jiao2",
	"蛀": "zhu4",
	"报": "bao4",
	"透": "tou4",
	"盘": "pan2",
	"垫": "dian4",
	"腿": "tui3",
	"砰": "peng1",
	"星": "xing1",
	"束": "shu4",
	"软": "ruan3",
	"卡": "ka3",
	"刷": "shua1",
	"局": "ju2",
	"瞄": "miao2",
	"袋": "dai4",
	"喏": "nuo4",
	"握": "wo4",
	"宠": "chong3",
	"喔": "o1",
	"闪": "shan3",
	"喷": "pen1",
	"汗": "han4",
	"奔": "ben4",
	"狂": "kuang2",
	"恕": "shu4",
	"矛": "mao2",
	"盾": "dun4",
	"牢": "lao2",
	"刺": "ci4",
	"沙": "sha1",
	"播": "bo1",
	"么": "ma5",
	"蟹": "xie4",
	"脏": "zang4",
	"腰": "yao1",
	"禅": "chan2",
	"团": "tuan2",
	"享": "xiang3",
	"师": "shi1",
	"焉": "yan1",
	"文": "wen2",
	"须": "xu1",
	"渐": "jian4",
	"寸": "cun4",
	"拨": "bo1",
	"赖": "lai4",
	"刘": "liu2",
	"梯": "ti1",
	"户": "hu4",
	"明": "ming2",
	"胸": "xiong1",
	"朵": "duo3",
	"评": "ping2",
	"敬": "jing4",
	"俗": "su2",
	"喽": "lou5",
	"肺": "fei4",
	"润": "run4",
	"狼": "lang2",
	"虾": "xia1",
	"驻": "zhu4",
	"组": "zu3",
	"认": "ren4",
	"挖": "wa1",
	"录": "lu4",
	"憋": "bie1",
	"田": "tian2",
	"艘": "sou1",
	"突": "tu1",
	"堵": "du3",
	"熟": "shu2",
	"枪": "qiang1",
	"担": "dan1",
	"拖": "tuo1",
	"踏": "ta4",
	"昏": "hun1",
	"啪": "pa1",
	"轰": "hong1",
	"哐": "kuang1",
	"咣": "guang1",
	"咻": "xiu1",
	"调": "tiao2",
	"浓": "nong2",
	"晒": "shai4",
	"存": "cun2",
	"哥": "ge1",
	"健": "jian4",
	"马": "ma3",
	"访": "fang3",
	"疯": "feng1",
	"旁": "pang2",
	"摔": "shuai1",
	"钩": "gou1",
	"翻": "fan1",
	"徐": "xu2",
	"塌": "ta1",
	"躲": "duo3",
	"碰": "peng4",
	"警": "jing3",
	"隆": "long2",
	"恨": "hen4",
	"抄": "chao1",
	"肯": "ken3",
	"减": "jian3",
	"误": "wu4",
	"呵": "he1",
	"秋": "qiu1",
	"皆": "jie1",
	"贼": "zei2",
	"舞": "wu3",
	"炸": "zha4",
	"插": "cha1",
	"忆": "yi4",
	"式": "shi4",
	"浪": "lang4",
	"赛": "sai4",
	"搅": "jiao3",
	"缠": "chan2",
	"娇": "jiao1",
	"展": "zhan3",
	"馆": "guan3",
	"训": "xun4",
	"躺": "tang3",
	"操": "cao1",
	"苟": "gou3",
	"乃": "nai3",
	"迁": "qian1",
	"恶": "e4",
	"劲": "jin4",
	"尝": "chang2",
	"遇": "yu4",
	"盛": "sheng4",
	"阳": "yang2",
	"衰": "shuai1",
	"秀": "xiu4",
	"视": "shi4",
	"趋": "qu1",
	"秒": "miao3",
	"岛": "dao3",
	"呈": "cheng2",
	"磅": "bang4",
	"柱": "zhu4",
	"跨": "kua4",
	"黏": "nian2",
	"胆": "dan3",
	"微": "wei1",
	"淡": "dan4",
	"怡": "yi2",
	"朱": "zhu1",
	"制": "zhi4",
	"猪": "zhu1",
	"幺": "yao1",
	"退": "tui4",
	"墓": "mu4",
	"兔": "tu4",
	"觉": "jiao4",
	"铺": "pu4",
	"拐": "guai3",
	"赵": "zhao4",
	"机": "ji1",
	"颠": "dian1",
	"呸": "pei1",
	"章": "zhang1",
	"划": "hua2",
	"备": "bei4",
	"蛋": "dan4",
	"孵": "fu1",
	"羡": "xian4",
	"仙": "xian1",
	"雅": "ya3",
	"权": "quan2",
	"势": "shi4",
	"显": "xian3",
	"煤": "mei2",
	"嗅": "xiu4",
	"兆": "zhao4"
}
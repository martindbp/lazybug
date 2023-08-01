
const STOPWORDS = [
    "sth",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "it",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "these",
    "those",
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "a",
    "an",
    "the",
    "and",
    "but",
    "if",
    "or",
    "because",
    "as",
    "until",
    "while",
    "of",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "s",
    "t",
    "can",
    "will",
    "just",
    "don",
    "'t",
    "'s",
    "should",
    "now",
];

const PINYIN_TONE_MARKS = {
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
};

function convertToDiacritical(match, removeTonalNumber = true) {
    const tone = parseInt(match[3], 10) % 5;
    let r = match[1].replace('v', 'ü').replace('V', 'Ü');
    let pos = 0;

    if (r.length > 1 && !'aeoAEO'.includes(r[0])) {
        pos = 1;
    }

    if (tone !== 0) {
        r = r.slice(0, pos) + PINYIN_TONE_MARKS[r[pos]][tone - 1] + r.slice(pos + 1);
    }

    let converted = r + match[2];
    if (!removeTonalNumber) {
        converted += match[3];
    }

    return converted;
}

function normalizedToDiacritical(pinyin) {
    const regex = /([aeiouüvÜr]{1,3})(n?g?r?)([012345])/gi;
    return pinyin.replace(regex, function (match, p1, p2, p3) {
        return convertToDiacritical([match, p1, p2, p3]);
    });
}

const DIACRITICAL_TABLE = {
    '\u0304': '1',
    '\u0301': '2',
    '\u030C': '3',
    '\u0300': '4'
};

function translateDiacriticalToNumber(s) {
    return s.normalize("NFD").split('').map(function(char) {
        return DIACRITICAL_TABLE[char] || char;
    }).join('');
}

function removeDiacriticals(s) {
    return translateDiacriticalToNumber(s).replace(/[0-5]/g, '');
}

function isHanzi(char) {
    let ranges = [['\u4E00', '\u9FFF'], ['\u3400', '\u4DBF'], ['\uF900', '\uFAFF']];
    for(let i = 0; i < ranges.length; i++) {
        let start = ranges[i][0].charCodeAt(0);
        let end = ranges[i][1].charCodeAt(0);
        if(char.charCodeAt(0) >= start && char.charCodeAt(0) <= end) {
            return true;
        }
    }
    return false;
}

function filterTextHanzi(text) {
    let result = '';
    for(let i = 0; i < text.length; i++) {
        let char = text.charAt(i);
        if(isHanzi(char)) {
            result += char;
        }
    }
    return result;
}

function filterStopWords(text) {
    const words = text.split(' ');
    const nonStopWords = [];
    for (const word of words) {
        if (STOPWORDS.includes(word.toLowerCase())) continue;
        nonStopWords.push(word);
    }

    if (nonStopWords.length > 0) return nonStopWords.join(' ');
    else return text;
}

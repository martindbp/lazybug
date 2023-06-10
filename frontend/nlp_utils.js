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

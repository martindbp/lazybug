let DICT = null;
let HSK_WORDS = null;

const CAPTION_FADEOUT_TIME = 5;
function getWordLevel(hz) {
    let wordLevel = null;
    for (let lvl = 0; lvl <= 5; lvl++) {
        if (HSK_WORDS[lvl].includes(hz)) {
            wordLevel = lvl+1;
            break;
        }
    }
    return wordLevel;
};

const fetchVersionedResource = function (filename, callback) {
    chrome.runtime.sendMessage({'type': 'fetchVersionedResource', 'filename': filename}, function onResponse(message) {
        if (message === 'error') {
            return false;
        }
        if (message === undefined || message == null) {
            console.log('Failed to fetch ' + filename);
            return false;
        }
        callback(message.data);
        return true;
    });
};

fetchVersionedResource('cedict_with_freqs.json', function (data) { DICT = data; });
fetchVersionedResource('hsk_words.json', function (data) { HSK_WORDS = data; });

const YOUTUBE_REGEXP = /(?:https?:\/{2})?(?:w{3}\.)?youtu(?:be)?\.(?:com|be)(?:\/watch\?v=|\/)([^\s&]+)/;
function getYoutubeIdFromURL(url) {
    const match = url.match(YOUTUBE_REGEXP);
    if (match === null) return null;
    return match[1];
}


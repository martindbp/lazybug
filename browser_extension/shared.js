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

// SVG icons from css.gg
const ICON_SVG = {
    'play-track-next': '<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 24 24" fill="none"><path d="M6 17L14 12L6 7V17Z" fill="currentColor"/><path d="M18 7H15V12V17H18V7Z" fill="currentColor"/></svg>',
    'play-track-prev': '<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 24 24" fill="none"><path d="M18 17L10 12L18 7V17Z" fill="currentColor"/><path d="M6 7H9V17H6V7Z" fill="currentColor"/></svg>',
    'move': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M7.75739 5.04077L9.1716 6.45498L11.0001 4.62652V10H13.0001V4.62661L14.8284 6.45498L16.2426 5.04077L12 0.798126L7.75739 5.04077Z" fill="currentColor" /><path d="M16.2426 18.9593L14.8284 17.545L13.0001 19.3734V14H11.0001V19.3735L9.1716 17.545L7.75739 18.9593L12 23.2019L16.2426 18.9593Z" fill="currentColor" /><path d="M5.65698 9.17157L4.24276 7.75735L0.00012207 12L4.24276 16.2426L5.65698 14.8284L3.82858 13H10.0001V11H3.82851L5.65698 9.17157Z" fill="currentColor" /><path d="M14.0001 11V13H20.1716L18.3432 14.8284L19.7574 16.2426L24.0001 12L19.7574 7.75735L18.3432 9.17157L20.1717 11H14.0001Z" fill="currentColor" /></svg>',
    'play-button': '<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 24 24" fill="none"><path d="M15 12.3301L9 16.6603L9 8L15 12.3301Z" fill="currentColor"/></svg>',
    'play-pause': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M11 7H8V17H11V7Z" fill="currentColor" /><path d="M13 17H16V7H13V17Z" fill="currentColor" /></svg>',
    'math-plus': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M12 4C11.4477 4 11 4.44772 11 5V11H5C4.44772 11 4 11.4477 4 12C4 12.5523 4.44772 13 5 13H11V19C11 19.5523 11.4477 20 12 20C12.5523 20 13 19.5523 13 19V13H19C19.5523 13 20 12.5523 20 12C20 11.4477 19.5523 11 19 11H13V5C13 4.44772 12.5523 4 12 4Z" fill="currentColor" /></svg>',
    'math-minus': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M4 12C4 11.4477 4.44772 11 5 11H19C19.5523 11 20 11.4477 20 12C20 12.5523 19.5523 13 19 13H5C4.44772 13 4 12.5523 4 12Z" fill="currentColor" /></svg>',
    'redo': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M13.1459 11.0499L12.9716 9.05752L15.3462 8.84977C14.4471 7.98322 13.2242 7.4503 11.8769 7.4503C9.11547 7.4503 6.87689 9.68888 6.87689 12.4503C6.87689 15.2117 9.11547 17.4503 11.8769 17.4503C13.6977 17.4503 15.2911 16.4771 16.1654 15.0224L18.1682 15.5231C17.0301 17.8487 14.6405 19.4503 11.8769 19.4503C8.0109 19.4503 4.87689 16.3163 4.87689 12.4503C4.87689 8.58431 8.0109 5.4503 11.8769 5.4503C13.8233 5.4503 15.5842 6.24474 16.853 7.52706L16.6078 4.72412L18.6002 4.5498L19.1231 10.527L13.1459 11.0499Z" fill="currentColor" /></svg>',
    'eye': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path fill-rule="evenodd" clip-rule="evenodd" d="M16 12C16 14.2091 14.2091 16 12 16C9.79086 16 8 14.2091 8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12ZM14 12C14 13.1046 13.1046 14 12 14C10.8954 14 10 13.1046 10 12C10 10.8954 10.8954 10 12 10C13.1046 10 14 10.8954 14 12Z" fill="currentColor" /><path fill-rule="evenodd" clip-rule="evenodd" d="M12 3C17.5915 3 22.2898 6.82432 23.6219 12C22.2898 17.1757 17.5915 21 12 21C6.40848 21 1.71018 17.1757 0.378052 12C1.71018 6.82432 6.40848 3 12 3ZM12 19C7.52443 19 3.73132 16.0581 2.45723 12C3.73132 7.94186 7.52443 5 12 5C16.4756 5 20.2687 7.94186 21.5428 12C20.2687 16.0581 16.4756 19 12 19Z" fill="currentColor" /></svg>',
    'options': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path fill-rule="evenodd" clip-rule="evenodd" d="M7 3C8.86384 3 10.4299 4.27477 10.874 6H19V8H10.874C10.4299 9.72523 8.86384 11 7 11C4.79086 11 3 9.20914 3 7C3 4.79086 4.79086 3 7 3ZM7 9C8.10457 9 9 8.10457 9 7C9 5.89543 8.10457 5 7 5C5.89543 5 5 5.89543 5 7C5 8.10457 5.89543 9 7 9Z" fill="currentColor" /><path fill-rule="evenodd" clip-rule="evenodd" d="M17 20C15.1362 20 13.5701 18.7252 13.126 17H5V15H13.126C13.5701 13.2748 15.1362 12 17 12C19.2091 12 21 13.7909 21 16C21 18.2091 19.2091 20 17 20ZM17 18C18.1046 18 19 17.1046 19 16C19 14.8954 18.1046 14 17 14C15.8954 14 15 14.8954 15 16C15 17.1046 15.8954 18 17 18Z" fill="currentColor" /> </svg>',
}

function getIconSvg(name, size) {
    if (ICON_SVG[name] === undefined) {
        console.log('No icon named', name);
    }
    return ICON_SVG[name].replace('${width}', size).replace('${height}', size);
}

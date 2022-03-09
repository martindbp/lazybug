const events = [
    'EVENT_SHOW_CAPTION_IDX',
    'EVENT_REPLAY_CAPTION',
    'EVENT_SHOW_DICTIONARY_RANGE',
    'EVENT_PEEK_ALL',
    'EVENT_PEEK_ROW_PY',
    'EVENT_PEEK_ROW_HZ',
    'EVENT_PEEK_ROW_TR',
    'EVENT_PEEK_TRANSLATION',
    'EVENT_PIN_ROW_PY',
    'EVENT_PIN_ROW_HZ',
    'EVENT_PIN_ROW_TR',
    'EVENT_PIN_ROW_TRANSLATION',
    'EVENT_PEEK_PY',
    'EVENT_PEEK_HZ',
    'EVENT_PEEK_TR',
    'EVENT_KNOW_PY',
    'EVENT_KNOW_HZ',
    'EVENT_KNOW_TR',
    'EVENT_KNOW_AUTO_PY',
    'EVENT_KNOW_AUTO_HZ',
    'EVENT_KNOW_AUTO_TR',
    'EVENT_LEARN_PY',
    'EVENT_LEARN_HZ',
    'EVENT_LEARN_TR',
    'EVENT_LEARN_AUTO_PY',
    'EVENT_LEARN_AUTO_HZ',
    'EVENT_LEARN_AUTO_TR',
    'EVENT_REMOVE_PY',
    'EVENT_REMOVE_HZ',
    'EVENT_REMOVE_TR',
    'EVENT_BLUR',
];

const eventsMap = {};
const reverseEventsMap = {};

for (let i = 0; i < events.length; i++) {
    eventsMap[events[i]] = i;
    reverseEventsMap[i] = events[i];
}

function getEvent(eventName, contentType) {
    return eventsMap[`EVENT_${eventName.toUpperCase()}_${contentType.toUpperCase()}`];
}

const CAPTION_FADEOUT_TIME = 5;
function fetchVersionedResource(filename, callback) {
    chrome.runtime.sendMessage({type: 'fetchVersionedResource', filename: filename}, function onResponse(message) {
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

function getIndexedDbData(storageName, keys, callback) {
    chrome.runtime.sendMessage({type: 'getIndexedDbData', storage: storageName, keys: keys}, function onResponse(message) {
        if (message === 'error') {
            return false;
        }
        if (message === undefined || message == null) {
            console.log('Failed to get data ' + keys);
            return false;
        }
        callback(message.data);
        return true;
    });
}

function setIndexedDbData(storageName, keys, values, callback) {
    chrome.runtime.sendMessage({type: 'setIndexedDbData', storage: storageName, keys: keys, values: values}, function onResponse(message) {
        if (message === 'error') {
            return false;
        }
        if (callback) callback();
        return true;
    });
}

function clearIndexedDb() {
    chrome.runtime.sendMessage({type: 'clearIndexedDb'}, function onResponse(message) {
        return true;
    });
}

function createSession(state) {
    console.log('Create session', state.captionId, state.captionHash, state.sessionTime);
    chrome.runtime.sendMessage({
        type: 'createSession',
        captionId: state.captionId,
        captionHash: state.captionHash,
        sessionTime: state.sessionTime
    }, function onResponse(message) {
        return true;
    });
}

function appendSessionLog(state, data) {
    console.log('Append log', state.captionId, state.captionHash, state.sessionTime, data);
    chrome.runtime.sendMessage({
        type: 'appendSessionLog',
        captionId: state.captionId,
        captionHash: state.captionHash,
        sessionTime: state.sessionTime,
        data: data,
    }, function onResponse(message) {
        return true;
    });
}

function getLog(callback) {
    return chrome.runtime.sendMessage({
        type: 'getLog',
    }, function onResponse(message) {
        callback(message.data);
        return true;
    });
}

const YOUTUBE_REGEXP = /(?:https?:\/{2})?(?:w{3}\.)?youtu(?:be)?\.(?:com|be)(?:\/watch\?v=|\/)([^\s&]+)/;
function getYoutubeIdFromURL(url) {
    const match = url.match(YOUTUBE_REGEXP);
    if (match === null) return null;
    return match[1];
}

function dictArrayToDict(arr) {
    return {
        hzTrad: arr[0],
        pys: arr[1],
        pysDiacriticals: arr[2],
        translations: arr[3],
    };
}

function dictItemsToDict(items) {
    const out = [];
    for (var item of items) {
        out.push(dictArrayToDict(item));
    }
    return out;
}

function captionArrayToDict(arr, captionData) {
    let [texts, t0s, t1s, boundingRects, charProbs, logprob, data_hash, translations, alignments] = arr;

    if (boundingRects.length === 1 && boundingRects[0] === null) {
        // The video has soft captions
        if (captionData.caption_top !== undefined && captionData.caption_bottom !== undefined) {
            // But the video also has hard captions that need to be blurred
            const xMin = captionData.frame_size[1] * 0.2;
            const xMax = captionData.frame_size[1] * 0.8;
            const yMin = 0;
            const yMax = captionData.frame_size[0] * (captionData.caption_bottom - captionData.caption_top);
            boundingRects = [[xMin, xMax, yMin, yMax]];
        }
        else {
            boundingRects = [];
        }
    }

    return {
        texts: texts,
        t0s: t0s,
        t1s: t1s,
        t0: t0s[0],
        t1: t1s[t1s.length-1],
        boundingRects: boundingRects,
        charProbs: charProbs,
        logprob: logprob,
        data_hash: data_hash,
        translations: translations,
        alignments: alignments,
    };
}

function isName(tr) {
    // NOTE: we say it's a name if there is _any_ capitalzied character, e.g. "lao Ni"
    return /[A-Z]/.test(tr) && !(tr.startsWith('I') || tr.startsWith("I'"));
}

function getKnowledgeKey(type, hz, pys, tr, translation) {
    let key = null;
    if (pys === null && ['py', 'tr'].includes(type)) return null;
    var pysWithoutTones = ['py', 'tr'].includes(type) ? pys.map(py => py.slice(0, -1)) : null;
    if (type == 'hz') key = `hz-${hz}`;
    if (type == 'py') key = `py-${hz}-${pysWithoutTones.join('/')}`;
    if (type == 'tr') {
        if (tr && isName(tr)) {
            // If the translation is capitalized, we want it to be tracked separately
            key = `tr-${hz}-${pysWithoutTones.join('/')}-${tr}`;
        }
        else {
            key = `tr-${hz}-${pysWithoutTones.join('/')}`;
        }
    }
    if (type == 'translation') key = `tr-${translation}`;
    return key;
}

function applyKnowledge(DICT, knowledge, type, hz, pys, tr, translation, knowledgeVal, syncIndexedDb = false) {
    const keys = [];
    const vals = [];
    let key = getKnowledgeKey(type, hz, pys, tr, translation);
    keys.push(key);
    vals.push(setKnowledge(knowledge, key, knowledgeVal));

    if (['hz', 'py', 'tr'].includes(type)) {
        // Add all the individual char/pys
        for (let startIdx = 0; startIdx < hz.length; startIdx++) {
            for (let endIdx = startIdx+1; endIdx < hz.length+1; endIdx++) {
                const hzSub = hz.substring(startIdx, endIdx);
                const pysSub = pys !== null ? pys.slice(startIdx, endIdx) : null;
                if (DICT[hzSub] === undefined) continue;

                key = getKnowledgeKey(type, hzSub, pysSub, tr, translation);
                keys.push(key);
                vals.push(setKnowledge(
                    knowledge,
                    key,
                    knowledgeVal
                ));
            }
        }
    }

    if (syncIndexedDb) {
        setIndexedDbData('knowledge', keys, vals, function() {});
    }
}

const KnowledgeUnknown = 0;
const KnowledgeKnown = 1;
const KnowledgeLearning = 2;

function setKnowledge(dict, key, newState) {
    let currCounts = dict[key];
    if (currCounts === undefined) {
        currCounts = [0, 0];
    }

    let prevState = KnowledgeUnknown;
    if (currCounts[KnowledgeLearning-1] > 0) {
        prevState = KnowledgeLearning;
    }
    else if (currCounts[KnowledgeKnown-1] > 0) {
        prevState = KnowledgeKnown;
    }

    if (prevState > 0) {
        currCounts[prevState-1] -= 1;
    }

    currCounts[newState-1] += 1;

    dict[key] = currCounts;
    return currCounts;
}

function getKnowledgeState(dict, key) {
    const knowledgeState = dict[key];
    if (knowledgeState  === undefined) return undefined;
    if (knowledgeState[0] > 0) return KnowledgeKnown;
    if (knowledgeState[1] > 0) return KnowledgeLearning;
    return KnowledgeUnknown;
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
    'replay': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M13.1459 11.0499L12.9716 9.05752L15.3462 8.84977C14.4471 7.98322 13.2242 7.4503 11.8769 7.4503C9.11547 7.4503 6.87689 9.68888 6.87689 12.4503C6.87689 15.2117 9.11547 17.4503 11.8769 17.4503C13.6977 17.4503 15.2911 16.4771 16.1654 15.0224L18.1682 15.5231C17.0301 17.8487 14.6405 19.4503 11.8769 19.4503C8.0109 19.4503 4.87689 16.3163 4.87689 12.4503C4.87689 8.58431 8.0109 5.4503 11.8769 5.4503C13.8233 5.4503 15.5842 6.24474 16.853 7.52706L16.6078 4.72412L18.6002 4.5498L19.1231 10.527L13.1459 11.0499Z" fill="currentColor" /></svg>',
    'eye': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path fill-rule="evenodd" clip-rule="evenodd" d="M16 12C16 14.2091 14.2091 16 12 16C9.79086 16 8 14.2091 8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12ZM14 12C14 13.1046 13.1046 14 12 14C10.8954 14 10 13.1046 10 12C10 10.8954 10.8954 10 12 10C13.1046 10 14 10.8954 14 12Z" fill="currentColor" /><path fill-rule="evenodd" clip-rule="evenodd" d="M12 3C17.5915 3 22.2898 6.82432 23.6219 12C22.2898 17.1757 17.5915 21 12 21C6.40848 21 1.71018 17.1757 0.378052 12C1.71018 6.82432 6.40848 3 12 3ZM12 19C7.52443 19 3.73132 16.0581 2.45723 12C3.73132 7.94186 7.52443 5 12 5C16.4756 5 20.2687 7.94186 21.5428 12C20.2687 16.0581 16.4756 19 12 19Z" fill="currentColor" /></svg>',
    'options': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path fill-rule="evenodd" clip-rule="evenodd" d="M7 3C8.86384 3 10.4299 4.27477 10.874 6H19V8H10.874C10.4299 9.72523 8.86384 11 7 11C4.79086 11 3 9.20914 3 7C3 4.79086 4.79086 3 7 3ZM7 9C8.10457 9 9 8.10457 9 7C9 5.89543 8.10457 5 7 5C5.89543 5 5 5.89543 5 7C5 8.10457 5.89543 9 7 9Z" fill="currentColor" /><path fill-rule="evenodd" clip-rule="evenodd" d="M17 20C15.1362 20 13.5701 18.7252 13.126 17H5V15H13.126C13.5701 13.2748 15.1362 12 17 12C19.2091 12 21 13.7909 21 16C21 18.2091 19.2091 20 17 20ZM17 18C18.1046 18 19 17.1046 19 16C19 14.8954 18.1046 14 17 14C15.8954 14 15 14.8954 15 16C15 17.1046 15.8954 18 17 18Z" fill="currentColor" /> </svg>',
    'book': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-book"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>',
    'book-plus': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-book"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path><g transform="scale(0.5,0.5),translate(12,8)"><path d="M12 4C11.4477 4 11 4.44772 11 5V11H5C4.44772 11 4 11.4477 4 12C4 12.5523 4.44772 13 5 13H11V19C11 19.5523 11.4477 20 12 20C12.5523 20 13 19.5523 13 19V13H19C19.5523 13 20 12.5523 20 12C20 11.4477 19.5523 11 19 11H13V5C13 4.44772 12.5523 4 12 4Z" fill="currentColor" /></g></svg>',
    'undo': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M5.33929 4.46777H7.33929V7.02487C8.52931 6.08978 10.0299 5.53207 11.6607 5.53207C15.5267 5.53207 18.6607 8.66608 18.6607 12.5321C18.6607 16.3981 15.5267 19.5321 11.6607 19.5321C9.51025 19.5321 7.58625 18.5623 6.30219 17.0363L7.92151 15.8515C8.83741 16.8825 10.1732 17.5321 11.6607 17.5321C14.4222 17.5321 16.6607 15.2935 16.6607 12.5321C16.6607 9.77065 14.4222 7.53207 11.6607 7.53207C10.5739 7.53207 9.56805 7.87884 8.74779 8.46777L11.3393 8.46777V10.4678H5.33929V4.46777Z" fill="currentColor" /></svg>',
    'check': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M10.2426 16.3137L6 12.071L7.41421 10.6568L10.2426 13.4853L15.8995 7.8284L17.3137 9.24262L10.2426 16.3137Z" fill="currentColor" /><path fill-rule="evenodd" clip-rule="evenodd" d="M1 5C1 2.79086 2.79086 1 5 1H19C21.2091 1 23 2.79086 23 5V19C23 21.2091 21.2091 23 19 23H5C2.79086 23 1 21.2091 1 19V5ZM5 3H19C20.1046 3 21 3.89543 21 5V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3Z" fill="currentColor" /></svg>',
    'close': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M16.3956 7.75734C16.7862 8.14786 16.7862 8.78103 16.3956 9.17155L13.4142 12.153L16.0896 14.8284C16.4802 15.2189 16.4802 15.8521 16.0896 16.2426C15.6991 16.6331 15.0659 16.6331 14.6754 16.2426L12 13.5672L9.32458 16.2426C8.93405 16.6331 8.30089 16.6331 7.91036 16.2426C7.51984 15.8521 7.51984 15.2189 7.91036 14.8284L10.5858 12.153L7.60436 9.17155C7.21383 8.78103 7.21383 8.14786 7.60436 7.75734C7.99488 7.36681 8.62805 7.36681 9.01857 7.75734L12 10.7388L14.9814 7.75734C15.372 7.36681 16.0051 7.36681 16.3956 7.75734Z" fill="currentColor" /><path fill-rule="evenodd" clip-rule="evenodd" d="M4 1C2.34315 1 1 2.34315 1 4V20C1 21.6569 2.34315 23 4 23H20C21.6569 23 23 21.6569 23 20V4C23 2.34315 21.6569 1 20 1H4ZM20 3H4C3.44772 3 3 3.44772 3 4V20C3 20.5523 3.44772 21 4 21H20C20.5523 21 21 20.5523 21 20V4C21 3.44772 20.5523 3 20 3Z" fill="currentColor" /></svg>',
    'study': '<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 122.88 101.37"><path d="M12.64,77.27l0.31-54.92h-6.2v69.88c8.52-2.2,17.07-3.6,25.68-3.66c7.95-0.05,15.9,1.06,23.87,3.76 c-4.95-4.01-10.47-6.96-16.36-8.88c-7.42-2.42-15.44-3.22-23.66-2.52c-1.86,0.15-3.48-1.23-3.64-3.08 C12.62,77.65,12.62,77.46,12.64,77.27L12.64,77.27z M103.62,19.48c-0.02-0.16-0.04-0.33-0.04-0.51c0-0.17,0.01-0.34,0.04-0.51V7.34 c-7.8-0.74-15.84,0.12-22.86,2.78c-6.56,2.49-12.22,6.58-15.9,12.44V85.9c5.72-3.82,11.57-6.96,17.58-9.1 c6.85-2.44,13.89-3.6,21.18-3.02V19.48L103.62,19.48z M110.37,15.6h9.14c1.86,0,3.37,1.51,3.37,3.37v77.66 c0,1.86-1.51,3.37-3.37,3.37c-0.38,0-0.75-0.06-1.09-0.18c-9.4-2.69-18.74-4.48-27.99-4.54c-9.02-0.06-18.03,1.53-27.08,5.52 c-0.56,0.37-1.23,0.57-1.92,0.56c-0.68,0.01-1.35-0.19-1.92-0.56c-9.04-4-18.06-5.58-27.08-5.52c-9.25,0.06-18.58,1.85-27.99,4.54 c-0.34,0.12-0.71,0.18-1.09,0.18C1.51,100.01,0,98.5,0,96.64V18.97c0-1.86,1.51-3.37,3.37-3.37h9.61l0.06-11.26 c0.01-1.62,1.15-2.96,2.68-3.28l0,0c8.87-1.85,19.65-1.39,29.1,2.23c6.53,2.5,12.46,6.49,16.79,12.25 c4.37-5.37,10.21-9.23,16.78-11.72c8.98-3.41,19.34-4.23,29.09-2.8c1.68,0.24,2.88,1.69,2.88,3.33h0V15.6L110.37,15.6z M68.13,91.82c7.45-2.34,14.89-3.3,22.33-3.26c8.61,0.05,17.16,1.46,25.68,3.66V22.35h-5.77v55.22c0,1.86-1.51,3.37-3.37,3.37 c-0.27,0-0.53-0.03-0.78-0.09c-7.38-1.16-14.53-0.2-21.51,2.29C79.09,85.15,73.57,88.15,68.13,91.82L68.13,91.82z M58.12,85.25 V22.46c-3.53-6.23-9.24-10.4-15.69-12.87c-7.31-2.8-15.52-3.43-22.68-2.41l-0.38,66.81c7.81-0.28,15.45,0.71,22.64,3.06 C47.73,78.91,53.15,81.64,58.12,85.25L58.12,85.25z" fill="currentColor" stroke-width="2" stroke="white" /></svg>',
    'dictionary': '<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 122.88 96.44"><path d="M12,73.51q.2-34.74.39-69.38A3.21,3.21,0,0,1,15,1h0C23.4-.75,36.64-.31,45.63,3.14a35.46,35.46,0,0,1,16,11.65,37.34,37.34,0,0,1,16-11.15C86.12.4,99-.38,108.23,1A3.2,3.2,0,0,1,111,4.14h0V73.8A3.21,3.21,0,0,1,107.77,77a3.49,3.49,0,0,1-.74-.09A53.45,53.45,0,0,0,83.58,79.1a71,71,0,0,0-15.77,8.26,69.09,69.09,0,0,1,21.24-3.1,125.42,125.42,0,0,1,27.41,3.48V14.84h3.21a3.21,3.21,0,0,1,3.21,3.21V91.94a3.21,3.21,0,0,1-3.21,3.21,3.18,3.18,0,0,1-1-.17A121.77,121.77,0,0,0,89,90.65a61.89,61.89,0,0,0-25.76,5.26,3.39,3.39,0,0,1-3.64,0,61.86,61.86,0,0,0-25.76-5.26A121.77,121.77,0,0,0,4.24,95a3.18,3.18,0,0,1-1,.17A3.21,3.21,0,0,1,0,91.94V18.05a3.21,3.21,0,0,1,3.21-3.21H6.42v72.9a125.42,125.42,0,0,1,27.41-3.48,68.84,68.84,0,0,1,22.71,3.57A48.7,48.7,0,0,0,41,79.39c-7-2.3-17.68-3.07-25.49-2.4A3.21,3.21,0,0,1,12,74.06a5,5,0,0,1,0-.55ZM73.64,64.4a2.3,2.3,0,1,1-2.5-3.85,51.46,51.46,0,0,1,11.8-5.4,53.73,53.73,0,0,1,13-2.67,2.29,2.29,0,1,1,.25,4.58,49.42,49.42,0,0,0-11.79,2.46A46.73,46.73,0,0,0,73.64,64.4Zm.2-17.76a2.29,2.29,0,0,1-2.46-3.87,52.71,52.71,0,0,1,11.74-5.3A54.12,54.12,0,0,1,95.9,34.85a2.3,2.3,0,0,1,.25,4.59,49.3,49.3,0,0,0-11.63,2.4,48,48,0,0,0-10.68,4.8Zm.06-17.7a2.3,2.3,0,1,1-2.46-3.89,52.54,52.54,0,0,1,11.72-5.27,53.71,53.71,0,0,1,12.74-2.6,2.29,2.29,0,1,1,.25,4.58,49.35,49.35,0,0,0-11.59,2.39A47.91,47.91,0,0,0,73.9,28.94ZM51.74,60.55a2.3,2.3,0,1,1-2.5,3.85,46.73,46.73,0,0,0-10.72-4.88,49.42,49.42,0,0,0-11.79-2.46A2.29,2.29,0,1,1,27,52.48a53.73,53.73,0,0,1,13,2.67,51.46,51.46,0,0,1,11.8,5.4ZM51.5,42.77A2.29,2.29,0,0,1,49,46.64a48,48,0,0,0-10.68-4.8,49.3,49.3,0,0,0-11.63-2.4A2.3,2.3,0,0,1,27,34.85a54.12,54.12,0,0,1,12.78,2.62,52.71,52.71,0,0,1,11.74,5.3Zm-.06-17.72A2.3,2.3,0,1,1,49,28.94a47.91,47.91,0,0,0-10.66-4.79,49.35,49.35,0,0,0-11.59-2.39A2.29,2.29,0,1,1,27,17.18a53.71,53.71,0,0,1,12.74,2.6,52.54,52.54,0,0,1,11.72,5.27ZM104.56,7c-7.42-.7-18.06.12-24.73,2.65A30,30,0,0,0,64.7,21.46V81.72a76.76,76.76,0,0,1,16.72-8.66,62.85,62.85,0,0,1,23.14-2.87V7ZM58.28,81.1V21.37c-3.36-5.93-8.79-9.89-14.93-12.24-7-2.67-17.75-3.27-24.56-2.3l-.36,63.56c7.43-.27,17.69.68,24.52,2.91a54.94,54.94,0,0,1,15.33,7.8Z" fill="currentColor" stroke-width="1" stroke="white" /></svg>',
    'pin': '<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 100 100"><path d="M85.4 45L54.9 14.6c-2.8-2.9-3.5-1.1-3.5.3v14L28.7 45.7H15c-3.9 0-.8 4.2-1.4 3.5l17.2 17.1-14.4 14.5c-.8.8-.8 2.1 0 2.9.8.8 2.1.8 2.9 0l14.4-14.4 17.1 17.2c-.5-.5 3.6 2.2 3.6-1.4V71.3l16.8-22.7h12.7c2.1-.1 4.9-.1 1.5-3.6zm-65.5 4.6h8.9l21.7 21.7v8.9L19.9 49.6zm32.5 17.7L32.7 47.6 52.8 33l14.4 14.6-14.8 19.7zm17.8-22.7L55.4 29.8v-8.9l23.7 23.7h-8.9z" fill="currentColor" stroke-width="4" stroke="white" /><path fill="currentColor" stroke-width="4" stroke="white" d="M804-1070V614H-980v-1684H804m8-8H-988V622H812v-1700z"/></svg>',
    'unpin': '<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 100 100"><path d="M85.4 45L54.9 14.6c-2.8-2.9-3.5-1.1-3.5.3v14L28.7 45.7H15c-3.9 0-.8 4.2-1.4 3.5l17.2 17.1-14.4 14.5c-.8.8-.8 2.1 0 2.9.8.8 2.1.8 2.9 0l14.4-14.4 17.1 17.2c-.5-.5 3.6 2.2 3.6-1.4V71.3l16.8-22.7h12.7c2.1-.1 4.9-.1 1.5-3.6zm-65.5 4.6h8.9l21.7 21.7v8.9L19.9 49.6zm32.5 17.7L32.7 47.6 52.8 33l14.4 14.6-14.8 19.7zm17.8-22.7L55.4 29.8v-8.9l23.7 23.7h-8.9z" fill="currentColor" stroke-width="4" stroke="white" /><path fill="currentColor" stroke-width="4" stroke="white" d="M804-1070V614H-980v-1684H804m8-8H-988V622H812v-1700z"/><line x1="10" y1="10" x2="90" y2="90" style="stroke-width: 4; stroke: white;" /></svg>',
    'pen': '<svg viewBox="0 0 24 24" width="${width}" height="${height}" fill="none" xmlns="http://www.w3.org/2000/svg" ><path fill-rule="evenodd" clip-rule="evenodd" d="M21.2635 2.29289C20.873 1.90237 20.2398 1.90237 19.8493 2.29289L18.9769 3.16525C17.8618 2.63254 16.4857 2.82801 15.5621 3.75165L4.95549 14.3582L10.6123 20.0151L21.2189 9.4085C22.1426 8.48486 22.338 7.1088 21.8053 5.99367L22.6777 5.12132C23.0682 4.7308 23.0682 4.09763 22.6777 3.70711L21.2635 2.29289ZM16.9955 10.8035L10.6123 17.1867L7.78392 14.3582L14.1671 7.9751L16.9955 10.8035ZM18.8138 8.98525L19.8047 7.99429C20.1953 7.60376 20.1953 6.9706 19.8047 6.58007L18.3905 5.16586C18 4.77534 17.3668 4.77534 16.9763 5.16586L15.9853 6.15683L18.8138 8.98525Z" fill="currentColor" /> <path d="M2 22.9502L4.12171 15.1717L9.77817 20.8289L2 22.9502Z" fill="currentColor" /></svg>',
}

function getIconSvg(name, size) {
    if (ICON_SVG[name] === undefined) {
        console.log('No icon named', name);
    }
    return ICON_SVG[name].replace('${width}', size).replace('${height}', size);
}

const CDN_URL = "https://cdn.lazybug.ai/file/";
const CAPTION_FADEOUT_TIME = 5;
const CHINESE_NUMBERS_REGEX = /^[一二三四五六七八九十百千万个]+$/;
const SESSION_ID = uuidv4();
let nextRequestId = 1;
const requestCallbacks = {}; // map between SESSION_ID+request_id to a callback handler

let lazybugIframe = null;

if (BROWSER_EXTENSION && !BACKGROUND_SCRIPT) {
    lazybugIframe = document.createElement('iframe');
    lazybugIframe.src = 'https://lazybug.ai/iframe.html';
    lazybugIframe.style = 'position: absolute;width:0;height:0;border:0;';
    document.body.appendChild(lazybugIframe);
}

const events = [
    'EVENT_SHOW_CAPTION_IDX',
    'EVENT_REPLAY_CAPTION',
    'EVENT_SHOW_DICTIONARY_RANGE',
    'EVENT_PEEK_ALL',
    'EVENT_PEEK_ROW_PY',
    'EVENT_PEEK_ROW_HZ',
    'EVENT_PEEK_ROW_TR',
    'EVENT_PEEK_ROW_TRANSLATION',
    'EVENT_PIN_ROW_PY',
    'EVENT_PIN_ROW_HZ',
    'EVENT_PIN_ROW_TR',
    'EVENT_PIN_ROW_TRANSLATION',
    'EVENT_PEEK_PY',
    'EVENT_PEEK_HZ',
    'EVENT_PEEK_TR',
    'EVENT_PEEK_WORD',
    'EVENT_PEEK_TRANSLATION',
    'EVENT_HIDE_WORD',
    'EVENT_HIDE_AUTO_WORD',
    'EVENT_STAR_CAPTION',
    'EVENT_STAR_WORD',
    'EVENT_STAR_TRANSLATION',
    'EVENT_PIN_WORD',
    'EVENT_UNSTAR_CAPTION',
    'EVENT_UNSTAR_WORD',
    'EVENT_UNSTAR_TRANSLATION',
    'EVENT_BLUR',
];

const eventsMap = {};
const reverseEventsMap = {};

for (let i = 0; i < events.length; i++) {
    eventsMap[events[i]] = i;
    reverseEventsMap[i] = events[i];
}

function uuidv4() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

function getEvent(eventName, contentType) {
    return eventsMap[`EVENT_${eventName.toUpperCase()}_${contentType.toUpperCase()}`];
}

function sendMessageToBackground(message, callback) {
    const responseHandler = function onResponse(response) {
        if (['error'].includes(response)) {
            console.log('Failed for message ', message);
            if (callback) callback('error');
            return false;
        }
        if (callback) {
            if ([null, undefined].includes(response)) callback(response);
            else callback(response.data);
        }
        return true;
    }

    if (BROWSER_EXTENSION && !BACKGROUND_SCRIPT) {
        // Send to iframe
        const requestId = `${SESSION_ID}-${nextRequestId}`;

        // Need to do this to make sure object is cloneable
        const data = JSON.parse(JSON.stringify({
            message: message,
            requestId: requestId,
        }));
        lazybugIframe.contentWindow.postMessage(data, '*');
        requestCallbacks[requestId] = responseHandler;
        nextRequestId += 1;
    }
    else {
        // Call directly
        message = JSON.parse(JSON.stringify(message));
        backgroundMessageHandler(message, null, responseHandler);
    }
}

if (BROWSER_EXTENSION && !BACKGROUND_SCRIPT) {
    // Listen for messages from the lazybug iframe
    window.addEventListener("message", message => {
        if (message.data.requestId === undefined) return;

        let callback = requestCallbacks[message.data.requestId];
        callback(message.data.data);
        delete requestCallbacks[message.data.requestId];
    });
}

function fetchCaptions(captionId, callback) {
    sendMessageToBackground({type: 'getCaptions',  'data': {
        'captionId': captionId,
    }}, callback);
}

function fetchResource(filename, callback) {
    sendMessageToBackground({type: 'fetchResource', filename: filename}, callback);
};

function fetchVersionedResource(filename, callback) {
    sendMessageToBackground({type: 'fetchVersionedResource', filename: filename}, callback);
};

function getIndexedDbData(storageName, keys, callback) {
    sendMessageToBackground({type: 'getIndexedDbData', storage: storageName, keys: keys}, callback);
}

function setIndexedDbData(storageName, keys, values, callback) {
    sendMessageToBackground({type: 'setIndexedDbData', storage: storageName, keys: keys, values: values}, callback);
}

function clearCache() {
    sendMessageToBackground({type: 'clearCache'});
}

function clearPersonalData(callback) {
    sendMessageToBackground({type: 'clearPersonalData'}, callback);
}

function exportDatabaseJson(callback) {
    sendMessageToBackground({type: 'exportDatabaseJson'}, callback);
}

function importDatabaseJson(data, callback) {
    sendMessageToBackground({type: 'importDatabaseJson', data: data}, callback);
}

function fetchPersonalDataToStore(store) {
    getIndexedDbData('states', null, function (data) {
        if (data) {
            const dict = {};
            for (const item of data) {
                dict[item.id] = item.value;
            }
            store.commit('setStates', dict);
        }
    });

    getIndexedDbData('other', ['options'], function (data) {
        if (data !== 'error' && data[0]) store.commit('setOptions', data[0]);
        else {
            // No options, so we set the default
            setIndexedDbData('other', ['options'], [store.state.options], function() {});
        }
    });
}

function appendSessionLog(state, data) {
    const showId = state.captionData.show_name;
    const [showName, seasonIdx, seasonName, episodeIdx, episodeName] = getShowSeasonEpisode(getShowInfo(null, state), state.captionId);
    console.log('Append log', state.captionId, state.captionHash, state.sessionTime, data, showName, seasonName, episodeName);
    sendMessageToBackground({
        type: 'appendSessionLog',
        sessionData: {
            captionId: state.captionId,
            captionHash: state.captionHash,
            sessionTime: state.sessionTime,
            showId: showId,
            seasonIdx: seasonIdx,
            episodeIdx: episodeIdx,
        },
        data: data,
    });
}

function getLog(offset, limit, callback) {
    return sendMessageToBackground({
        type: 'getLog',
        offset: offset,
        limit: limit,
    }, callback);
}

function getViewingHistory(offset, limit, callback) {
    return sendMessageToBackground({
        type: 'getViewingHistory',
        offset: offset,
        limit: limit,
        dedupeLast: true,
    }, callback);
}

function getLogRows(callback) {
    return sendMessageToBackground({
        type: 'getLogRows',
    }, callback);
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

function findVideoInShowInfo(showInfo, captionId) {
    for (let i = 0; i < showInfo.seasons.length; i++) {
        for (let j = 0; j < showInfo.seasons[i].episodes.length; j++) {
            if (showInfo.seasons[i].episodes[j].id === captionId) {
                return [i, j];
            }
        }
    }

    return [null, null];
}

function captionArrayToDict(arr, captionData) {
    let [texts, t0s, t1s, boundingRects, charProbs, logprob, data_hash, translations, alignments, lineTimingOffset] = arr;

    if (boundingRects.length === 1 && boundingRects[0] === null) {
        // The video has soft captions
        if (captionData.caption_top !== undefined && captionData.caption_bottom !== undefined) {
            // But the video also has hard captions that need to be blurred
            // TODO: use caption_left/right if available
            const xMin = captionData.frame_size[1] * 0.2;
            const xMax = captionData.frame_size[1] * 0.8;
            const yMin = captionData.frame_size[0] * captionData.caption_top;
            const yMax = captionData.frame_size[0] * captionData.caption_bottom;
            boundingRects = [[xMin, xMax, yMin, yMax]];
        }
        else {
            boundingRects = [];
        }
    }

    let timingOffset = captionData.timing_offset || 0;
    if (lineTimingOffset !== undefined) {
        timingOffset = lineTimingOffset;
    }

    return {
        texts: texts,
        t0s: t0s,
        t1s: t1s,
        t0: t0s[0],
        t1: t1s[t1s.length-1],
        timingOffset: timingOffset,
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
    // Should match "Henry", but not "TV" or "chair"
    return /^[A-Z][^A-Z]+/.test(tr) && !(tr.startsWith('I') || tr.startsWith("I'"));
}

function hiddenStates(states, wordData) {
    const hidden = getStates(states, wordData, StateHidden, StateNone, StateHidden);
    // Translation is always hidden:
    hidden.translation = true;
    return hidden;
}

function starredStates(states, wordData) {
    const translationState = getState(states, wordDataStateKey(wordData, 'translation'), StateStarred, StateNone)
    const starred = {'words': [], 'translation': translationState === StateStarred};
    for (let i = 0; i < wordData.hz.length; i++) {
        const state = getState(states, wordDataStateKey(wordData, 'word', i), StateStarred, StateNone);
        starred.words.push(state === StateStarred);
    }
    return starred;
}

function getStates(states, wordData, compareTo, defaultValue, defaultValueTranslation) {
    const translationState = getState(states, wordDataStateKey(wordData, 'translation'), compareTo, defaultValueTranslation)
    const statesOut = {'py': [], 'hz': [], 'tr': [], 'translation': translationState === compareTo};
    for (let i = 0; i < wordData.hz.length; i++) {
        for (var type of ['hz', 'py', 'tr']) {
            const state = getState(states, wordDataStateKey(wordData, 'word', i), compareTo, defaultValue);
            statesOut[type].push(state === compareTo);
        }
    }
    return statesOut;
}

function wordDataStateKey(wordData, type, i = null) {
    return getStateKey(
        type,
        i === null ? null : wordData.hz[i],
        i === null ? null : wordData.pys[i],
        i === null ? null : wordData.tr[i],
        wordData.translation
    );
}

function getStateKey(type, hz, pys, tr, translation) {
    let key = null;
    if (pys === null && type === 'word') return null;
    var pysWithoutTonesLower = type === 'word' ? pys.map(py => py.slice(0, -1).toLowerCase()) : null;

    if (type === 'word') {
        if (tr && isName(tr)) {
            // If the translation is capitalized, we want it to be tracked separately
            return `word-${hz}-${pysWithoutTonesLower.join('/')}-name`;
        }
        else {
            return `word-${hz}-${pysWithoutTonesLower.join('/')}`;
        }
    }
    else if (type == 'translation') {
        return `tr-${translation}`;
    }
}

function applyState(DICT, states, type, hz, pys, tr, translation, stateType, stateVal, explicit, syncIndexedDb = false) {
    const keys = [];
    const vals = [];

    let keyType = type;
    if (['py', 'hz', 'tr'].includes(type)) keyType = 'word'; // convert everything but 'translation' to 'word' for keys
    let key = getStateKey(keyType, hz, pys, tr, translation);
    keys.push(key);
    vals.push(setState(states, key, stateType, stateVal, explicit));


    if (type === 'word' && stateType === StateHidden) {
        // Add all the individual char/pys
        for (let startIdx = 0; startIdx < hz.length; startIdx++) {
            for (let endIdx = startIdx+1; endIdx < hz.length+1; endIdx++) {
                if (startIdx === 0 && endIdx === hz.length) continue;

                const hzSub = hz.substring(startIdx, endIdx);
                const pysSub = pys !== null ? pys.slice(startIdx, endIdx) : null;
                if (DICT[hzSub] === undefined) continue;

                key = getStateKey(type, hzSub, pysSub, tr, translation);
                keys.push(key);
                vals.push(setState(
                    states,
                    key,
                    stateType,
                    stateVal,
                    false, // not exlicit
                ));
            }
        }
    }

    if (syncIndexedDb) {
        setIndexedDbData('states', keys, vals, function() {});
    }
}

const StateNone = 0;
const StateHidden = 1;
const StateStarred = 2;

function setState(dict, key, stateType, newState, explicit) {
    let currData = dict[key];
    if (currData === undefined) {
        currData = [0, 0, false]; // Hidden/Star/Explicit vs implicit
    }

    const currExplicit = currData[2];
    if (currExplicit && ! explicit) {
        // Implicit state has no effect on current explicit state
        return currData;
    }
    else if (explicit) {
        // If explicit, we just set it to 0 or 1, no need to count
        currData[stateType-1] = newState === StateNone ? 0 : 1;
        currData[2] = true; // set explicit
    }
    else if (! currExplicit && ! explicit) {
        // Update the implicit count
        let prevState = currData[stateType-1] ? stateType : StateNone;

        if (prevState > 0) {
            currData[prevState-1] -= 1;
        }

        currData[newState-1] += 1;
    }

    dict[key] = currData;
    return currData;
}

function getState(dict, key, stateType, defaultValue) {
    const state = dict[key];
    if (state  === undefined) return defaultValue;
    if (state[stateType-1] > 0) return stateType;
    return StateNone;
}

function truncateTranslationLength(py, hz) {
    // Calculates a max length based on the length of `py` and `hz`
    return Math.max(15, Math.ceil(Math.max(py.length, hz.length) * 2));  // add 100% to longest
}

function getWordData(data, translationIdx, captionIdx) {
    // Create a bit more convenient data structure for the words

    const wordData = {
        hz: [],
        py: [],
        tr: [],
        translation: null,
        pys: [],
        pysDiacritical: [],
        alignmentIndices: [],
        captionIdx: captionIdx,
    };

    if (data === null) {
        return wordData;
    }

    wordData.translation = data.translations[translationIdx];

    let nextIdx = 0;
    const text = data.texts.join(' ');
    wordData.text = text;
    for (let i = 0; i < data.alignments.length; i++) {
        const [startIdx, endIdx, _, pyParts, wordTranslation] = data.alignments[i];
        if (startIdx > nextIdx) {
            wordData.hz.push(text.substring(nextIdx, startIdx));
            wordData.py.push('');
            wordData.tr.push('');
            wordData.pys.push(null);
            wordData.pysDiacritical.push(null);
            wordData.alignmentIndices.push(null);
        }
        const hz = text.substring(startIdx, endIdx);
        wordData.hz.push(hz);
        const pysDiacritical = pyParts.map((part) => part[0]);
        const displayPinyin = pysDiacritical.join('');
        const pys = displayPinyin === '' ? null : pyParts.map((part) => part[1]);
        wordData.py.push(displayPinyin);
        wordData.tr.push(wordTranslation);
        wordData.pysDiacritical.push(pysDiacritical);
        wordData.pys.push(pys);
        wordData.alignmentIndices.push(i);
        nextIdx = endIdx;
    }
    if (nextIdx < text.length) {
        wordData.hz.push(text.substring(nextIdx, text.length));
        wordData.py.push('');
        wordData.tr.push('');
        wordData.pys.push(null);
        wordData.pysDiacritical.push(null);
        wordData.alignmentIndices.push(null);
    }
    return wordData;
}

function videoIdFromCaptionId(captionId) {
    const parts = captionId.split('-');
    return parts.slice(1).join('-');
}

const getYoutubeEmbedCode = (id, t0, t1, autoplay = false, width = 560, height = 315) => `<iframe width="${width}" height="${height}" src="https://www.youtube-nocookie.com/embed/${id}?start=${Math.floor(t0)}&end=${Math.ceil(t1)}&autoplay=${autoplay ? 1 : 0}&rel=0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
function captionToAnkiCloze(wordData, hiddenStates, captionIdx, type, i, captionId = null, captionHash = null, t0 = null, t1 = null, escape = false) {
    let html = `<table id="${captionId} hash="${captionHash} idx="${captionIdx}" type="${type}" i="${i}">\n`;
    let nextClozeIdx = 0;
    for (const rowType of ['py', 'hz', 'tr']) {
        let row = '\t<tr>\n';
        for (let j = 0; j < wordData[rowType].length; j++) {
            let data = wordData[rowType][j];

            if (i == j) {
                if (type === 'py') {
                    if (rowType === 'py' || rowType === 'hz') {
                        row += '\t\t<td>{{c1::' + data + '}}</td>\n';
                    }
                    else {
                        row += '\t\t<td>' + data + '</td>\n';
                    }
                }
                else if (type === 'hz') {
                    if (rowType === 'hz') {
                        row += '\t\t<td>' + data + '</td>\n';
                    }
                    else if (rowType === 'py') {
                        row += '\t\t<td>{{c1::' + data + '}}</td>\n';
                    }
                    else if (rowType === 'tr') {
                        row += '\t\t<td>{{c1::' + data + '}}</td>\n';
                    }
                }
                else if (type === 'tr') {
                    if (rowType === 'tr') {
                        row += '\t\t<td>{{c1::' + data + '}}</td>\n';
                    }
                    else {
                        row += '\t\t<td>' + data + '</td>\n';
                    }
                }
            }
            else {
                let visibilityStr = 'style="visibility: hidden"';
                if (type === 'py') visibilityStr = '';

                let title = null;
                if (rowType === 'tr') {
                    const truncateLength = truncateTranslationLength(wordData.py[j], wordData.hz[j]);
                    const doTruncate = data.length > truncateLength;
                    title = data;
                    data = data.slice(0, truncateLength) + (doTruncate ? '...' : '');
                }
                if (rowType !== 'hz' && hiddenStates[rowType][j]) {
                    data = '<span style="display: none">' + data + '</span>';
                }
                if (title !== null) {
                    row += `\t\t<td ${visibilityStr} title="${title}">` + data + '</td>\n';
                }
                else {
                    row += `\t\t<td ${visibilityStr} >` + data + '</td>\n';
                }
            }
        }
        row += '\t</tr>\n';
        html += row;
    }
    html += '</table>';
    if (type !== 'py') {
        html += `<br><button onClick="document.querySelectorAll('td').forEach((el) => el.style.visibility = 'visible')">Show context</button>`;
    }
    html += `<br><hr><br><div>{{c1::${wordData.translation}}}</div>`;
    if (captionId !== null) {
        const parts = captionId.split('-');
        const id = parts.slice(1).join('-');
        const embedding = getYoutubeEmbedCode(id, t0, t1, true);
        html += `<br><hr><button onClick="addEmbedding(event)">Play</button>`;
        html += '<script>';
        html += 'function addEmbedding(event) {';
        html += `event.target.outerHTML = '${embedding}'`;
        html += '}';
        html += '</script>';
    }

    if (escape) {
        html = html.replaceAll(/\n/g, '');
        html = html.replaceAll(/\t/g, '');
    }
    return html;
}

function updateClipboard(newClip, $q = null, message = null) {
    navigator.clipboard.writeText(newClip).then(function() {
    }, function() {
        console.log('Clipboard failed');
    });

    if ($q && message) {
        $q.notify({
            type: 'positive',
            message: message
        });
    }
}

function download(filename, text) {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
}

function getShowSeasonEpisode(showInfo, captionId) {
    let showName = null;
    if (showInfo) {
        showName = showInfo.name;
        let [seasonIdx, episodeIdx] = findVideoInShowInfo(showInfo, captionId);
        if (seasonIdx !== null) {
            const seasonName = getSeasonName(showInfo, seasonIdx);
            const episodeName = getEpisodeName(showInfo, seasonIdx, episodeIdx);
            return [showName, seasonIdx, seasonName, episodeIdx, episodeName];
        }
    }

    return [showName, null, null, null, null];
}

function getSeasonName(showInfo, seasonIdx) {
    const season = showInfo.seasons[seasonIdx];
    const number = season.number;
    if (! [null, undefined].includes(number)) { // if explicit number is available, use that
        seasonIdx = number - 1;
    }
    seasonName = season.name;
    if (! seasonName) {
        seasonName = `S${pad(seasonIdx + 1, 2)}`;
    }

    return seasonName;
}

function getEpisodeName(showInfo, seasonIdx, episodeIdx) {
    const season = showInfo.seasons[seasonIdx];
    episodeName = season.episodes[episodeIdx].name;
    if (! episodeName) {
        episodeName = `E${pad(episodeIdx + 1, 2)}`;
    }

    return episodeName;
}

function resolveShowName(showName) {
    if (showName === null) {
        return null;
    }
    else if (typeof showName === "object") {
        return showName.hz;
    }
    else {
        return showName;
    }
}

function pad(num, size) {
    num = num.toString();
    while (num.length < size) num = "0" + num;
    return num;
}

function srtTimestamp(t) {
    const hours = parseInt(t / (60*60));
    t -= hours * 60 * 60;
    const minutes = parseInt(t / 60);
    t -= minutes * 60;
    const seconds = t;
    let secondsString = seconds.toFixed(3);
    if (seconds < 10) secondsString = '0' + secondsString;
    return `${pad(hours, 2)}:${pad(minutes, 2)}:${secondsString}`.replace('.', ',');
}

function youtubeThumbnailURL(captionId) {
    const videoId = videoIdFromCaptionId(captionId);
    return `https://i.ytimg.com/vi/${videoId}/0.jpg`;
}

function syncPersonalDatabase(uploadURL, data, callback) {
    fetch(url, {method: "PUT", body: data}).then(function() {
        callback();
    }).catch((error) => {
        callback(error);
    });
}

function login(username, password, callback) {
    fetch('/auth/jwt/login', {
        method: 'POST',
        headers:{
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            'username': username,
            'password': password
        })
    }).then(function(res) {
        return res.json();
    }).then((res) => {
        if (res.detail) callback(null, res);
        else callback(res, null)
    }).catch((error) => {
        callback(null, error);
    });
}

function register(username, password, callback) {
    fetch('/auth/register', {
        method: 'POST',
        headers:{
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'email': username,
            'password': password
        })
    }).then(function(res) {
        if (res.ok) callback();
        else return res.json();
    }).then((error) => {
        if (error) callback(error);
    }).catch((error) => {
        callback(error);
    });
}

function getSignedUploadLink(accessToken, callback) {
    fetch('/signed-upload-link', {
        method: 'GET',
        headers: new Headers({
            'Authorization': 'Bearer ' + accessToken,
            'Content-Type': 'application/x-www-form-urlencoded'
        }),
    }).then(function(res) {
        return res.json();
    }).then((res) => {
        callback(res)
    }).catch((error) => {
        callback(error);
    });
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
    'study': '<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 122.88 101.37"><path d="M12.64,77.27l0.31-54.92h-6.2v69.88c8.52-2.2,17.07-3.6,25.68-3.66c7.95-0.05,15.9,1.06,23.87,3.76 c-4.95-4.01-10.47-6.96-16.36-8.88c-7.42-2.42-15.44-3.22-23.66-2.52c-1.86,0.15-3.48-1.23-3.64-3.08 C12.62,77.65,12.62,77.46,12.64,77.27L12.64,77.27z M103.62,19.48c-0.02-0.16-0.04-0.33-0.04-0.51c0-0.17,0.01-0.34,0.04-0.51V7.34 c-7.8-0.74-15.84,0.12-22.86,2.78c-6.56,2.49-12.22,6.58-15.9,12.44V85.9c5.72-3.82,11.57-6.96,17.58-9.1 c6.85-2.44,13.89-3.6,21.18-3.02V19.48L103.62,19.48z M110.37,15.6h9.14c1.86,0,3.37,1.51,3.37,3.37v77.66 c0,1.86-1.51,3.37-3.37,3.37c-0.38,0-0.75-0.06-1.09-0.18c-9.4-2.69-18.74-4.48-27.99-4.54c-9.02-0.06-18.03,1.53-27.08,5.52 c-0.56,0.37-1.23,0.57-1.92,0.56c-0.68,0.01-1.35-0.19-1.92-0.56c-9.04-4-18.06-5.58-27.08-5.52c-9.25,0.06-18.58,1.85-27.99,4.54 c-0.34,0.12-0.71,0.18-1.09,0.18C1.51,100.01,0,98.5,0,96.64V18.97c0-1.86,1.51-3.37,3.37-3.37h9.61l0.06-11.26 c0.01-1.62,1.15-2.96,2.68-3.28l0,0c8.87-1.85,19.65-1.39,29.1,2.23c6.53,2.5,12.46,6.49,16.79,12.25 c4.37-5.37,10.21-9.23,16.78-11.72c8.98-3.41,19.34-4.23,29.09-2.8c1.68,0.24,2.88,1.69,2.88,3.33h0V15.6L110.37,15.6z M68.13,91.82c7.45-2.34,14.89-3.3,22.33-3.26c8.61,0.05,17.16,1.46,25.68,3.66V22.35h-5.77v55.22c0,1.86-1.51,3.37-3.37,3.37 c-0.27,0-0.53-0.03-0.78-0.09c-7.38-1.16-14.53-0.2-21.51,2.29C79.09,85.15,73.57,88.15,68.13,91.82L68.13,91.82z M58.12,85.25 V22.46c-3.53-6.23-9.24-10.4-15.69-12.87c-7.31-2.8-15.52-3.43-22.68-2.41l-0.38,66.81c7.81-0.28,15.45,0.71,22.64,3.06 C47.73,78.91,53.15,81.64,58.12,85.25L58.12,85.25z" fill="currentColor" stroke-width="2" stroke="${color}" /></svg>',
    'dictionary': '<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 122.88 96.44"><path d="M12,73.51q.2-34.74.39-69.38A3.21,3.21,0,0,1,15,1h0C23.4-.75,36.64-.31,45.63,3.14a35.46,35.46,0,0,1,16,11.65,37.34,37.34,0,0,1,16-11.15C86.12.4,99-.38,108.23,1A3.2,3.2,0,0,1,111,4.14h0V73.8A3.21,3.21,0,0,1,107.77,77a3.49,3.49,0,0,1-.74-.09A53.45,53.45,0,0,0,83.58,79.1a71,71,0,0,0-15.77,8.26,69.09,69.09,0,0,1,21.24-3.1,125.42,125.42,0,0,1,27.41,3.48V14.84h3.21a3.21,3.21,0,0,1,3.21,3.21V91.94a3.21,3.21,0,0,1-3.21,3.21,3.18,3.18,0,0,1-1-.17A121.77,121.77,0,0,0,89,90.65a61.89,61.89,0,0,0-25.76,5.26,3.39,3.39,0,0,1-3.64,0,61.86,61.86,0,0,0-25.76-5.26A121.77,121.77,0,0,0,4.24,95a3.18,3.18,0,0,1-1,.17A3.21,3.21,0,0,1,0,91.94V18.05a3.21,3.21,0,0,1,3.21-3.21H6.42v72.9a125.42,125.42,0,0,1,27.41-3.48,68.84,68.84,0,0,1,22.71,3.57A48.7,48.7,0,0,0,41,79.39c-7-2.3-17.68-3.07-25.49-2.4A3.21,3.21,0,0,1,12,74.06a5,5,0,0,1,0-.55ZM73.64,64.4a2.3,2.3,0,1,1-2.5-3.85,51.46,51.46,0,0,1,11.8-5.4,53.73,53.73,0,0,1,13-2.67,2.29,2.29,0,1,1,.25,4.58,49.42,49.42,0,0,0-11.79,2.46A46.73,46.73,0,0,0,73.64,64.4Zm.2-17.76a2.29,2.29,0,0,1-2.46-3.87,52.71,52.71,0,0,1,11.74-5.3A54.12,54.12,0,0,1,95.9,34.85a2.3,2.3,0,0,1,.25,4.59,49.3,49.3,0,0,0-11.63,2.4,48,48,0,0,0-10.68,4.8Zm.06-17.7a2.3,2.3,0,1,1-2.46-3.89,52.54,52.54,0,0,1,11.72-5.27,53.71,53.71,0,0,1,12.74-2.6,2.29,2.29,0,1,1,.25,4.58,49.35,49.35,0,0,0-11.59,2.39A47.91,47.91,0,0,0,73.9,28.94ZM51.74,60.55a2.3,2.3,0,1,1-2.5,3.85,46.73,46.73,0,0,0-10.72-4.88,49.42,49.42,0,0,0-11.79-2.46A2.29,2.29,0,1,1,27,52.48a53.73,53.73,0,0,1,13,2.67,51.46,51.46,0,0,1,11.8,5.4ZM51.5,42.77A2.29,2.29,0,0,1,49,46.64a48,48,0,0,0-10.68-4.8,49.3,49.3,0,0,0-11.63-2.4A2.3,2.3,0,0,1,27,34.85a54.12,54.12,0,0,1,12.78,2.62,52.71,52.71,0,0,1,11.74,5.3Zm-.06-17.72A2.3,2.3,0,1,1,49,28.94a47.91,47.91,0,0,0-10.66-4.79,49.35,49.35,0,0,0-11.59-2.39A2.29,2.29,0,1,1,27,17.18a53.71,53.71,0,0,1,12.74,2.6,52.54,52.54,0,0,1,11.72,5.27ZM104.56,7c-7.42-.7-18.06.12-24.73,2.65A30,30,0,0,0,64.7,21.46V81.72a76.76,76.76,0,0,1,16.72-8.66,62.85,62.85,0,0,1,23.14-2.87V7ZM58.28,81.1V21.37c-3.36-5.93-8.79-9.89-14.93-12.24-7-2.67-17.75-3.27-24.56-2.3l-.36,63.56c7.43-.27,17.69.68,24.52,2.91a54.94,54.94,0,0,1,15.33,7.8Z" fill="currentColor" stroke-width="1" stroke="${color}" /></svg>',
    'pin': '<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 100 100"><path d="M85.4 45L54.9 14.6c-2.8-2.9-3.5-1.1-3.5.3v14L28.7 45.7H15c-3.9 0-.8 4.2-1.4 3.5l17.2 17.1-14.4 14.5c-.8.8-.8 2.1 0 2.9.8.8 2.1.8 2.9 0l14.4-14.4 17.1 17.2c-.5-.5 3.6 2.2 3.6-1.4V71.3l16.8-22.7h12.7c2.1-.1 4.9-.1 1.5-3.6zm-65.5 4.6h8.9l21.7 21.7v8.9L19.9 49.6zm32.5 17.7L32.7 47.6 52.8 33l14.4 14.6-14.8 19.7zm17.8-22.7L55.4 29.8v-8.9l23.7 23.7h-8.9z" fill="currentColor" stroke-width="4" stroke="${color}" /><path fill="currentColor" stroke-width="4" stroke="${color}" d="M804-1070V614H-980v-1684H804m8-8H-988V622H812v-1700z"/></svg>',
    'unpin': '<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 100 100"><path d="M85.4 45L54.9 14.6c-2.8-2.9-3.5-1.1-3.5.3v14L28.7 45.7H15c-3.9 0-.8 4.2-1.4 3.5l17.2 17.1-14.4 14.5c-.8.8-.8 2.1 0 2.9.8.8 2.1.8 2.9 0l14.4-14.4 17.1 17.2c-.5-.5 3.6 2.2 3.6-1.4V71.3l16.8-22.7h12.7c2.1-.1 4.9-.1 1.5-3.6zm-65.5 4.6h8.9l21.7 21.7v8.9L19.9 49.6zm32.5 17.7L32.7 47.6 52.8 33l14.4 14.6-14.8 19.7zm17.8-22.7L55.4 29.8v-8.9l23.7 23.7h-8.9z" fill="currentColor" stroke-width="4" stroke="${color}" /><path fill="currentColor" stroke-width="4" stroke="${color}" d="M804-1070V614H-980v-1684H804m8-8H-988V622H812v-1700z"/><line x1="10" y1="10" x2="90" y2="90" style="stroke-width: 4; stroke: ${color};" /></svg>',
    'pen': '<svg viewBox="0 0 24 24" width="${width}" height="${height}" fill="none" xmlns="http://www.w3.org/2000/svg" ><path fill-rule="evenodd" clip-rule="evenodd" d="M21.2635 2.29289C20.873 1.90237 20.2398 1.90237 19.8493 2.29289L18.9769 3.16525C17.8618 2.63254 16.4857 2.82801 15.5621 3.75165L4.95549 14.3582L10.6123 20.0151L21.2189 9.4085C22.1426 8.48486 22.338 7.1088 21.8053 5.99367L22.6777 5.12132C23.0682 4.7308 23.0682 4.09763 22.6777 3.70711L21.2635 2.29289ZM16.9955 10.8035L10.6123 17.1867L7.78392 14.3582L14.1671 7.9751L16.9955 10.8035ZM18.8138 8.98525L19.8047 7.99429C20.1953 7.60376 20.1953 6.9706 19.8047 6.58007L18.3905 5.16586C18 4.77534 17.3668 4.77534 16.9763 5.16586L15.9853 6.15683L18.8138 8.98525Z" fill="currentColor" /> <path d="M2 22.9502L4.12171 15.1717L9.77817 20.8289L2 22.9502Z" fill="currentColor" /></svg>',
    'hide': '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="${width}" height="${height}" viewBox="0 0 572.098 572.098"> <g> <path fill="currentColor" d="M99.187,398.999l44.333-44.332c-24.89-15.037-47.503-33.984-66.763-56.379c29.187-33.941,66.053-60.018,106.947-76.426 c-6.279,14.002-9.853,29.486-9.853,45.827c0,16.597,3.696,32.3,10.165,46.476l35.802-35.797 c-5.698-5.594-9.248-13.36-9.248-21.977c0-17.02,13.801-30.82,30.82-30.82c8.611,0,16.383,3.55,21.971,9.248l32.534-32.534 l36.635-36.628l18.366-18.373c-21.206-4.186-42.896-6.469-64.848-6.469c-107.663,0-209.732,52.155-273.038,139.518L0,298.288 l13.011,17.957C36.83,349.116,66.151,376.999,99.187,398.999z"/> <path fill="currentColor" d="M459.208,188.998l-44.854,44.854c30.539,16.071,58.115,37.846,80.986,64.437 c-52.167,60.662-128.826,96.273-209.292,96.273c-10.3,0-20.533-0.6-30.661-1.744l-52.375,52.375 c26.903,6.887,54.762,10.57,83.036,10.57c107.663,0,209.738-52.154,273.038-139.523l13.011-17.957l-13.011-17.956 C532.023,242.995,497.844,212.15,459.208,188.998z"/> <path fill="currentColor" d="M286.049,379.888c61.965,0,112.198-50.234,112.198-112.199c0-5.588-0.545-11.035-1.335-16.402L269.647,378.56 C275.015,379.349,280.461,379.888,286.049,379.888z"/> <path fill="currentColor" d="M248.815,373.431L391.79,230.455l4.994-4.994l45.796-45.796l86.764-86.77c13.543-13.543,13.543-35.502,0-49.046 c-6.77-6.769-15.649-10.159-24.523-10.159s-17.754,3.384-24.522,10.159l-108.33,108.336l-22.772,22.772l-29.248,29.248 l-48.14,48.14l-34.456,34.456l-44.027,44.027l-33.115,33.115l-45.056,45.055l-70.208,70.203 c-13.543,13.543-13.543,35.502,0,49.045c6.769,6.77,15.649,10.16,24.523,10.16s17.754-3.385,24.523-10.16l88.899-88.898 l50.086-50.086L248.815,373.431z"/> </g></svg>',
    'copy': '<svg width="${width}" height="${height}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" > <path fill-rule="evenodd" clip-rule="evenodd" d="M3 19V1H17V5H21V23H7V19H3ZM15 17V3H5V17H15ZM17 7V19H9V21H19V7H17Z" fill="currentColor" /> </svg>',
    'star': '<svg version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="${width}" height="${height}" viewBox="0 0 314.335 314.336" style="enable-background:new 0 0 314.335 314.336;" xml:space="preserve"> <g> <path stroke="${color}" fill="${color}" d="M302.593,117.321h-80.698c-13.583,0-27.994-10.472-32.191-23.398l-24.944-76.744c-4.197-12.925-10.997-12.925-15.198,0 l-24.941,76.744c-4.2,12.926-18.612,23.398-32.195,23.398H11.74c-13.583,0-15.688,6.473-4.699,14.462l65.284,47.426 c10.989,7.986,16.498,24.932,12.298,37.854l-24.941,76.741c-4.2,12.922,1.309,16.922,12.298,8.93l65.291-47.427 c10.988-7.986,28.805-7.986,39.794,0l65.29,47.427c10.988,7.992,16.501,3.98,12.298-8.93l-24.938-76.741 c-4.197-12.923,1.31-29.868,12.298-37.854l65.284-47.426C318.285,123.794,316.176,117.321,302.593,117.321z"/></g></svg>',
    'hollowstar': '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="${width}" height="${height}" viewBox="0 0 512 512" style="enable-background:new 0 0 512 512;" xml:space="preserve"><g><path stroke="${color}" fill="${color}" d="M511.177,197.119c-1.975-6.079-7.23-10.51-13.554-11.429l-156.54-22.758L271.059,21.066 c-2.829-5.731-8.667-9.359-15.059-9.359c-6.391,0-12.23,3.628-15.059,9.359l-70.024,141.866L14.377,185.689 c-6.324,0.919-11.58,5.35-13.554,11.429c-1.976,6.079-0.328,12.753,4.25,17.214L118.338,324.74L91.619,480.664 c-1.08,6.3,1.51,12.665,6.681,16.422c5.17,3.756,12.024,4.252,17.683,1.279l140.016-73.593l140.014,73.593 c5.688,2.99,12.54,2.457,17.683-1.279c5.171-3.756,7.762-10.123,6.681-16.422L393.66,324.741l113.267-110.409 C511.505,209.87,513.153,203.196,511.177,197.119z M363.897,306.851c-3.958,3.857-5.763,9.414-4.83,14.861l22.463,131.097 l-117.718-61.875c-4.89-2.572-10.735-2.573-15.625,0l-117.719,61.875l22.463-131.097c0.934-5.446-0.872-11.004-4.83-14.861 L52.878,214.03l131.607-19.133c5.469-0.795,10.195-4.23,12.643-9.185L256,66.439l58.872,119.274 c2.447,4.955,7.174,8.39,12.643,9.185l131.607,19.133L363.897,306.851z"/></g></svg>',
    'switch': '<svg width="${width}" height="${height}" viewBox="3 3 18 18" fill="none" xmlns="http://www.w3.org/2000/svg" ><path d="M16 13V11.5H10V9.5H16V8L19 10.5L16 13Z" fill="currentColor" /><path d="M8 17V15.5H14V13.5H8V12L5 14.5L8 17Z" fill="currentColor" /></svg>',
}

function getIconSvg(name, size, color = "white") {
    if (ICON_SVG[name] === undefined) {
        console.log('No icon named', name);
    }
    return ICON_SVG[name].replaceAll('${width}', size).replaceAll('${height}', size).replaceAll('${color}', color);
}

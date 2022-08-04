const DEFAULT_FONT_SIZE = 24;
const DEFAULT_SHORTCUTS = {
    next: 'ArrowRight',
    prev: 'ArrowLeft',
    replay: 'KeyR',
    dictionary: 'KeyD',
    peek: 'KeyP',
    peekFullTr: 'KeyT',
    peekPy: 'KeyY',
    peekHz: 'KeyH',
    peekTr: 'KeyN',
    pausePlay: 'Space', // already a shortcut, but is applied outside the video in Web
}


function syncOptions(state) {
    setIndexedDbData('other', ['options'], [state.options], function() {});
}

function getShowInfo(store, state = null) {
    if (state === null) state = store.state;
    if ([null, undefined].includes(state.captionData) || [null, undefined].includes(state.showList)) return null;

    return state.showList[state.captionData.show_name];
}

const store = new Vuex.Store({
    state: {
        captionId: null,
        videoId: null,
        AVElement: null,
        videoAPI: null,
        videoDuration: null,
        sessionTime: null,
        captionData: null,
        captionHash: null, // use this for event log. Equals 'fetching' if in the process of fetching
        fetchedCaptionId: null,
        resourceFetchErrors: [],
        youtubeAPIReady: false,
        showList: null,
        thumbnailObserver: null,
        videoList: null,
        DICT: null,
        HSK_WORDS: null,
        SIMPLE_CHARS: null,
        states: Vue.ref({}),
        captionFontScale: 0.5,
        captionFontSize: 24,
        captionOffset: [0, 0],
        isMovingCaption: false,
        peekStates: Vue.ref({
            py: [],
            hz: [],
            tr: [],
            rows: {
                py: false,
                tr: false,
                hz: false,
                translation: false,
            }
        }),
        autoPeekStates: Vue.ref({
            py: [],
            hz: [],
            tr: [],
            rows: {
                py: false,
                tr: false,
                hz: false,
                translation: false,
            }
        }),
        showOptions: false,
        optionsHighlightSection: null,
        showDictionary: false,
        showDictionaryRange: [-1, -1],
        timingOffset: 0,
        webPage: 'videos',
        watchingShowInfo: null,
        watchingSeason: null,
        watchingEpisode: null,
        options: Vue.ref({
            extensionToggle: true,
            autoPause: false,
            WPSThreshold: 2.0,
            characterSet: 'sm',
            blurCaptions: true,
            pin: {
                hz: false,
                py: false,
                tr: false,
                translation: false,
            },
            pinLevels: {
                hz: 0,
                py: 0,
                tr: 0,
                translation: 0,
            },
            displayTranslation: 0, // index into [human, machine][min(idx, length)]
            hideWordsLevel: 0,
            peekAfterAutoHide: true,
            keyboardShortcutsToggle: true,
            keyboardShortcuts: DEFAULT_SHORTCUTS,
            anki: {
                advancedCards: [
                    "Cloze word hanzi + pinyin",
                    "Cloze word translation",
                    "Cloze whole word",
                    "Basic produce Chinese",
                    "Basic produce translation",
                    "Basic produce Hanzi",
                ],
                advancedToggled: [
                    false,
                    false,
                    false,
                    false,
                    false,
                    false,
                ],
                basicToggled: [
                    false,
                    false,
                    false,
                ],
                clozeIncludeHint: false,
            },
        }),
    },
    mutations: {
        setWebPage(state, page) {
            state.webPage = page;
        },
        setWatchingShowInfo(state, showInfo) {
            state.watchingShowInfo = showInfo;
        },
        setWatchingSeason(state, season) {
            state.watchingSeason = season;
        },
        setWatchingEpisode(state, episode) {
            state.watchingEpisode = episode;
        },
        setVideoAPI(state, api) {
            state.videoAPI = api;
        },
        setAVElement(state, el) {
            state.AVElement = el;
        },
        setVideoDuration(state, duration) {
            state.videoDuration = duration;
        },
        setYoutubeAPIReady(state) {
            state.youtubeAPIReady = true;
        },
        switchTranslation(state) {
            state.options.displayTranslation = (state.options.displayTranslation + 1) % 2;
        },
        setOptionsHighlightSection(state, val) {
            state.optionsHighlightSection = val;
        },
        setVideoId(state, val) {
            state.videoId = val
        },
        setVideoList(state, val) {
            state.videoList = new Set(val);
            if (BROWSER_EXTENSION) {
                const newThumbnailObserver = initializeThumbnailBadges(state.videoList);
                if (state.thumbnailObserver) state.thumbnailObserver.disconnect();
                state.thumbnailObserver = newThumbnailObserver;
            }
        },
        setShowList(state, val) {
            state.showList = val;
        },
        setSimpleCharsList(state, val) {
            state.SIMPLE_CHARS = val;
        },
        resetResourceFetchError(state, val) {
            // We only reset it if the currente error holds this resource type
            // (not some other resource)
            if (state.resourceFetchErrors.includes(val)) {
                state.resourceFetchErrors.splice(state.resourceFetchErrors.indexOf(val), 1);
            }
        },
        setResourceFetchError(state, val) {
            state.resourceFetchErrors.push(val);
        },
        setIsMovingCaption(state, val) {
            state.isMovingCaption = val;
        },
        setTimingOffset(state, val) {
            state.timingOffset = val;
        },
        setCaptionId(state, val) {
            state.captionId = val;
            state.sessionTime = Date.now();
            if ([null, undefined].includes(val)) return;
        },
        setCaptionIdDataHash(state, val) {
            state.captionData = val.data;
            state.captionHash = val.hash;
            state.fetchedCaptionId = val.id;
        },
        setShowOptions(state, val) {
            state.showOptions = val;
        },
        setShowDictionary(state, val) {
            if (! [null, undefined].includes(val.val)) state.showDictionary = val.val;
            if (val.range) {
                state.showDictionaryRange = val.range;
                if (val.range[0] >= 0) {
                    appendSessionLog(
                        state,
                        [eventsMap['EVENT_SHOW_DICTIONARY_RANGE'], val.range[0], val.range[1]]
                    );
                }
            }
        },
        setStates(state, states) {
            state.states = states;
        },
        increaseCaptionFontScale(state) {
            state.captionFontScale = Math.min(state.captionFontScale + 0.1, 1.0);
            state.captionFontSize = Math.round(2 * DEFAULT_FONT_SIZE * state.captionFontScale);
        },
        decreaseCaptionFontScale(state) {
            state.captionFontScale = Math.max(state.captionFontScale - 0.1, 0.3);
            state.captionFontSize = Math.round(2 * DEFAULT_FONT_SIZE * state.captionFontScale);
        },
        setCaptionOffset(state, offset) {
            state.captionOffset = offset;
        },
        setPeekState(state, val) {
            const states = val.auto ? state.autoPeekStates : state.peekStates;
            if ([undefined, null].includes(val.i)) {
                if (val.type === 'translation') {
                    states[val.type] = true;
                    states.rows[val.type] = true;
                }
                else {
                    states.rows[val.type] = true;
                    // Set peek state for all words
                    for (let i = 0; i < states[val.type].length; i++) {
                        states[val.type][i] = true;
                    }
                }
            }
            else {
                states[val.type][val.i] = true;
            }
        },
        resetPeekStates(state, val) {
            state.peekStates = {
                py: [],
                hz: [],
                tr: [],
                translation: false,
                rows: {
                    hz: false,
                    tr: false,
                    py: false,
                    translation: false,
                },
            };
            for (let i = 0; i < val; i++) {
                for (const type of ['py', 'hz', 'tr']) {
                    state.peekStates[type].push(false);
                }
            }
            state.autoPeekStates = JSON.parse(JSON.stringify(state.peekStates));
        },
        setPeekStates(state, val) {
            state.peekStates = val;
        },
        setBlur(state, val) {
            state.options.blurCaptions = val;
            syncOptions(state);
            appendSessionLog(state, [eventsMap['EVENT_BLUR'], val]);
        },
        setOptions(state, options) {
            state.options = options;
            syncOptions(state);
        },
        setOption(state, option) {
            state.options[option.key] = option.value;
            syncOptions(state);
        },
        setDeepOption(state, option) {
            state.options[option.key][option.key2] = option.value;
            syncOptions(state);
        },
        setDict(state, dict) {
            state.DICT = dict;
        },
        setHskWords(state, words) {
            state.HSK_WORDS = words;
        },
        setAnkiAdvancedCards(state, val) {
            state.options.anki.advancedCards = val;
            syncOptions(state);
        },
        setAnkiCardsAdvancedToggled(state, val) {
            state.options.anki.advancedToggled = val;
            syncOptions(state);
        },
        setAnkiCardsBasicToggled(state, val) {
            state.options.anki.basicToggled = val;
            syncOptions(state);
        },
        setAnkiCardsClozeIncludeHint(state, val) {
            state.options.anki.clozeIncludeHint = val;
            syncOptions(state);
        },
    },
});

if (BROWSER_EXTENSION) {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === 'extensionToggle') {
            // Reset captionOffset so we have a way get out of the situation where it's outside the window
            store.commit('setCaptionOffset', [0, 0]);
            store.commit('setOption', {key: 'extensionToggle', value: message.data});
        }
        return true;
    });
}

const FETCH_PUBLIC_RESOURCES = [
    ['public_cedict.json', 'dictionary', 'setDict'],
    ['hsk_words.json', 'HSK word list', 'setHskWords'],
    ['video_list.json', 'video list', 'setVideoList'],
    ['show_list_full.json', 'show list', 'setShowList'],
    ['simple_chars.json', 'simple chars list', 'setSimpleCharsList'],
];

function fetchInitialResources() {
    for (const [filename, errorName, mutation] of FETCH_PUBLIC_RESOURCES) {
        fetchVersionedResource(filename, function (data) {
            if (data === 'error') {
                store.commit('setResourceFetchError', errorName);
            }
            else {
                store.commit('resetResourceFetchError', errorName);
                store.commit(mutation, data);
            }
        });
    }

    fetchPersonalDataToStore(store);
}

if (BROWSER_EXTENSION) {
    // We have to wait for the iframe to load before we can fetch stuff from it
    lazybugIframe.addEventListener('load', fetchInitialResources);
}
else {
    fetchInitialResources();
}

function addBadge($img, videoList) {
    if ($img === null) return;
    const $a = $img.closest("#thumbnail");
    const youtubeIdRegex = /^.*\?v\=([a-zA-Z0-9_-]*)&?.*/;
    const match = youtubeIdRegex.exec($a.href);
    if (!match) return;

    const id = match[1];
    if (! videoList.has(`youtube-${id}`)) {
        return;
    }

    $img.style.position = 'relative';
    const badge = document.createElement('img');
    badge.classList.add('lazybugbadge');
    badge.src = CDN_URL + 'lazybug-public/images/64_lazybug.png';
    badge.style.filter = 'drop-shadow(5px 5px 5px black)';
    badge.style.width = badge.style.height = '28px';
    badge.style.position = 'absolute';
    badge.style.top = '4px';
    badge.style.left = '4px';
    $img.parentNode.appendChild(badge);
}

function initializeThumbnailBadges(videoList) {
    for (const $img of document.querySelectorAll('#thumbnail img:not(.lazybugbadge)')) {
        addBadge($img, videoList);
    }

    return new MutationObserver((mutations) => {
        let hasNewThumbnails = false;
        for (let mutation of mutations) {
            switch(mutation.type) {
                case 'childList':
                    for (let node of mutation.addedNodes) {
                        if (node.nodeType !== 1) continue;
                        if (node.tagName === 'IMG' && !node.classList.contains('lazybugbadge') && node.closest('#thumbnail')) {
                            addBadge(node, videoList);
                        }
                        else if (node.id === 'thumbnail') {
                            addBadge(node.querySelector('img:not(.lazybugbadge)'), videoList);
                        }
                    }
                    break;
                case 'attributes':
                    if (mutation.target.id === 'thumbnail' && mutation.attributeName === 'href' && mutation.oldValue !== null) {
                        const $img = mutation.target.querySelector('img:not(.lazybugbadge)');
                        for (const $badgeImg of mutation.target.querySelectorAll('img.lazybugbadge')) {
                            $badgeImg.remove();
                        }
                        addBadge($img, videoList);
                    }
                    break;
            }
        }
    }).observe(document, {subtree: true, childList: true, attributes: true, attributeOldValue: true});
}

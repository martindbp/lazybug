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
}


function syncOptions(state) {
    setIndexedDbData('other', ['options'], [state.options], function() {});
}

const store = new Vuex.Store({
    state: {
        captionId: null,
        videoId: null,
        sessionTime: null,
        captionData: null,
        captionHash: null, // use this for event log
        resourceFetchError: null,
        showList: null,
        showInfo: null,
        videoList: null,
        DICT: null,
        HSK_WORDS: null,
        states: Vue.ref({}),
        captionFontScale: 0.5,
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
        showOptions: false,
        showDictionary: false,
        showDictionaryRange: [-1, -1],
        timingOffset: 0,
        options: Vue.ref({
            extensionToggle: true,
            autoPause: false,
            characterSet: 'sm',
            blurCaptions: true,
            pin: {
                hz: false,
                py: false,
                tr: false,
                translation: false,
            },
            displayTranslation: 0, // index into [human, machine][min(idx, length)]
            hideLevels: {
                py: 0,
                hz: 0,
                tr: 0,
            },
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
        setVideoId(state, val) {
            state.videoId = val
        },
        setVideoList(state, val) {
            state.videoList = val;
        },
        setShowList(state, val) {
            state.showList = val;
        },
        resetResourceFetchError(state, val) {
            // We only reset it if the currente error holds this resource type
            // (not some other resource)
            if (state.resourceFetchError === val) {
                state.resourceFetchError = null;
            }
        },
        setResourceFetchError(state, val) {
            state.resourceFetchError = val;
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
        setCaptionDataAndHash(state, val) {
            state.captionData = val.data;
            state.captionHash = val.hash;
            if (state.captionData !== null) {
                if (state.resourceFetchError === 'show info') {
                    state.resourceFetchError = null;
                }
                fetchResource(`shows/${state.captionData.show_name}.json`, function (data) {
                    if (data === 'error') {
                        state.resourceFetchError = 'show info';
                    }
                    else {
                        state.showInfo = data;
                    }
                });
            }
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
        },
        decreaseCaptionFontScale(state) {
            state.captionFontScale = Math.max(state.captionFontScale - 0.1, 0.3);
        },
        setCaptionOffset(state, offset) {
            state.captionOffset = offset;
        },
        setPeekState(state, val) {
            if ([undefined, null].includes(val.i)) {
                if (val.type === 'translation') {
                    state.peekStates[val.type] = true;
                    state.peekStates.rows[val.type] = true;
                }
                else {
                    state.peekStates.rows[val.type] = true;
                    // Set peek state for all words
                    for (let i = 0; i < state.peekStates[val.type].length; i++) {
                        state.peekStates[val.type][i] = true;
                    }
                }
            }
            else {
                state.peekStates[val.type][val.i] = true;
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

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'extensionToggle') {
        // Reset captionOffset so we have a way get out of the situation where it's outside the window
        store.commit('setCaptionOffset', [0, 0]);
        store.commit('setOption', {key: 'extensionToggle', value: message.data});
    }
    return true;
});

const FETCH_PUBLIC_RESOURCES = [
    ['public_cedict.json', 'dictionary', 'setDict'],
    ['hsk_words.json', 'HSK word list', 'setHskWords'],
    ['video_list.json', 'video list', 'setVideoList'],
    ['show_list.json', 'show list', 'setShowList'],
];

store.commit('resetResourceFetchError');

for (const [filename, errorName, mutation] of FETCH_PUBLIC_RESOURCES) {
    fetchVersionedResource(filename, function (data) {
        if (data === 'error') {
            store.commit('setResourceFetchError', errorName);
        }
        else {
            store.commit(mutation, data);
        }
    });
}

fetchPersonalDataToStore(store);

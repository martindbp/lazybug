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
        sessionTime: null,
        captionData: null,
        captionHash: null, // use this for event log
        DICT: null,
        HSK_WORDS: null,
        knowledge: Vue.ref({}),
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
            autoPause: true,
            characterSet: 'sm',
            blurCaptions: true,
            pin: {
                hz: false,
                py: false,
                tr: false,
                translation: false,
            },
            displayTranslation: 0, // index into [human, machine][min(idx, length)]
            knownLevels: {
                py: 4,
                hz: 2,
                tr: 4,
            },
            keyboardShortcutsToggle: true,
            keyboardShortcuts: DEFAULT_SHORTCUTS,
        }),
    },
    mutations: {
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
        setCaptionData(state, val) {
            state.captionData = val;
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
        setKnowledge(state, knowledge) {
            state.knowledge = knowledge;
            setIndexedDbData('knowledge', null, knowledge, function() {});
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
    },
});

fetchVersionedResource('public_cedict.json', function (data) { store.commit('setDict', data); });
fetchVersionedResource('hsk_words.json', function (data) { store.commit('setHskWords', data); });
getIndexedDbData('knowledge', null, function (data) {
    if (data) {
        const dict = {};
        for (const item of data) {
            dict[item.id] = item.value;
        }
        store.commit('setKnowledge', dict);
    }
});
getIndexedDbData('other', ['options'], function (data) {
    if (data[0]) store.commit('setOptions', data[0]);
});

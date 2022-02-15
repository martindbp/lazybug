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

const store = new Vuex.Store({
    state: {
        DICT: null,
        HSK_WORDS: null,
        knowledge: Vue.ref({}),
        captionFontScale: 0.5,
        captionOffset: [0, 0],
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
        captionData: null,
    },
    mutations: {
        setTimingOffset(state, val) {
            state.timingOffset = val;
        },
        setCaptionData(state, val) {
            state.captionData = val;
        },
        setShowOptions(state, val) {
            state.showOptions = val;
        },
        setShowDictionary(state, val) {
            state.showDictionary = val;
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
        setOptions(state, options) {
            state.options = options;
            setIndexedDbData('other', ['options'], [state.options], function() {});
        },
        setOption(state, option) {
            state.options[option.key] = option.value;
            setIndexedDbData('other', ['options'], [state.options], function() {});
        },
        setDeepOption(state, option) {
            state.options[option.key][option.key2] = option.value;
            setIndexedDbData('other', ['options'], [state.options], function() {});
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

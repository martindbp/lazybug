const KnowledgeUnknown = 0;
const KnowledgeKnown = 1;
const KnowledgeLearning = 2;

let knowledgeChanged = false;
let optionsChanged = false;

function setPinyinKnown(state, key, value) {
    const prevValue = state.knowledge[key];
    const [type, hz, pysStr] = key.split('-');
    if (type === 'py') {
        const pys = pysStr.split('/');
        for (let i = 0; i < pys.length; i++) {
            let hzChar = hz[i];
            let py = pys[i];
            const key = `${hzChar}-${py}`;
            let currKnownPys = state.knownPys[key];
            let currLearningPys = state.learningPys[key];
            if (currKnownPys === undefined) currKnownPys = 0;
            if (currLearningPys === undefined) currLearningPys = 0;

            if (value === KnowledgeKnown) {
                currKnownPys += 1;
                if (prevValue === KnowledgeLearning) {
                    currLearningPys -= 1;
                }
            }
            else if (value === KnowledgeLearning) {
                currLearningPys += 1;
                if (prevValue === KnowledgeKnown) {
                    currKnownPys -= 1;
                }
            }

            state.knownPys[key] = currKnownPys;
            state.learningPys[key] = currLearningPys;
        }
    }
}

const store = new Vuex.Store({
    state: {
        DICT: null,
        HSK_WORDS: null,
        knowledge: Vue.ref({}),
        knownPys: Vue.ref({}),
        learningPys: Vue.ref({}),
        captionFontScale: 0.5,
        captionOffset: [0, 0],
        peekStates: Vue.ref({'py': [], 'hz': [], 'tr': [], 'translation': false}),
        showOptions: false,
        showDictionary: false,
        options: Vue.ref({
            autoPause: true,
            characterSet: 'sm',
            show: {
                hz: null,
                py: null,
                tr: null,
                fullTr: false,
            },
            knownLevels: {
                py: 4,
                hz: 2,
                tr: 4,
            },
        }),
    },
    mutations: {
        setShowOptions(state, val) {
            state.showOptions = val;
        },
        setShowDictionary(state, val) {
            state.showDictionary = val;
        },
        setKnowledge(state, knowledge) {
            state.knowledge = knowledge;
            for (const [key, value] of Object.entries(knowledge)) {
                setPinyinKnown(state, key, value);
            }
        },
        setKnowledgeKey(state, keyVal) {
            state.knowledge[keyVal.key] = keyVal.val;
            setPinyinKnown(state, keyVal.key, keyVal.val);
            knowledgeChanged = true;
        },
        setKnowledgeKeys(state, keysVals) {
            for (let i = 0; i < keysVals.keys.length; i++) {
                const keyVal = {key: keysVals.keys[i], val: keysVals.vals[i]};
                state.knowledge[keyVal.key] = keyVal.val;
                setPinyinKnown(state, keyVal.key, keyVal.val);
            }
            knowledgeChanged = true;
        },
        increaseCaptionFontScale(state) {
            state.captionFontScale = Math.min(state.captionFontScale + 0.1, 1.0);
        },
        decreaseCaptionFontScale(state) {
            state.captionFontScale = Math.max(state.captionFontScale - 0.1, 0.0);
        },
        setCaptionOffset(state, offset) {
            state.captionOffset = offset;
        },
        setPeekState(state, val) {
            if (val.i === undefined || val.i === null) {
                state.peekStates[val.type] = true;
            }
            else {
                state.peekStates[val.type][val.i] = true;
            }
        },
        setPeekStates(state, val) {
            state.peekStates = val;
        },
        setOptions(state, options) {
            state.options = options;
        },
        setOption(state, option) {
            state.options[option.key] = option.value;
            optionsChanged = true;
        },
        setDeepOption(state, option) {
            state.options[option.key][option.key2] = option.value;
            optionsChanged = true;
        },
        setDict(state, dict) {
            state.DICT = dict;
        },
        setHskWords(state, words) {
            state.HSK_WORDS = words;
        },
    },
    getters: {
        getKnowledgeState: (state) => (key) => {
            const knowledgeState = state.knowledge[key];
            if (knowledgeState  === undefined) return undefined;
            return knowledgeState;
        }
    }
});

// Read current knowledge/options
chrome.storage.local.get(['knowledge', 'options'], (items) => {
    if (items.knowledge) store.commit('setKnowledge', items.knowledge);
    if (items.options) store.commit('setOptions', items.options);
});


setInterval(function() {
    if (knowledgeChanged) {
        chrome.storage.local.set({knowledge: store.state.knowledge}, function() {
            knowledgeChanged = false;
        });
    }
    if (optionsChanged) {
        chrome.storage.local.set({options: store.state.options}, function() {
            optionsChanged = false;
        });
    }
}, 5000);

fetchVersionedResource('public_cedict.json', function (data) { store.commit('setDict', data); });
fetchVersionedResource('hsk_words.json', function (data) { store.commit('setHskWords', data); });

app.mixin({
    methods: {
        sm2tr(text) {
            if (this.$store.state.DICT === null) return null;
            if (this.$store.state.options.characterSet == 'sm') return text;

            let trText = '';
            let nextIdx = 0;
            while (nextIdx < text.length) {
                let foundStr = text.substring(nextIdx, nextIdx+1);
                for (var i = nextIdx+1; i < text.length; i++) {
                    const subStr = text.substring(nextIdx, i);
                    if (this.$store.state.DICT[foundStr] !== undefined) {
                        break;
                    }
                    foundStr = subStr;
                }
                let entries = this.$store.state.DICT[foundStr];
                if (entries !== undefined) {
                    trText += dictArrayToDict(entries[0]).hzTrad;
                }
                else {
                    trText += foundStr;
                }

                nextIdx += foundStr.length;
            }

            return trText;
        },
        getWordLevel(hz) {
            if (this.$store.state.HSK_WORDS === null) return null;
            let wordLevel = null;
            for (let lvl = 0; lvl <= 5; lvl++) {
                if (this.$store.state.HSK_WORDS[lvl].includes(hz)) {
                    wordLevel = lvl+1;
                    break;
                }
            }
            return wordLevel;
        },
    },
    computed: {
        knownPysHSK: function() {
            const known = {};
            for (let lvl = 0; lvl < this.$store.state.options.knownLevels.py; lvl++) {
                for (const word of this.$store.state.HSK_WORDS[lvl]) {
                    for (const hzChar of word) {
                        const entries = this.$store.state.DICT[hzChar];
                        for (const entry of entries) {
                            const pys = dictArrayToDict(entry).pys;
                            const key = getKnowledgeKey('py', hzChar, pys, null);
                            known[key] = true;
                        }
                    }
                }
            }
            return known;
        }
    },
});


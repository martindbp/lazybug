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
    },
    computed: {
        lvlKnowledge: function() {
            if (this.$store.state.DICT === null || this.$store.state.HSK_WORDS === null) return {};
            const d = this.$store.state.DICT;
            const knowledge = {};
            for (let lvl = 0; lvl < 6; lvl++) {
                const knowPy = lvl <= this.$store.state.options.knownLevels.py;
                const knowHz = lvl <= this.$store.state.options.knownLevels.hz;
                const knowTr = lvl <= this.$store.state.options.knownLevels.tr;

                for (const hz of this.$store.state.HSK_WORDS[lvl]) {
                    if (knowHz) applyKnowledge(d, knowledge, 'hz', hz, null, null, null, KnowledgeKnown, false);
                    const entries = d[hz];
                    if (entries === undefined) continue;

                    for (let entry of entries) {
                        entry = dictArrayToDict(entry);
                        const pys = entry.pys;
                        if (knowPy) applyKnowledge(d, knowledge, 'py', hz, pys, null, null, KnowledgeKnown, false);
                        if (knowTr) applyKnowledge(d, knowledge, 'tr', hz, pys, null, null, KnowledgeKnown, false);
                        /*
                        for (const translation of entry.translations) {
                            if (knowTr) applyKnowledge(knowledge, 'tr', hz, pys, translation, false);
                        }
                        */
                    }
                }
            }
            return knowledge;
        },
    },
});


<template>
    <q-dialog seamless v-model="show" dark class="fixdialogheight">
        <q-card dark style="width: 600px" class="q-px-sm q-pb-md">
            <q-card-section align="center">
                <div class="text-h4" :style="{ color: '#E8E8E8' }">
                    <span
                        :class="{
                            char: true,
                            selected: i >= showRange[0] && i < showRange[1],
                            highlight: i >= highlightRange[0] && i < highlightRange[1],
                            firstchar: i == highlightRange[0],
                            lastchar: i == highlightRange[1] - 1
                        }"
                        v-for="(char, i) in text"
                        @mouseover="mouseoverChar = i"
                        @click="clickChar(i)"
                    >
                        {{ char }}
                    </span>
                </div>
            </q-card-section>
            <q-card-section align="left" style="padding: 25px; max-height: 400px; height: 400px" class="scroll">
                <q-separator color="orange" v-if="dictEntries.length > 0"/>
                <div v-for="entry in dictEntries">
                    <div>
                        <span class="text-h4">{{ entry.hz }}</span> <span class="hsklvl">(HSK{{ entry.lvl !== null ? entry.lvl : ': unknown'}})</span>
                    </div>
                    <div class="text-h6" :style="{ color: '#E8E8E8' }" v-for="item in entry.items">
                        <span v-for="(py, i) in item.pysDiacriticals" :style="{ color: COLORS[parseInt(item.pys[i].slice(-1))] }">
                            {{ py }}
                        </span>: {{ item.translations.join(' | ') }}</div>
                    <q-separator color="orange" />
                </div>
                <div v-if="dictEntries.length > 0"><br/>Source <a href="https://cc-cedict.org/wiki/">(CC-EDICT)</a></div>
                <div class="text-h5" v-if="dictEntries.length === 0 && text !== ''">
                    Click on a word to see the dictionary pinyin and translations
                </div>
            </q-card-section>
            <q-card-actions align="right" class="text-teal">
                <q-btn flat label="OK" @click="clickClose"></q-btn>
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script>


export default {
    mixins: [mixin],
    props: ['caption'],
    components: { },
    data: function() { return {
        mouseoverChar: null,
        COLORS: [
            null,
            '#DC143C', // red
            'orange',
            '#228B22', // green
            '#4169E1', // blue
            'gray'
        ],
        keyboardListener: null,
    }},
    mounted: function() {
        const self = this;
        this.keyboardListener = window.addEventListener("keydown", function(event) {
            if(event.key === "Escape") self.show = false;
        }, {capture: false});
    },
    beforeDestroy: function() {
        window.removeEventListener('keydown', this.keyboardListener);
    },
    computed: {
        text: function() {
            return this.texts.tr;
        },
        texts: function() {
            const sm = this.caption.texts.join(' ');
            return {
                sm: sm,
                tr: this.sm2tr(sm),
            };
        },
        show: {
            get: function() { return this.$store.state.showDialog.dictionary; },
            set: function(val) { this.$store.commit('setShowDictionary', {value: val}); },
        },
        showRange: {
            get: function() { return this.$store.state.showDictionaryRange; },
            set: function(val) { this.$store.commit('setShowDictionary', {range: val, playerId: this.playerId}); },
        },
        dictEntries: function() {
            if (this.$store.state.DICT === null || this.showRange[0] < 0) return [];

            const entries = []
            for (var i = this.showRange[0]+1; i <= this.showRange[1]; i++) {
                const text = this.text.substring(this.showRange[0], i);
                const textSm = this.texts.sm.substring(this.showRange[0], i);
                if (this.$store.state.DICT[textSm] !== undefined) {
                    let entryLvl = null;
                    for (let lvl = 0; lvl < 6; lvl++) {
                        if (this.$store.state.HSK_WORDS[lvl].includes(text)) {
                            entryLvl = lvl + 1;
                            break;
                        }
                    }
                    entries.push({hz: text, items: dictItemsToDict(this.$store.state.DICT[textSm]), lvl: entryLvl});
                }
            }

            return entries.reverse();
        },
        highlightRange: function() {
            if (this.$store.state.DICT === null || this.mouseoverChar === null) return [-1, -1];

            let range = [-1, -1];
            for (var i = this.mouseoverChar+1; i < this.texts.sm.length+1; i++) {
                if (this.$store.state.DICT[this.texts.sm.substring(this.mouseoverChar, i)] !== undefined) {
                    range = [this.mouseoverChar, i];
                }
            }
            return range;
        },
    },
    watch: {
        caption: function(newVal, oldVal) {
            this.show = false
            this.showRange = [-1, -1];
            this.mouseoverChar = null;
        },
        showRange: function(newVal, oldVal) {
            this.mouseoverChar = newVal[0];
        },
    },
    methods: {
        clickClose: function(event) {
            // Remove the "lazybugquasardialog" class from the dialog parent, otherwise there's some flickering
            let dialog = document.querySelector('.lazybugquasardialog');
            if (dialog) {
                dialog.classList.remove('lazybugquasardialog');
            }
            this.show = false;
        },
        clickChar: function(event) {
            this.showRange = this.highlightRange;
        },
    },
}
</script>
<style>

.lazybugquasardialog {
    z-index: 9999;
    position: absolute;
    left: 0;
}

.char {
    cursor: pointer;
}

.char.highlight {
    background: gray;
}

.firstchar {
    border-radius: 5px 0px 0px 5px;
}

.lastchar {
    border-radius: 0px 5px 5px 0px;
}

.firstchar.lastchar {
    border-radius: 5px;
}

.selected {
    text-decoration: underline;
    text-decoration-color: orange;
}

.hsklvl {
    font-size: 15px;
}

</style>

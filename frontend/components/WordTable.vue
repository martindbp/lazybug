<template>
    <div>
        <q-table
            title="Starred Words"
            :rows="rows"
            :columns="columns"
            selection="multiple"
            v-model:selected="selected"
            :loading="loading"
            @request="onRequest"
            :pagination="pagination"
            hide-pagination
            :class="{wordtable: true, mobile: isMobile}"
        >
          <template v-slot:body="props">
              <q-tr v-if="props.row.isNewSession">
                  <q-td colspan="100%">
                      <div style="font-size: 1.2em" >
                          <q-checkbox @update:model-value="checkedSession(props.row)" :model-value="selectedSessions[props.row.sessionId] ? true : false" color="primary" style="margin-right: 30px" /><b>{{ timestampToYYYMMDD(props.row.time) }}</b>:
                          {{ props.row.data.showName }} {{ props.row.data.seasonName }} {{ props.row.data.episodeName }}
                      </div>
                  </q-td>
              </q-tr>
              <q-tr :props="props">
                  <q-td>
                      <q-checkbox v-model="props.selected" color="primary" />
                  </q-td>
                  <q-td
                     v-for="col in props.cols"
                     :key="col.name"
                     :props="props"
                     @click="props.expand = !props.expand"
                     :style="{ cursor: 'pointer', fontSize: col.name === 'hz' ? '1.2em' : '1em' }"
                     v-html="col.value"
                     >
                  </q-td>
              </q-tr>
              <q-tr v-if="props.expand" v-show="props.expand" :props="props">
                  <q-td colspan="100%">
                      <div v-html="rowYoutubeEmbedCode(props.row.idx)" />
                  </q-td>
              </q-tr>
          </template>

          <template v-slot:top>
              <div class="text-h5">Starred Words</div>
              <q-btn icon="first_page" color="grey-8" round dense flat :disable="isFirstPage" @click="firstPage" />
              <q-btn icon="chevron_left" color="grey-8" round dense flat :disable="isFirstPage" @click="prevPage" />
              <q-btn icon="chevron_right" color="grey-8" round dense flat :disable="isLastPage" @click="nextPage" />
              <q-btn icon="last_page" color="grey-8" round dense flat :disable="isLastPage" @click="lastPage" />
              <q-btn-dropdown :disabled="selected.length === 0" color="primary" label="Export" style="margin-left: 5px; margin-right: 5px">
                  <q-list>
                      <q-item clickable v-close-popup @click="showExportDialog = true">
                          <q-item-section>
                              <q-item-label>Anki CSV</q-item-label>
                          </q-item-section>
                      </q-item>
                      <q-item clickable v-close-popup @click="exportPleco">
                          <q-item-section>
                              <q-item-label>Pleco (word list)</q-item-label>
                          </q-item-section>
                      </q-item>
                  </q-list>
              </q-btn-dropdown>
              {{ getSelectedString() }}
          </template>
        </q-table>
        <q-dialog class="fixdialogheight" v-model="showExportDialog" seamless>
            <q-card>
                <q-tabs
                   v-model="ankiCardTab"
                   no-caps
                   class="bg-orange text-white shadow-2"
                 >
                    <q-tab name="basic" label="Basic" />
                    <q-tab name="cloze" label="Cloze" />
                    <q-tab name="advanced" label="Advanced" />
                </q-tabs>
                <q-tab-panels v-model="ankiCardTab">
                    <q-tab-panel name="basic">
                        <q-card-section class="row items-center">
                            <div class="q-pa-md q-gutter-y-sm column">
                                <q-toggle v-for="(card, idx) in ankiCardsBasic" :label="card" v-model="ankiCardsBasicToggled[idx]" @update:model-value="updateAnkiCardsBasicToggled"/>
                            </div>
                        </q-card-section>

                        <q-card-actions align="right">
                            <q-btn flat label="Cancel" color="primary" v-close-popup />
                            <q-btn flat label="Export" color="primary" v-close-popup @click="exportToAnkiBasic" />
                        </q-card-actions>
                    </q-tab-panel>
                    <q-tab-panel name="cloze">
                        <q-card-section class="row items-center">
                            <q-toggle label="Include word translation hint" v-model="ankiCardsClozeIncludeHint" @update:model-value="updateAnkiCardsClozeIncludeHint"/>
                        </q-card-section>

                        <q-card-actions align="right">
                            <q-btn flat label="Cancel" color="primary" v-close-popup />
                            <q-btn flat label="Export" color="primary" v-close-popup @click="exportToAnkiCloze" />
                        </q-card-actions>
                    </q-tab-panel>
                    <q-tab-panel name="advanced">
                        <q-card-section v-if="editAnkiCards" class="row items-center">
                            <div class="q-pa-md q-gutter-y-sm column">
                                <q-input v-model="ankiCardsEditText" filled type="textarea" />
                                <q-btn flat label="Done" color="primary" @click="doneEditAnkiCards" />
                            </div>
                        </q-card-section>
                        <q-card-section v-else class="row items-center">
                            <div class="q-pa-md q-gutter-y-sm column">
                                <q-toggle v-for="(card, idx) in ankiCardsAdvanced" :label="card" v-model="ankiCardsAdvancedToggled[idx]" @update:model-value="updateAnkiCardsAdvancedToggled"/>
                                <q-btn flat label="Edit Cards" color="primary" @click="startEditAnkiCards"/>
                            </div>
                        </q-card-section>

                        <q-card-actions align="right">
                            <q-btn flat label="Cancel" color="primary" v-close-popup />
                            <q-btn flat label="Export" color="primary" v-close-popup @click="exportToAnkiAdvanced" />
                        </q-card-actions>
                    </q-tab-panel>
                </q-tab-panels>
            </q-card>
        </q-dialog>
    </div>
</template>

<script>
const FIELD_TO_LABEL = {
    hz: 'Hanzi',
    tr: 'Translation',
    py: 'Pinyin',
    translation: 'Full Translation',
};


const ROWS_PER_PAGE = 4;

export default {
    mixins: [mixin],
    data: function() { return {
        columns: [
            {name: 'hz', field: 'hz', label: FIELD_TO_LABEL.hz},
            {name: 'py', field: 'py', label: FIELD_TO_LABEL.py},
            {name: 'tr', field: 'tr', label: FIELD_TO_LABEL.tr},
            {name: 'translation', field: 'translation', label: FIELD_TO_LABEL.translation},
        ],
        selected: [],
        selectedSessions: {},
        starEvents: [],
        pagination: {
            rowsPerPage: 0,
        },
        rows: [],
        page: 0,
        numRows: 0,
        numPages: 0,
        loading: true,
        tab: Vue.ref('history'),
        ankiCardTab: Vue.ref('basic'),
        showExportDialog: false,
        editAnkiCards: false,
        ankiCardsEditText: '',
        ankiCardsBasic: [
            'Pinyin -> Translation',
            'Translation -> Pinyin + Hanzi',
            'Hanzi -> Pinyin + Translation',
        ],
        ankiCardsCloze: [
            'Normal cloze',
            'Cloze w/ word translation hint',
        ],
    }},
    mounted: function() {
        const self = this;
        getLogRows(function(numRows) {
            self.numRows = numRows;
            self.numPages = Math.ceil(numRows / ROWS_PER_PAGE);
        });
    },
    computed: {
        ankiCardsAdvanced: {
            get: function() { return this.$store.state.options.anki.advancedCards; },
            set: function(val) { this.$store.commit('setAnkiAdvancedCards', val); },
        },
        ankiCardsBasicToggled: {
            get: function() { return this.$store.state.options.anki.basicToggled; },
            set: function(val) { this.$store.commit('setAnkiCardsBasicToggled', val); },
        },
        ankiCardsClozeIncludeHint: {
            get: function() { return this.$store.state.options.anki.clozeIncludeHint; },
            set: function(val) { this.$store.commit('setAnkiCardsClozeIncludeHint', val); },
        },
        ankiCardsAdvancedToggled: {
            get: function() { return this.$store.state.options.anki.advancedToggled; },
            set: function(val) { this.$store.commit('setAnkiCardsAdvancedToggled', val); },
        },
        isFirstPage: function() {
            return this.page === 0;
        },
        isLastPage: function() {
            return this.numPages === 0 || this.page === this.numPages - 1;
        },
    },
    watch: {
        page: {
            immediate: true,
            handler: function(newValue) {
                this.requestPageData(newValue);
            },
        },
        numRows: {
            handler: function(newValue) {
                this.requestPageData(this.page);
            },
        }
    },
    methods: {
        checkedSession: function(row) {
            this.selectedSessions[row.sessionId] = ! this.selectedSessions[row.sessionId];

            // First remove any of the session items that are selected
            const newSelected = [];
            for (let i = 0; i < this.selected.length; i++) {
                const r = this.selected[i];
                if (r.sessionId !== row.sessionId) {
                    newSelected.push(r);
                }
            }

            if (this.selectedSessions[row.sessionId]) {
                // Add in all the session rows
                for (let i = row.idx; i < this.rows.length; i++) {
                    const r = this.rows[i];
                    if (r.sessionId !== row.sessionId) break;

                    newSelected.push(r);
                }
            }

            this.selected = newSelected;
        },
        startEditAnkiCards: function() {
            this.ankiCardsEditText = this.ankiCardsAdvanced.join('\n');
            this.editAnkiCards = true;
        },
        doneEditAnkiCards: function() {
            this.editAnkiCards = false;
            this.ankiCardsAdvanced = this.ankiCardsEditText.split('\n').filter((card) => card.trim().length > 0);
            const toggled = [];
            for (let i = 0; i < this.ankiCardsAdvanced.length; i++) toggled.push(false);
            this.ankiCardsAdvancedToggled = toggled;
            this.ankiCardsEditText = '';
        },
        updateAnkiCardsBasicToggled: function() {
            this.$store.commit('setAnkiCardsBasicToggled', this.ankiCardsBasicToggled);
        },
        updateAnkiCardsClozeIncludeHint: function() {
            this.$store.commit('setAnkiCardsClozeIncludeHint', this.ankiCardsClozeIncludeHint);
        },
        updateAnkiCardsAdvancedToggled: function() {
            this.$store.commit('setAnkiCardsAdvancedToggled', this.ankiCardsAdvancedToggled);
        },
        firstPage: function() {
            this.page = 0;
        },
        lastPage: function() {
            this.page = this.numPages - 1;
        },
        prevPage: function() {
            this.page = Math.max(0, this.page - 1);
        },
        nextPage: function() {
            this.page = Math.min(this.numPages - 1, this.page + 1);
        },
        requestPageData: function(page) {
            const self = this;
            const offset = page * ROWS_PER_PAGE;
            const limit = Math.min(ROWS_PER_PAGE, this.numRows - offset);
            this.loading = false;
            if (limit === 0) return;

            console.log('Fetching', offset, limit);
            this.loading = true;
            getLog(offset, limit, function(data) {
                self.starEvents = self.filterStarEvents(data);
                self.rows = self.starEventsToRows(self.starEvents);
                self.pagination.rowsPerPage = self.rows.length;
                self.loading = false;
            });
        },
        reverseEventsMap: function(eventId) {
            return reverseEventsMap[eventId];
        },
        getSelectedString: function() {
            return this.selected.length === 0 ? '' : `${this.selected.length} item${this.selected.length > 1 ? 's' : ''}`;
        },
        exportPleco: function() {
            let list = '';
            for (const item of this.selected) {
                const [type, eventData, sessionTime, captionId, captionHash] = item.event;
                const [wordIdx, data] = eventData;

                const wordData = getWordData(data.data, data.translationIdx);
                if (wordIdx === null) {
                    continue
                }
                else {
                    const sm = wordData.hz[wordIdx];
                    const trad = this.sm2tr(sm, false);
                    list += `${sm}[${trad}]\n`;
                }
            }
            const filename = `export-pleco-${(new Date(Date.now())).toISOString().split('T')[0]}.txt`;
            download(filename, list);
        },
        exportToAnkiBasic: function() {
            let csv = '';
            for (const item of this.selected) {
                const [type, eventData, sessionTime, captionId, captionHash] = item.event;
                const [wordIdx, data] = eventData;

                const wordData = getWordData(data.data, data.translationIdx);
                if (wordIdx === null) {
                    // Full Hanzi -> Full Translation
                    csv += `${data.data.texts.join(' ')};${wordData.translation}\n`;
                }
                else {
                    if (this.ankiCardsBasicToggled[0]) {
                        // Pinyin -> Translation
                        csv += `${wordData.py[wordIdx]};${wordData.tr[wordIdx]}\n`;
                    }
                    if (this.ankiCardsBasicToggled[1]) {
                        // Translation -> Pinyin + Hanzi
                        csv += `${wordData.tr[wordIdx]};${wordData.py[wordIdx]} / ${wordData.hz[wordIdx]}\n`;
                    }
                    else if (this.ankiCardsBasicToggled[2]) {
                        // Hanzi -> Pinyin + Translation
                        csv += `${wordData.hz[wordIdx]};${wordData.py[wordIdx]} / ${wordData.tr[wordIdx]}\n`;
                    }
                }
            }
            const filename = `export-anki-basic-${(new Date(Date.now())).toISOString().split('T')[0]}.csv`;
            download(filename, csv);
        },
        exportToAnkiCloze: function() {
            let csv = '';
            for (const item of this.selected) {
                const [type, eventData, sessionTime, captionId, captionHash] = item.event;
                const [wordIdx, data] = eventData;

                const wordData = getWordData(data.data, data.translationIdx);
                if (wordIdx === null) {
                    continue; // no cloze for this kind
                }
                else {
                    // Pinyin + Hanzi
                    let pinyin = '';
                    let hanzi = '';
                    for (let i = 0; i < wordData.hz.length; i++) {
                        if (i == wordIdx) {
                            hanzi += `{{c1::${wordData.hz[i]}}}`;
                            pinyin += `{{c1::${wordData.py[i]}}}`;
                        }
                        else {
                            hanzi += wordData.hz[i];
                            pinyin += wordData.py[i];
                        }
                    }

                    if (this.ankiCardsClozeIncludeHint) {
                        csv += `${pinyin}<br>${hanzi}<br><br>Word translation: ${wordData.tr[wordIdx]};${wordData.translation}\n`;
                    }
                    else {
                        csv += `${pinyin}<br>${hanzi}<br>;${wordData.translation}\n`;
                    }
                }
            }
            const filename = `export-anki-cloze-${(new Date(Date.now())).toISOString().split('T')[0]}.csv`;
            download(filename, csv);
        },
        exportToAnkiAdvanced: function() {
            let csv = '';
            for (const item of this.selected) {
                const [type, eventData, sessionTime, captionId, captionHash] = item.event;
                const [wordIdx, data] = eventData;
                const t0 = data.data.t0;
                const t1 = data.data.t1;

                const wordData = getWordData(data.data, data.translationIdx);

                const rowData = {
                    type: type,
                    captionId: captionId,
                    captionHash: captionHash,
                    wordData: wordData,
                    hidden: data.hidden,
                    captionIdx: data.captionIdx,
                    wordIdx: wordIdx,
                    t0: t0,
                    t1: t1,
                };
                let search = '';
                if (wordIdx === null) {
                    search = wordData.translation;
                }
                else {
                    search = wordData.hz[wordIdx] + '/' + wordData.py[wordIdx];

                    const hz = wordData.hz[wordIdx];
                    if (this.$store.state.DICT[hz] !== undefined) {
                        rowData.dictionary = dictItemsToDict(this.$store.state.DICT[hz]);
                    }
                }

                const exportVals = [];
                for (const val of this.ankiCardsAdvancedToggled) {
                    exportVals.push(val ? '1' : '');
                }

                exportVals.push(wordIdx === null ? '1' : '');

                csv += `${search};${JSON.stringify(rowData)};${exportVals.join(';')}\n`;
            }
            const filename = `export-anki-advanced-${(new Date(Date.now())).toISOString().split('T')[0]}.csv`;
            download(filename, csv);
        },
        rowYoutubeEmbedCode: function(rowIdx) {
            const [type, eventData, sessionTime, captionId, captionHash] = this.starEvents[rowIdx];
            const [wordIdx, data] = eventData;
            const t0 = data.data.t0;
            const t1 = data.data.t1;
            const parts = captionId.split('-');
            const id = parts.slice(1).join('-');
            return getYoutubeEmbedCode(id, t0, t1);
        },
        timestampToYYYMMDD: function(val) {
            return (new Date(val)).toISOString().split('T')[0];
        },
        filterStarEvents: function(sessions) {
            const events = [];
            if (sessions === null) return events;

            for (const session of sessions) {
                for (let i = 0; i < session.eventIds.length; i++) {
                    const eventId = session.eventIds[i];
                    if (eventId === null) continue;
                    const eventData = session.eventData[i];
                    const eventName = reverseEventsMap[eventId];
                    if (eventName.startsWith("EVENT_STAR")) {
                        if (session.showName) {
                            // Old data has showName/seasonName/episodeName
                            eventData[1].showName = resolveShowName(session.showName);
                            eventData[1].seasonName = session.seasonName;
                            eventData[1].episodeName = session.episodeName;
                        }
                        else {
                            const showInfo = this.$store.state.showList[session.showId];
                            eventData[1].showName = resolveShowName(showInfo.name);
                            eventData[1].seasonName = getSeasonName(showInfo, session.seasonIdx);
                            eventData[1].episodeName = getEpisodeName(showInfo, session.seasonIdx, session.episodeIdx);
                        }

                        let type = null;
                        if (eventName.endsWith('PY')) {
                            type = 'py';
                        }
                        else if (eventName.endsWith('HZ')) {
                            type = 'hz';
                        }
                        else if (eventName.endsWith('TR')) {
                            type = 'tr';
                        }
                        else if (eventName.endsWith('TRANSLATION')) {
                            type = 'translation';
                        }
                        events.push([type, eventData, session.sessionTime, session.captionId, session.captionHash]);
                    }
                }
            }

            return events;
        },
        starEventsToRows: function(events) {
            const rows = [];
            let lastSessionId = null;
            const seenIds = new Set();
            for (let i = 0; i < events.length; i++) {
                const [type, eventData, sessionTime, captionId, captionHash] = events[i];
                let [wordIdx, data] = eventData;
                const wordData = getWordData(data.data, data.translationIdx);
                const dt = data.dt;

                const sessionId = `${sessionTime}-${captionId}`;

                let py = null;
                let hz = null;
                let tr = null;
                let translation = wordData.translation;
                const text = data.data.texts.join(' ');
                if (! [null, undefined].includes(wordIdx)) {
                    const alignmentIdx = wordData.alignmentIndices[wordIdx];
                    const alignment = data.data.alignments[alignmentIdx];
                    const [startIdx, endIdx, ...rest] = alignment;

                    py = wordIdx !== null ? wordData.py[wordIdx] : '';
                    hz = wordIdx !== null ? wordData.hz[wordIdx] : '';
                    tr = wordIdx !== null ? wordData.tr[wordIdx] : '';
                    translation = null;
                }
                else {
                    hz = text;
                }

                const id = `${sessionTime}-${dt}-${captionId}-${py}-${hz}-${tr}-${wordData.translation}`;
                if (seenIds.has(id)) continue;
                seenIds.add(id);

                rows.push({
                    id: id,
                    idx: i,
                    type: type,
                    py: py,
                    hz: hz,
                    tr: tr,
                    translation: translation,
                    time: sessionTime,
                    video: captionId,
                    sessionId: sessionId,
                    isNewSession: sessionId !== lastSessionId,
                    data: data,
                    event: events[i],
                });

                lastSessionId = sessionId;
            }

            return rows;
        },
    },
};
</script>

<style>
.wordtable {
    display: inline-block;
}
.wordtable:not(.mobile) {
    margin-top: 50px;
    margin-left: 50px;
    min-width: 500px;
}
</style>

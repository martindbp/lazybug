<template>
    <div class="q-pa-md" style="width: 50%; left: 25%; position: absolute; min-width: 500px;">
        <q-card>
        <q-tabs
           v-model="tab"
           no-caps
           class="bg-orange text-white shadow-2"
         >
            <q-tab name="history" label="History" />
            <q-tab name="options" label="Options" />
        </q-tabs>

        <q-tab-panels v-model="tab">
            <q-tab-panel name="history">
                <q-table
                    style="width: 100%; display: inline-block"
                    title="Starred"
                    :rows="rows"
                    :columns="columns"
                    selection="multiple"
                    v-model:selected="selected"
                    :loading="loading"
                    @request="onRequest"
                    :pagination="pagination"
                    hide-pagination
                >
                  <template v-slot:body="props">
                      <q-tr v-if="props.row.isNewSession">
                          <q-td colspan="100%">
                              <div style="font-size: 1.2em" ><b>{{ timestampToYYYMMDD(props.row.time) }}</b>:
                                  {{ props.row.data.showName }} {{ props.row.data.seasonName }} {{ props.row.data.episodeName }}</div>
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
                      <div class="text-h5">Starred</div>
                      <q-btn
                           icon="first_page"
                           color="grey-8"
                           round
                           dense
                           flat
                           :disable="isFirstPage"
                           @click="firstPage"
                       />

                      <q-btn
                           icon="chevron_left"
                           color="grey-8"
                           round
                           dense
                           flat
                           :disable="isFirstPage"
                           @click="prevPage"
                       />

                      <q-btn
                           icon="chevron_right"
                           color="grey-8"
                           round
                           dense
                           flat
                           :disable="isLastPage"
                           @click="nextPage"
                       />

                      <q-btn
                           icon="last_page"
                           color="grey-8"
                           round
                           dense
                           flat
                           :disable="isLastPage"
                           @click="lastPage"
                       />
                          {{ getSelectedString() }}
                  </template>
                </q-table>
                <div class="q-mt-md">
                    <q-btn :disabled="selected.length === 0" label="Export to Anki" @click="exportToAnki"/>
                </div>
            </q-tab-panel>
            <q-tab-panel name="options">
                <q-btn color="secondary" label="Clear cache" @click="clearCache" :disabled="clickedClearCache" />
                <br>
                <br>
                <q-btn color="deep-orange" label="Clear personal data" @click="clearPersonalData" :disabled="clickedClearPersonalData" />
                <br>
                (Will permanently delete personal data)
                <br>
                <br>
                <q-btn color="green" label="Export Database File" @click="exportDb" />
                <br>
                <br>
                <q-btn color="blue" label="Import Database File" @click="importDb" />
            </q-tab-panel>
        </q-tab-panels>
        </q-card>
    </div>
</template>

<script>
const FIELD_TO_LABEL = {
    hz: 'Hanzi',
    tr: 'Translation',
    py: 'Pinyin',
    translation: 'Full Translation',
};


function wrapInColorSpan(str, color) {
    return `<span style="border-radius: 3px; border: 2px dotted ${color}">${str}</span>`;
}

const ROWS_PER_PAGE = 4;

export default {
    data: function() { return {
        columns: [
            {name: 'hz', field: 'hz', label: FIELD_TO_LABEL.hz},
            {name: 'py', field: 'py', label: FIELD_TO_LABEL.py},
            {name: 'tr', field: 'tr', label: FIELD_TO_LABEL.tr},
            {name: 'translation', field: 'translation', label: FIELD_TO_LABEL.translation},
        ],
        selected: [],
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
        clickedClearCache: false,
        clickedClearPersonalData: false,
    }},
    mounted: function() {
        const self = this;
        getLogRows(function(numRows) {
            self.numRows = numRows;
            self.numPages = Math.ceil(numRows / ROWS_PER_PAGE);
        });
    },
    computed: {
        isFirstPage: function() {
            return this.page === 0;
        },
        isLastPage: function() {
            return this.page === this.numPages - 1;
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
            this.loading = true;
            const offset = page * ROWS_PER_PAGE;
            const limit = Math.min(ROWS_PER_PAGE, this.numRows - offset);
            if (limit === 0) return;

            console.log('Fetching', offset, limit);
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
        exportToAnki: function() {
            let csv = '';
            for (const item of this.selected) {
                const [type, eventData, sessionTime, captionId, captionHash] = item.event;
                const [_, idx, data] = eventData;
                const t0 = data.data.t0;
                const t1 = data.data.t1;

                const wordData = getWordData(data.data, data.translationIdx);
                const cloze = captionToAnkiCloze(wordData, data.hidden, data.captionIdx, type, idx, captionId, captionHash, t0, t1, true);
                csv += cloze + '\n'
            }
            const filename = 'anki-export-'+(new Date(Date.now())).toISOString().split('T')[0]+'.csv'
            download(filename, csv);
        },
        rowYoutubeEmbedCode: function(rowIdx) {
            const [type, eventData, sessionTime, captionId, captionHash] = this.starEvents[rowIdx];
            const [_, idx, data] = eventData;
            const t0 = data.data.t0;
            const t1 = data.data.t1;
            const [site, id] = captionId.split('-');
            return getYoutubeEmbedCode(id, t0, t1);
        },
        timestampToYYYMMDD: function(val) {
            return (new Date(val)).toISOString().split('T')[0];
        },
        filterStarEvents: function(sessions) {
            const events = [];
            if (sessions === null) return events;

            for (const session of sessions) {
                for (const event of session.events) {
                    const eventName = reverseEventsMap[event[0]];
                    if (eventName.startsWith("EVENT_STAR")) {
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
                        const idx = event[1];
                        events.push([type, event, session.sessionTime, session.captionId, session.captionHash]);
                    }
                }
            }

            return events;
        },
        starEventsToRows: function(events) {
            const rows = [];
            let lastSessionId = null;
            for (let i = 0; i < events.length; i++) {
                const [type, eventData, sessionTime, captionId, captionHash] = events[i];
                let [_, idx, data] = eventData;
                const wordData = getWordData(data.data, data.translationIdx);
                const dt = data.dt;

                const sessionId = `${sessionTime}-${captionId}`;

                let py = null;
                let hz = null;
                let fullHz = null;
                let tr = null;
                let translation = wordData.translation;
                const text = data.data.texts.join(' ');
                if (! [null, undefined].includes(idx)) {
                    const alignmentIdx = wordData.alignmentIndices[idx];
                    const alignment = data.data.alignments[alignmentIdx];
                    const [startIdx, endIdx, ...rest] = alignment;

                    let hzColor = 'gray';
                    if (type === 'hz') {
                        hzColor = 'darkorange';
                    }
                    fullHz = `${text.substring(0, startIdx)}<span style="border-radius: 3px; border: 2px dotted ${hzColor}">${text.substring(startIdx, endIdx)}</span>${text.substring(endIdx)}`;

                    py = idx !== null ? wordData.py[idx] : '';
                    hz = idx !== null ? wordData.hz[idx] : '';
                    tr = idx !== null ? wordData.tr[idx] : '';
                    //translation = null;
                }
                else {
                    fullHz = text;
                }

                const id = `${sessionTime}-${dt}-${captionId}-${py}-${hz}-${tr}-${wordData.translation}`;

                if (type === 'py') py = wrapInColorSpan(py, 'darkorange');
                else if (type === 'tr') tr = wrapInColorSpan(tr, 'darkorange');
                else if (type === 'translation') translation = wrapInColorSpan(translation, 'darkorange');

                rows.push({
                    id: id,
                    idx: i,
                    type: type,
                    py: py,
                    hz: fullHz,
                    tr: tr,
                    translation: translation,
                    time: sessionTime,
                    video: captionId,
                    isNewSession: sessionId !== lastSessionId,
                    data: data,
                    event: events[i],
                });
                lastSessionId = sessionId;
            }

            return rows;
        },
        clearCache: function() {
            clearCache();
            this.clickedClearCache = true;
        },
        clearPersonalData: function() {
            const self = this;
            clearPersonalData(function() {
                fetchPersonalDataToStore(self.$store);
                self.clickedClearPersonalData = true;
            });
        },
        exportDb: function() {
            exportDatabaseJson(function(data) {
                const filename = 'database-'+(new Date(Date.now())).toISOString().split('T')[0]+'.json'
                download(filename, JSON.stringify(data));
            });
        },
        importDb: function() {
            var fileChooser = document.createElement("input");
            fileChooser.style.display = 'none';
            fileChooser.type = 'file';

            fileChooser.addEventListener('change', function (evt) {
                var f = evt.target.files[0];
                if(f) {
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        const data = JSON.parse(e.target.result);
                        importDatabaseJson(data, function(error) {
                            if (! [null, undefined].includes(error)) {
                                alert('Something went wrong: ' + error);
                            }
                            else {
                                alert('Successfully imported database');
                            }
                       });
                    }
                    reader.readAsText(f);
                }
            });

            document.body.appendChild(fileChooser);
            fileChooser.click();
        }
    },
};
</script>

<style>
</style>

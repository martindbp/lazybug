<template>
    <div>
    <q-table
      :rows="rows"
      :columns="columns"
      :pagination="pagination"
      :loading="isLoading"
      row-key="name"
      :class="{showtable: true, mobile: isMobile}"
    >
        <template v-slot:top-left>
            <q-input borderless dense debounce="300" v-model="searchFilter" placeholder="Search">
                <template v-slot:prepend>
                    <q-icon name="search" />
                </template>
            </q-input>
        </template>
        <template v-slot:header-cell="props">
            <q-th :props="props">
                {{ props.col.label }}
                <span v-if="columnFilters[props.col.name] !== undefined">
                    <q-badge class="clickablebadge" @click.stop.prevent="removeFilter(...filter)" v-for="filter in columnFilters[props.col.name]" :color="mapToColor(filter[1], filter[2])">{{filter[2]}}</q-badge>
                </span>
            </q-th>
        </template>
        <template v-slot:body="props">
            <q-tr :props="props" @click="setPlaying(props.row.showId)" style="cursor: pointer;" >
                <q-tooltip delay="200" anchor="top left" self="top right" :offset="[-10, 9]" style="background: rgba(0,0,0,0)">
                    <img width="100" :src="thumbnailURL(props.row)" />
                </q-tooltip>
                <q-td key="name" :props="props" class="text-subtitle1" style="max-width: 350px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
                    <span v-if="props.cols[0].value.en">
                        {{ props.cols[0].value.hz }}<br>
                        {{ props.cols[0].value.en }}
                    </span>
                    <span v-else>
                        {{ props.cols[0].value }}
                    </span>
                    <q-badge style="margin-left: 5px" v-if="props.row.is_new" :color="mapToColor('new')">new</q-badge>
                </q-td>
                <q-td key="difficulty" :props="props">
                    <q-badge :color="mapDifficultyToColor(props.cols[1].value)">
                        {{ props.cols[1].value }}
                    </q-badge>
                </q-td>
                <q-td key="percent_known_vocab" :props="props">
                    <q-linear-progress v-if="[null, undefined].includes(props.cols[2].value)" query />
                    <q-linear-progress v-else color="green" instant-feedback :value="props.cols[2].value" />
                </q-td>
                <q-td key="douban" :props="props">
                    <span v-if="props.cols[3].value === 'N/A'">N/A</span>
                    <q-badge v-else :color="mapDoubanToColor(props.cols[3].value)">
                        {{ props.cols[3].value }}
                    </q-badge>
                </q-td>
                <q-td key="type" :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('type', 'type', props.cols[4].value)" :color="mapToColor('type', props.cols[4].value)">
                        {{ props.cols[4].value }}
                    </q-badge>
                </q-td>
                <q-td key="year" :props="props" style="white-space: normal; max-width: 200px;">
                    {{ props.cols[5].value }}
                </q-td>
                <q-td key="genres" :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('genres', 'genres', genre)" v-for="genre in props.cols[6].value" :color="mapToColor('genres', genre)">
                        {{ genre }}
                    </q-badge>
                </q-td>
                <q-td key="synopsis" :props="props" style="white-space: normal; max-width: 200px;">
                    {{ props.cols[7].value }}
                </q-td>
                <q-td key="sources" :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('sources', 'caption_source', props.cols[8].value[0])" :color="mapToColor('caption_source', props.cols[8].value[0])">
                        {{ props.cols[8].value[0] }}
                    </q-badge>
                    <br>
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('sources', 'translation_source', props.cols[8].value[1])" :color="mapToColor('translation_source', props.cols[8].value[1])">
                        {{ props.cols[8].value[1] }}
                    </q-badge>
                </q-td>
                <q-td key="num_processed" :props="props" style="white-space: normal; max-width: 200px;">
                    {{ props.cols[9].value }}
                </q-td>
                <q-td key="free" :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('free', 'free', props.cols[10].value)"  :color="mapToColor('free', props.cols[10].value)">
                        {{ props.cols[10].value ? 'free' : 'paid' }}
                    </q-badge>
                </q-td>
            </q-tr>
        </template>
    </q-table>
    </div>
</template>

<script>

var roundToScale = function(n, scale) {
    return parseFloat((Math.round(n / scale) * scale).toFixed(1));
};

function isNew(date) {
    return ((Date.now() - Date.parse(date)) < 1000*3600*24*30)  // within 30 days
}

export default {
    mixins: [mixin],
    data: function() { return {
        searchFilter: '',
        pagination: {
            rowsPerPage: 25,
        },
        columns: [
          {
            name: 'name',
            required: true,
            label: 'Name',
            align: 'left',
            field: row => row.name,
            sortable: true
          },
          {
            name: 'difficulty',
            required: true,
            label: 'Difficulty',
            align: 'left',
            field: row => roundToScale(10*(row.difficulty !== undefined ? row.difficulty : row.difficulty_manual), 0.1),
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'percent_known_vocab',
            required: true,
            label: '% Known',
            field: row => row.percent_known_vocab,
            sortable: true
          },
          {
            name: 'douban',
            required: true,
            label: 'Douban',
            align: 'left',
            field: row => row.douban || 'N/A',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'type',
            required: true,
            label: 'Type',
            align: 'left',
            field: row => row.type || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'year',
            required: true,
            label: 'Year',
            align: 'left',
            field: row => row.year || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'genres',
            required: true,
            label: 'Genres',
            align: 'left',
            field: row => row.genres,
            sortable: true
          },
          {
            name: 'synopsis',
            required: true,
            label: 'Synopsis',
            align: 'left',
            field: row => row.synopsis || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'sources',
            required: true,
            label: 'Sources',
            align: 'left',
            field: row => [row.caption_source, row.translation_source],
            sortable: true
          },
          {
            name: 'num_processed',
            required: true,
            label: '#',
            align: 'left',
            field: row => row.num_processed || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'free',
            required: true,
            label: 'Free',
            align: 'left',
            field: row => row.free,
            sortable: true
          },
        ],
        filters: null,
    }},
    computed: {
        rows: function() {
            if (this.$store.state.showList === null) return [];
            let showPercentKnown = this.showPercentKnown;
            let rows = Object.values(this.$store.state.showList).filter((show) => show.released);
            let filters = this.filters;
            if (filters !== null) {
                rows = rows.filter(row => {
                    let allMatch = true;
                    for (const [filterCol, filterProp, filterVal] of filters) {
                        if (Array.isArray(row[filterProp])) {
                            if (! row[filterProp].includes(filterVal)) allMatch = false;
                        }
                        else {
                            if (row[filterProp] !== filterVal) allMatch = false;
                        }
                    }
                    return allMatch;
                });
            }
            if (this.searchFilter.length > 0) {
                rows = rows.filter(row => {
                    let sourceStrings = [
                        removeDiacritics(this.searchFilter.toLowerCase().replace(' ', '')),
                    ];

                    let targetStrings = [];
                    if (typeof(row.name) === 'object') {
                        if (row.name.hz) targetStrings.push(row.name.hz.toLowerCase().replace(' ', ''));
                        if (row.name.py) targetStrings.push(removeDiacritics(row.name.py).toLowerCase().replace(' ', ''));
                        if (row.name.en) targetStrings.push(row.name.en.toLowerCase().replace(/[^A-Za-z0-9 ]/, ''));
                    }
                    else {
                        targetStrings.push(row.name.toLowerCase().replace(' ', ''))
                    }
                    for (const t of targetStrings) {
                        for (const s of sourceStrings) {
                            if (t.includes(s)) return true;
                        }
                    }
                    return false;
                });
            }

            // Add in the % known and isNew properties
            rows = rows.map(row => {
                let val = null;
                if (showPercentKnown === 0) val = null;
                else if (showPercentKnown === null) val = 0;
                else val = showPercentKnown[row.showId];
                row.percent_known_vocab = val;
                row.is_new = isNew(row.date_added);
                return row;
            });

            // If there are no filters, sort by "is_new"
            if (filters === null && this.searchFilter.length === 0) {
                rows = rows.sort((a, b) => {
                    return b.is_new - a.is_new;
                });
            }

            return rows;
        },
        columnFilters: function() {
            let colFilters = {};
            if (this.filters === null) return colFilters;

            for (const [col, rowProp, val] of this.filters) {
                colFilters[col] = colFilters[col] || [];
                colFilters[col].push([col, rowProp, val]);
            }
            return colFilters;
        },
        isLoading: function() {
            return this.$store.state.showList === null;
        },
    },
    methods: {
        thumbnailURL: function(showInfo) {
            return youtubeThumbnailURL(showInfo.seasons[0].episodes[0].id);
        },
        mapDifficultyToColor: function(difficulty) {
            if (difficulty < 4) return 'green';
            else if (difficulty < 7) return 'orange';
            else return 'red';
        },
        mapDoubanToColor: function(score) {
            if (score < 7) return 'red';
            else if (score < 8.0) return 'orange';
            else return 'green';
        },
        mapToColor: function(type, val) {
            if (type === 'genres') {
                const colors = ['green', 'blue', 'red', 'orange', 'purple', 'cyan', 'teal', 'light-green', 'amber', 'brown', 'blue-gray', 'indigo'];
                let charCodeSum = 0;
                for (let i = 0; i < val.length; i++) {
                    charCodeSum += val.charCodeAt(i);
                }

                return colors[charCodeSum % colors.length];
            }
            else if (type === 'caption_source') {
                return 'blue';
            }
            else if (type === 'translation_source') {
                return 'green';
            }
            else if (type === 'type') {
                if (val === 'tv') return 'blue';
                else if (val === 'movie') return 'red';
                else return 'green';
            }
            else if (type === 'new') return 'blue';
            else if (type === 'free') {
                return val ? 'green' : 'red';
            }
        },
        addFilter: function(column, rowProp, value) {
            this.removeFilter(column, rowProp, value);
            if (this.filters === null) {
                this.filters = [];
            }
            this.filters.push([column, rowProp, value]);
        },
        removeFilter: function(column, rowProp, value) {
            if (this.filters === null) return;
            this.filters = this.filters.filter(filter => {
                if (filter[0] === column && filter[1] === rowProp && filter[2] === value) return false;
                return true;
            });
            if (this.filters.length === 0) this.filters = null;
        },
        clearFilters: function() {
            this.filters = null;
        },
    }
};
</script>

<style>
.clickablebadge {
    margin-left: 2px;
    margin-bottom: 2px;
    cursor: pointer;
}

.showtable.mobile {
    margin: 0;
}
</style>

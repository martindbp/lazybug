<template>
    <div class="q-pa-md" style="display: inline-block">
        <q-table
          :rows="rows"
          :columns="columns"
          :pagination="pagination"
          :loading="isLoading"
          row-key="name"
        >
            <template v-slot:header-cell="props">
                <q-th :props="props">
                    {{ props.col.label }}
                    <span v-if="columnFilters[props.col.name] !== undefined">
                        <q-badge class="clickablebadge" @click.stop.prevent="removeFilter(...filter)" v-for="filter in columnFilters[props.col.name]" :color="mapToColor(filter[1], filter[2])">{{filter[2]}}</q-badge>
                    </span>
                </q-th>
            </template>
            <template v-slot:body-cell-name="props">
                <q-td :props="props">
                    <a :href="youtubeURL(props.row)">{{ props.value }}</a>
                </q-td>
            </template>
            <template v-slot:body-cell-difficulty="props">
                <q-td :props="props">
                    <q-badge :color="mapDifficultyToColor(props.value)">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            </template>
            <template v-slot:body-cell-douban="props">
                <q-td :props="props">
                    <span v-if="props.value === 'N/A'">N/A</span>
                    <q-badge v-else :color="mapDoubanToColor(props.value)">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            </template>
            <template v-slot:body-cell-type="props">
                <q-td :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click="addFilter('type', 'type', props.value)" :color="mapToColor('type', props.value)">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            </template>
            <template v-slot:body-cell-genres="props">
                <q-td :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click="addFilter('genres', 'genres', genre)" v-for="genre in props.value" :color="mapToColor('genres', genre)">
                        {{ genre }}
                    </q-badge>
                </q-td>
            </template>
            <template v-slot:body-cell-sources="props">
                <q-td :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click="addFilter('sources', 'caption_source', props.value[0])" :color="mapToColor('caption_source', props.value[0])">
                        {{ props.value[0] }}
                    </q-badge>
                    <q-badge class="clickablebadge" @click="addFilter('sources', 'translation_source', props.value[1])" :color="mapToColor('translation_source', props.value[1])">
                        {{ props.value[1] }}
                    </q-badge>
                </q-td>
            </template>
        </q-table>
    </div>
</template>

<script>
var roundToScale = function(n,scale) {
    return parseFloat((Math.round(n / scale) * scale).toFixed(1));
};

export default {
    data: function() { return {
        pagination: {
            rowsPerPage: 50,
        },
        columns: [
          {
            name: 'name',
            required: true,
            label: 'Name',
            align: 'left',
            field: row => row.name.en ? `${row.name.hz} | ${row.name.en}` : row.name,
            sortable: true
          },
          {
            name: 'difficulty',
            required: true,
            label: 'Difficulty',
            align: 'left',
            field: row => roundToScale(10*(row.difficulty || row.difficulty_manual), 0.1),
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'douban',
            required: true,
            label: 'Douban score',
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
            label: 'Episodes/Videos',
            align: 'left',
            field: row => row.num_processed || '-',
            format: val => `${val}`,
            sortable: true
          },
        ],
        filters: null,
    }},
    computed: {
        rows: function() {
            if (this.$store.state.showList === null) return [];
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
        youtubeURL: function(row) {
            const playlist = row.seasons[0].youtube_playlist;
            const captionId = row.seasons[0].episodes[0].id;
            const parts = captionId.split('-');
            const id = parts.slice(1).join('-');

            if ([null, undefined].includes(playlist)) {
                return `https://youtube.com/watch?v=${id}`;
            }
            else {
                return `https://youtube.com/watch?v=${id}&list=${playlist}`;
            }
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
        },
        addFilter: function(column, rowProp, value) {
            if (this.filters === null) {
                this.filters = [];
            }
            this.filters.push([column, rowProp, value]);
        },
        removeFilter: function(column, rowProp, value) {
            this.filters = this.filters.filter(filter => {
                if (filter[0] === column && filter[1] === rowProp && filter[2] === value) return false;
                return true;
            });
            if (this.filters.length === 0) this.filters = null;
        },
        clearFilters: function() {
            this.filters = null;
        }
    }
};
</script>

<style>
.clickablebadge {
    margin-left: 2px;
    margin-bottom: 2px;
    cursor: pointer;
}
</style>

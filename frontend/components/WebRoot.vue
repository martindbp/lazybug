<template>
    <div class="q-pa-md" style="display: inline-block">
        <q-table
          title="Shows"
          :rows="rows"
          :columns="columns"
          :pagination="pagination"
          :loading="isLoading"
          row-key="name-en"
        >
            <template v-slot:body-cell-difficulty="props">
                <q-td :props="props">
                    <q-rating
                      readonly
                      v-model="props.value"
                      max="3"
                      size="1em"
                      color="red-5"
                      icon="star_border"
                      icon-selected="star"
                      icon-half="star_half"
                    />
                </q-td>
            </template>
            <template v-slot:body-cell-douban="props">
                <q-td :props="props">
                    <q-badge color="green">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            </template>
        </q-table>
    </div>
</template>

<script>
var roundToScale = function(n,scale) {
    console.log(n, parseFloat((Math.round(n / scale) * scale).toFixed(1)));
    return parseFloat((Math.round(n / scale) * scale).toFixed(1));
};

export default {
    data: function() { return {
        pagination: {
            rowsPerPage: 50,
        },
        columns: [
          {
            name: 'name-en',
            required: true,
            label: 'Name',
            align: 'left',
            field: row => row.name.en ? `${row.name.en}` : row.name,
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'difficulty',
            required: true,
            label: 'Difficulty',
            align: 'left',
            field: row => roundToScale(3.5*(row.difficulty || row.difficulty_manual), 0.5),
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
            field: row => row.genres || '-',
            format: val => `${val}`,
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
        ]
    }},
    computed: {
        rows: function() {
            if (this.$store.state.showList === null) return [];
            return Object.values(this.$store.state.showList).filter((show) => show.released);
        },
        isLoading: function() {
            return this.$store.state.showList === null;
        },
    }
};
</script>

<style>
.test {
    color: blue;
}
</style>

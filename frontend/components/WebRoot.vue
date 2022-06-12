<template>
    <div class="q-pa-md" style="width: 50%; left: 25%; position: absolute; min-width: 500px;">
        <q-table
          title="Shows"
          :rows="rows"
          :columns="columns"
          :pagination="pagination"
          row-key="name-en"
        />
    </div>
</template>

<script>
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
            field: row => row.name.en || row.name,
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'name-zh',
            required: true,
            label: 'Hanzi',
            align: 'left',
            field: row => row.name.hz || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'name-py',
            required: true,
            label: 'Pinyin',
            align: 'left',
            field: row => row.name.py || '-',
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
        ]
    }},
    computed: {
        rows: function() {
            if (this.$store.state.showList === null) return [];
            return Object.values(this.$store.state.showList).filter((show) => show.released);
        },
    }
};
</script>

<style>
.test {
    color: blue;
}
</style>

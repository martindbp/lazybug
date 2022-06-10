<template>
    <div class="q-pa-md" style="width: 50%; left: 25%; position: absolute; min-width: 500px;">
        <q-card v-for="show in showList">
            {{ show }}
        </q-card>
    </div>
</template>

<script>
export default {
    computed: {
        showList: function() {
            return this.$store.state.showList;
        },
    }
};
</script>

<style>
.test {
    color: blue;
}
</style>

<template>
    <q-slider
        color="teal"
        v-model="hideWordsLevel"
        :min="0"
        :max="7"
        :step="1"
        :label-value="hideWordsLevel < 7 ? hideWordsLevel : 'all'"
        label
        snap
        markers
    />
</template>

<script>
export default {
    computed: {
        hideWordsLevel: {
            get: function() {
                return this.$store.state.options.hideWordsLevel;
            },
            set: function(val) {
                this.$store.commit('setOption', {key: 'hideWordsLevel', value: val});
            },
        },
    },
}
</script>
<style>
</style>

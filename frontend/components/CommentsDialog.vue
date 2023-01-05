<template>
    <q-dialog seamless v-model="show" dark>
        <q-card dark style="width: 600px" class="q-px-sm q-pb-md">
            <q-card-section align="center">
                <q-card v-for="comment in comments">
                    {{ comment.cooked }}
                </q-card>
            </q-card-section>
            <q-card-actions align="right" class="text-teal">
                <q-btn flat label="OK" @click="show = false"></q-btn>
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script>

export default {
    mixins: [mixin],
    props: ['comments'],
    components: { },
    computed: {
        show: {
            get: function() { return this.$store.state.showDialog.comments; },
            set: function(val) { this.$store.commit('setShowDialog', {dialog: 'comments', val: val}); },
        },
    }
}
</script>
<style>
</style>

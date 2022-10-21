<template>
    <q-dialog seamless persistent position="bottom" v-model="show">
        <q-card>
            Devtools
            <q-btn flat label="OK" @click="show = false"></q-btn>
        </q-card>
    </q-dialog>
</template>

<script>


export default {
    mixins: [mixin],
    data: function() { return {
        keyboardListener: null,
    }},
    computed: {
        show: {
            get: function() { return this.$store.state.showDialog.devtools; },
            set: function(val) { this.$store.commit('setShowDialog', {dialog: 'devtools', val: val}); },
        },
    },
    mounted: function() {
        const self = this;
        this.keyboardListener = window.addEventListener("keydown", function(event) {
            const shift = event.getModifierState("Shift");
            const ctrl = event.getModifierState("Control");
            const alt = event.getModifierState("Alt");
            if (shift && ctrl && alt && event.key === 'D') {
                self.show = true;
            }
        }, {capture: true});
    },
    beforeDestroy: function() {
        window.removeEventListener('keydown', this.keyboardListener);
    },
    watch: {
    },
    methods: {
    },
}
</script>
<style>
</style>

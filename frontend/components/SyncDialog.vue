<template>
    <q-dialog seamless v-model="$store.state.showSyncDialog">
        <q-card>
            <q-card-section>
                <div class="text-h6">Syncing Data</div>
            </q-card-section>
            <q-linear-progress v-if="$store.state.isSyncing" indeterminate color="secondary" class="q-mt-sm" />
            <q-linear-progress v-else value="1.0" color="green" class="q-mt-sm" />
            <q-card-section>
                <q-scroll-area style="height: 200px; width: 400px; max-width: 400px">
                    <div :key="message" v-for="message in $store.state.syncProgress">
                        * {{ message }}
                    </div>
                </q-scroll-area>
            </q-card-section>

            <q-card-section class="text-h7 text-red text-center" v-if="$store.state.syncError">
                Something went wrong: {{ $store.state.syncError }}
            </q-card-section>
            <q-card-section class="text-h7 text-center" v-else-if="$store.state.isSyncing">
                Processing...
            </q-card-section>
            <q-card-section class="text-h7 text-green text-center" v-else>
                DONE
            </q-card-section>

            <q-card-actions align="right">
                <q-btn v-if="! $store.state.isSyncing || $store.state.syncError" flat label="OK" color="primary" v-close-popup />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script>
export default {
    mixins: [mixin],
};
</script>

<style>
</style>

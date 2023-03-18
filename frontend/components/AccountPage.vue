<template>
    <div class="q-pa-md" style="margin-left: 25px; margin-top: 25px;">
        <div class="q-pa-md row items-start q-gutter-md">
            <q-card class="accountcard">
                <q-card-section>
                    <div class="text-h6">Account</div>
                    <span v-if="$store.state.accountEmail" class="text-subtitle2 text-left">{{ $store.state.accountEmail }}</span>
                </q-card-section>

                <q-separator />

                <q-card-actions vertical v-if="$store.state.accessToken">
                    <q-btn color="green" flat @click="showModalAndSync()">Sync Cloud</q-btn>
                    <q-btn color="red" flat @click="logout">Logout</q-btn>
                    <q-btn v-if="$store.state.syncProgress.length > 0" color="gray" flat @click="$store.commit('setShowDialog', {dialog: 'sync', value: true})">Show Sync Log</q-btn>
                </q-card-actions>
                <q-card-actions v-else>
                    <q-btn color="primary" flat @click="register">Register</q-btn>
                    <q-btn flat @click="login">Login</q-btn>
                    <q-btn v-if="$store.state.syncProgress.length > 0" color="gray" flat @click="$store.commit('setShowDialog', {dialog: 'sync', value: true})">Show Sync Log</q-btn>
                </q-card-actions>

                <q-separator />

                <q-card-actions vertical>
                    <q-checkbox v-model="okReceiveEmails" label="OK to receive occasional email updates" />
                </q-card-actions>

                <q-separator />

                <q-card-actions vertical>
                    <q-btn color="primary" flat @click="showIntro">Show Intro</q-btn>
                </q-card-actions>
            </q-card>
            <q-card class="accountcard">
                <q-card-section>
                    <div class="text-h6">Local Data (v{{ latestDbVersion }})</div>
                </q-card-section>

                <q-separator />
                <q-card-actions vertical>
                    <q-btn color="green" flat @click="exportDb">Download</q-btn>
                    <q-btn flat @click="importDb">Restore from File</q-btn>
                </q-card-actions>

                <q-separator />

                <q-card-actions vertical>
                    <q-btn color="orange" flat @click="clearCache" :disabled="clickedClearCache" >Clear Cache</q-btn>
                    <q-btn color="red" flat @click="confirmClearPersonalData = true" :disabled="clickedClearPersonalData">Clear Personal Data</q-btn>
                </q-card-actions>
            </q-card>
        </div>
        <q-dialog seamless v-model="confirmClearPersonalData">
            <q-card>
                <q-card-section class="row items-center">
                    <span class="q-ml-sm">Are you sure? This will delete your local data permanently.</span>
                </q-card-section>

                <q-card-actions align="right">
                    <q-btn flat label="Cancel" color="primary" v-close-popup />
                    <q-btn flat label="Delete" color="red" v-close-popup @click="clearPersonalData" />
                </q-card-actions>
            </q-card>
        </q-dialog>
    </div>
</template>

<script>

export default {
    mixins: [mixin],
    data: function() { return {
        clickedClearCache: false,
        confirmClearPersonalData: false,
        clickedClearPersonalData: false,
    }},
    computed: {
        okReceiveEmails: {
            get: function() {
                return this.$store.state.options.okReceiveEmails;
            },
            set: function(val) {
                this.$store.commit('setOption', {key: 'okReceiveEmails', value: val});
            },
        },
        latestDbVersion: function() {
            return getLatestDbVersion();
        },
    },
    methods: {
        showIntro: function() {
            this.$store.commit('setShowDialog', { dialog: 'intro', value: true });
        },
        clearCache: function() {
            clearCache();
            this.clickedClearCache = true;
        },
        clearDataThenCall(confirmCallback) {
            const self = this;
            isPersonalDbEmpty(function(isEmpty) {
                if (isEmpty) {
                    confirmCallback(true);
                }
                else {
                    self.$q.dialog({
                        title: 'Confirm',
                        message: 'There is local data changes that will be overwritten, continue?',
                        cancel: true,
                    }).onOk(() => {
                        clearPersonalData(function() {
                            confirmCallback(true);
                        });
                    }).onCancel(() => {
                        confirmCallback(false);
                    });
                }
            });
        },
        register: function() {
            this.$store.commit('setShowDialog', {dialog: 'account', value: 'register'});
        },
        login: function() {
            const self = this;
            this.clearDataThenCall(function(confirm) {
                if (confirm) {
                    self.$store.commit('setShowDialog', {dialog: 'account', value: 'login'});
                }
            });
        },
        logout: function() {
            const self = this;
            this.showModalAndSync(true, function(error) {
                self.$store.commit('addSyncProgress', 'Clearing IndexedDB');
                clearPersonalData(function() {
                    self.$store.commit('addSyncProgress', 'Logging out of Discourse');
                    fetch('/api/discourse/logout', {
                        method: 'POST',
                        headers: new Headers({
                            'Authorization': 'Bearer ' + self.$store.state.accessToken,
                            'Content-Type': 'application/x-www-form-urlencoded'
                        }),
                    })
                    .catch((error) => {
                        self.$store.commit('addSyncProgress', 'Discourse logout error:', error);
                    })
                    .then(() => {
                        self.$store.commit('setLoggedOut');
                    });
                });
            });
        },
        clearPersonalData: function() {
            const self = this;
            clearPersonalData(function() {
                self.clickedClearPersonalData = true;
                self.$store.commit('setLastSyncDate', null);
            });
        },
        exportDb: function() {
            const self = this;
            exportDatabaseJson(function(data) {
                const filename = `database-v${self.latestDbVersion}-${(new Date(Date.now())).toISOString().split('T')[0]}.json`;
                download(filename, JSON.stringify(data));
            });
        },
        importDb: function() {
            var fileChooser = document.createElement("input");
            fileChooser.style.display = 'none';
            fileChooser.type = 'file';

            const self = this;
            fileChooser.addEventListener('change', function (evt) {
                var f = evt.target.files[0];
                if(f) {
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        const data = JSON.parse(e.target.result);
                        importDatabaseJson(data, self.$store, function(error) {
                            if (! [null, undefined].includes(error)) {
                                self.$q.dialog({
                                    title: 'ERROR',
                                    message: 'Something went wrong importing database: ' + error + '. Take a screenshot and report the problem in the Discourse forum (go to "Discuss")',
                                });
                            }
                            else {
                                self.$store.commit('setLastSyncDate', null);
                                self.$store.commit('setNeedSync', true);
                                self.$q.dialog({
                                    title: 'Success',
                                    message: 'Database successfully imported from file',
                                });
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
.accountcard {
    min-width: 275px;
}
</style>

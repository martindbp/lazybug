<template>
    <div class="q-pa-md" style="margin-left: 25px; margin-top: 25px;">
        <div class="q-pa-md row items-start q-gutter-md">
            <q-card>
                <q-card-section>
                    <div class="text-h6">Account</div>
                    <div v-if="$store.state.accountEmail" class="text-subtitle2">{{ $store.state.accountEmail }}</div>
                </q-card-section>

                <q-separator />

                <q-card-actions vertical v-if="$store.state.accessToken">
                    <q-btn color="green" flat @click="showModalAndSync">Sync Cloud</q-btn>
                    <q-btn color="red" flat @click="logout">Logout</q-btn>
                </q-card-actions>
                <q-card-actions v-else>
                    <q-btn color="primary" flat @click="register">Register</q-btn>
                    <q-btn flat @click="login">Login</q-btn>
                </q-card-actions>
            </q-card>
            <q-card>
                <q-card-section>
                    <div class="text-h6">Backup or Restore</div>
                    <div class="text-subtitle2">Download data file or restore from file</div>
                </q-card-section>

                <q-separator />

                <q-card-actions vertical>
                    <q-btn color="green" flat @click="exportDb">Download</q-btn>
                    <q-btn flat @click="importDb">Restore from File</q-btn>
                </q-card-actions>
            </q-card>

            <q-card>
                <q-card-section>
                    <div class="text-h6">Clear Local Data</div>
                </q-card-section>

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
    methods: {
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
            this.$store.commit('setShowAccountDialog', 'register');
        },
        login: function() {
            const self = this;
            this.clearDataThenCall(function(confirm) {
                if (confirm) {
                    self.$store.commit('setShowAccountDialog', 'login');
                }
            });
        },
        logout: function() {
            const self = this;
            this.showModalAndSync(true, function(error) {
                clearPersonalData(function() {
                    self.$store.commit('setLogout');
                });
            });
        },
        clearPersonalData: function() {
            const self = this;
            clearPersonalData(function() {
                self.clickedClearPersonalData = true;
            });
        },
        exportDb: function() {
            exportDatabaseJson(function(data) {
                const filename = `database-v${VERSION}-${(new Date(Date.now())).toISOString().split('T')[0]}.json`;
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
                                alert('Something went wrong: ' + error);
                            }
                            else {
                                alert('Successfully imported database');
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
</style>

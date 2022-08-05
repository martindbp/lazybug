<template>
    <div class="q-pa-md" style="width: 50%; margin-left: 50px; margin-top: 50px; min-width: 500px;">
        <q-btn color="secondary" label="Clear cache" @click="clearCache" :disabled="clickedClearCache" />
        <br>
        <br>
        <q-btn color="deep-orange" label="Clear database" @click="confirmClearPersonalData = true" :disabled="clickedClearPersonalData" />
        <br>
        (Will permanently delete personal data)
        <br>
        <br>
        <q-btn color="green" label="Download database backup" @click="exportDb" />
        <br>
        <br>
        <q-btn color="blue" label="Restore database from backup" @click="importDb" />

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
const ROWS_PER_PAGE = 4;

export default {
    mixins: [mixin],
    data: function() { return {
        clickedClearCache: false,
        confirmClearPersonalData: false,
        clickedClearPersonalData: false,
    }},
    watch: {
    },
    methods: {
        clearCache: function() {
            clearCache();
            this.clickedClearCache = true;
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

            fileChooser.addEventListener('change', function (evt) {
                var f = evt.target.files[0];
                if(f) {
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        const data = JSON.parse(e.target.result);
                        importDatabaseJson(data, function(error) {
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

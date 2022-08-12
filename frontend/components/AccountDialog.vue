<template>
    <q-dialog seamless v-model="show" class="fixdialogheight">
        <q-card class="q-px-sm q-pb-md">
            <q-tabs
              v-model="tab"
              dense
              class="shadow-2"
            >
                <q-tab name="login" label="Login" />
                <q-tab name="register" label="Register" />
            </q-tabs>

            <q-tab-panels v-model="tab">
                <q-tab-panel name="login">
                    Please enter your email and password:
                    <q-input v-model="email" filled type="email" hint="Email" />
                    <br>
                    <q-input v-model="password" filled type="password" hint="Password" />
                    <div class="accounterror" v-if="error">{{ error }}</div>
                </q-tab-panel>
                <q-tab-panel name="register">
                    Please enter desired email and password:
                    <q-input v-model="email" filled type="email" hint="Email" />
                    <br>
                    <q-input v-model="password" filled type="password" hint="Password" />
                    <div class="accounterror" v-if="error">{{ error }}</div>
                </q-tab-panel>
            </q-tab-panels>
            <q-card-actions align="right" class="text-teal absolute-bottom">
                <q-btn flat label="Close" v-close-popup></q-btn>
                <q-btn v-if="tab === 'login'" :loading="loading" flat color="primary" label="Login" @click="clickLogin"></q-btn>
                <q-btn v-else :loading="loading" flat color="primary" label="Register" @click="clickRegister"></q-btn>
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script>
export default {
    components: { },
    data: function() { return {
        tab: Vue.ref('login'),
        email: '',
        password: '',
        loading: false,
        error: null,
    }},
    computed: {
        show: {
            get: function() { return this.$store.state.showAccountDialog !== false; },
            set: function(val) { this.$store.commit('setShowAccountDialog', val); },
        },
        showAccountDialog: {
            get: function() { return this.$store.state.showAccountDialog; },
        },
    },
    watch: {
        showAccountDialog: function() {
            if (this.show !== false) {
                this.tab = this.$store.state.showAccountDialog;
            }
        }
    },
    methods: {
        clickLogin: function() {
            this.loading = true;
            const self = this;

            login(this.email, this.password, function(res, error) {
                self.loading = false;
                if (error) {
                    self.error = Array.isArray(error.detail) ? error.detail.map((error) => error.msg).join('\n') : error.detail;
                }
                else if (res) {
                    self.$store.commit('setAccessToken', res.access_token);
                    self.show = false;
                    self.password = '';
                }
            });
        },
        clickRegister: function() {
            this.loading = true;
            const self = this;

            register(this.email, this.password, function(error) {
                self.loading = false;
                if (error) {
                    self.error = Array.isArray(error.detail) ? error.detail.map((error) => error.msg).join('\n') : error.detail;
                }
                else {
                    self.show = false;
                    self.password = '';
                }
            });
        },
    },
}
</script>
<style>
.fixdialogheight .q-panel {
    height: 300px !important;
    width: 400px;
}

.fixdialogheight .q-panel > div {
    height: 300px !important;
    width: 400px;
}

.accounterror {
    margin-top: 10px;
    color: red;
}
</style>

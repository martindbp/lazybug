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
                    <form>
                        <q-input ref="loginEmail" v-model="email" filled type="email" hint="Email" />
                        <br>
                        <q-input ref="loginPassword" v-model="password" filled type="password" hint="Password" />
                        <div class="accounterror" v-if="error">{{ error }}</div>
                    </form>
                </q-tab-panel>
                <q-tab-panel name="register">
                    Please enter desired email and password:
                    <form>
                        <q-input ref="registerEmail" v-model="email" filled type="email" hint="Email" />
                        <br>
                        <q-input ref="registerPassword" v-model="password" filled type="password" hint="Password" />
                        <div class="accounterror" v-if="error">{{ error }}</div>
                    </form>
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
    mixins: [mixin],
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
            get: function() {
                return this.$store.state.showDialog.account !== false;
            },
            set: function(val) {
                this.$store.commit('setShowDialog', {dialog: 'account', val: val});
            },
        },
    },
    watch: {
        show: function() {
            if (this.show !== false) {
                this.tab = this.$store.state.showDialog.account;
                const self = this;
                // Need to delay this further as nextTick is not enough
                setTimeout(function() {
                    self.focus();
                }, 50);
            }
        },
        tab: function() {
            this.error = null;
            this.focus();
        },
    },
    methods: {
        focus: function() {
            const self = this;
            this.$nextTick(() => {
                if (self.tab === 'login') self.$refs.loginEmail.focus();
                else self.$refs.registerEmail.focus();
            });
        },
        clickLogin: function() {
            this.loading = true;
            const self = this;

            login(this.email, this.password, function(res, error) {
                self.loading = false;
                if (error) {
                    self.error = error
                    if (typeof error === 'object') {
                        self.error = Array.isArray(error.detail) ? error.detail.map((error) => error.msg).join('\n') : error.detail;
                    }

                    if (self.error === 'LOGIN_BAD_CREDENTIALS') self.error = 'Email or password was incorrect';
                }
                else if (res) {
                    self.$store.commit('setLogin', {accessToken: res.access_token, email: self.email });
                    self.show = false;
                    self.password = '';
                    self.showModalAndSync(true);
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
                    self.clickLogin();
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

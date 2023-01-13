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
                    <form>
                        <div v-show="sentPasswordResetEmail === false">
                            <q-input ref="loginEmail" v-model="email" filled type="email" hint="Email" @keydown.enter.prevent="submit" />
                            <br>
                        </div>
                        <q-input ref="loginPassword" v-model="password" filled type="password" hint="Password" @keydown.enter.prevent="submit" />
                        <div v-if="sentPasswordResetEmail" >
                            <br>
                            <q-input ref="resetPasswordTokenInput" v-model="passwordResetToken" filled type="text" hint="Password Reset Code" @keydown.enter.prevent="submit" />
                        </div>
                        <div class="accountmessage" v-if="sentPasswordResetEmail === true">A reset code has been sent, copy and paste it above</div>
                        <div class="accountmessage" v-if="sentPasswordResetEmail === 'loading'">Sending an email, hang on...</div>
                        <div class="accounterror" v-if="error">{{ error }}</div>
                    </form>
                </q-tab-panel>
                <q-tab-panel name="register">
                    Enter desired email and password:
                    <form>
                        <q-input ref="registerEmail" v-model="email" filled type="email" hint="Email" @keydown.enter.prevent="submit" />
                        <br>
                        <q-input ref="registerPassword" v-model="password" filled type="password" hint="Password" @keydown.enter.prevent="submit" />
                        <div class="accounterror" v-if="error">{{ error }}</div>
                    </form>
                </q-tab-panel>
            </q-tab-panels>
            <q-card-actions align="right" class="text-teal absolute-bottom">
                <div v-if="tab === 'login'">
                    <q-btn v-if="!sentPasswordResetEmail" :loading="loading === 'forgot'" flat color="deep-orange" label="Forgot Password" @click="clickForgotPassword"></q-btn>
                    <q-btn v-if="sentPasswordResetEmail" :loading="loading === 'reset'" flat color="primary" label="Reset Password" @click="clickResetPassword"></q-btn>
                </div>
                <q-btn flat label="Close" v-close-popup></q-btn>
                <div v-if="tab === 'login'">
                    <q-btn v-if="sentPasswordResetEmail === false" :loading="loading === 'login'" flat color="primary" label="Login" @click="clickLogin"></q-btn>
                </div>
                <q-btn v-else :loading="loading === 'register'" flat color="primary" label="Register" @click="clickRegister"></q-btn>
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
        passwordResetToken: null,
        sentPasswordResetEmail: false,
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
        show: {
            immediate: true,
            handler: function() {
                if (this.show !== false) {
                    this.tab = this.$store.state.showDialog.account;
                    const self = this;
                    // Need to delay this further as nextTick is not enough
                    setTimeout(function() {
                        self.focus();
                    }, 50);
                }
            },
        },
        tab: function() {
            this.error = null;
            this.focus();
        },
    },
    methods: {
        clickResetPassword: function() {
            this.error = null;
            if (this.password.length === 0) {
                this.error = 'You need to a new password to reset'
                return;
            }

            this.sentPasswordResetEmail = false;
            this.loading = 'reset';
            const self = this;
            fetch('/api/auth/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: this.passwordResetToken,
                    password: this.password,
                }),
            })
            .catch((error) => {
                self.error = `Something went wrong: ${error}`;
                self.loading = false;
            })
            .then(() => {
                self.passwordResetToken = null;
                self.loading = false;
                self.$q.dialog({
                    title: 'Success!',
                    message: 'Your password has been successfully changed',
                }).onOk(() => {
                    self.clickLogin();
                });
            });
        },
        clickForgotPassword: function() {
            this.error = null;
            if (this.email.length === 0) {
                this.error = 'You need to provide an email to request new password'
                return;
            }

            this.loading = 'forgot';
            this.sentPasswordResetEmail = 'loading';
            const self = this;
            fetch('/api/auth/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.email
                }),
            })
            .then((data) => {
                self.sentPasswordResetEmail = true;
                self.loading = false;
            })
            .catch((error) => {
                self.error = error;
                self.loading = false;
                self.sentPasswordResetEmail = false;
            });
        },
        focus: function() {
            const self = this;
            this.$nextTick(() => {
                if (self.tab === 'login') self.$refs.loginEmail.focus();
                else self.$refs.registerEmail.focus();
            });
        },
        submit: function() {
            if (this.tab === 'login') this.clickLogin();
            else if (this.tab === 'register') this.clickRegister();
        },
        clickLogin: function() {
            this.loading = 'login';
            this.error = null;
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
            this.loading = 'register';
            this.error = null;
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

.accountmessage {
    margin-top: 10px;
    color: black;
}
</style>

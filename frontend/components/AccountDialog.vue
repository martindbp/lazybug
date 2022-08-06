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
                    <q-input v-model="email" filled type="email" hint="Email" />
                    <br>
                    <q-input v-model="password" filled type="password" hint="Password" />
                    <div v-if="error">{{ error }}</div>
                </q-tab-panel>
                <q-tab-panel name="register">
                    <q-input v-model="email" filled type="email" hint="Email" />
                    <br>
                    <q-input v-model="password" filled type="password" hint="Password" />
                    <div v-if="error">{{ error }}</div>
                </q-tab-panel>
            </q-tab-panels>
            <q-card-actions align="right" class="text-teal absolute-bottom">
                <q-btn flat label="Close" v-close-popup></q-btn>
                <q-btn v-if="tab === 'login'" flat color="primary" v-close-popup label="Login" @click="clickLogin"></q-btn>
                <q-btn v-else flat color="primary" v-close-popup label="Register" @click="clickRegister"></q-btn>
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
            get: function() { return this.$store.state.showAccountDialog; },
            set: function(val) { this.$store.commit('setShowAccountDialog', val); },
        },
    },
    methods: {
        clickLogin: function() {
            this.loading = true;
            const self = this;
            fetch('http://localhost/auth/jwt/login', {
                method: 'POST',
                headers:{
                  'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'username': this.email,
                    'password': this.password,
                })
            }).then(function(res) {
                self.loading = false;
            }).catch((error) => {
                self.loading = false;
                self.error = error;
            });
        },
        clickRegister: function() {
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
</style>

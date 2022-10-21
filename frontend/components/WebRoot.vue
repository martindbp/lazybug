<template>
    <div>
        <q-layout view="lHh Lpr lff" container class="shadow-2 rounded-borders">
           <q-header v-if="isMobile" elevated class="bg-blue">
               <q-toolbar>
                   <q-btn flat @click="drawer = !drawer" round dense icon="menu" />
                   <q-toolbar-title>Lazybug - {{pageTitle}}</q-toolbar-title>
               </q-toolbar>
           </q-header>

          <q-drawer
            v-model="drawer"
            show-if-above
            bordered
            :behavior="mobile"
            :width="200"
            style="text-align: left;"
            class="bg-grey-3"
          >
              <q-scroll-area style="border-right: 1px solid #ddd">
              <q-img src="/static/images/lazybug_sanstext.svg" width="250" style="margin-top: 15px; margin-bottom: 15px; margin-left: -25px; vertical-align: middle; filter: drop-shadow(5px 5px 5px rgba(0,0,0,0.5))" />
              <q-list padding>
                <q-item v-if="$store.state.playingShowId" :active="page === 'player'" clickable @click="clickPage('player')" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="tv" />
                  </q-item-section>

                  <q-item-section>
                    Player
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'content'" clickable @click="clickPage('content')" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="list" />
                  </q-item-section>

                  <q-item-section>
                    Content
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'history'" clickable @click="clickPage('history')" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="history" />
                  </q-item-section>

                  <q-item-section>
                    History
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'star'" clickable @click="clickPage('star')" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="star" />
                  </q-item-section>

                  <q-item-section>
                    Starred
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'discuss'" clickable @click="clickDiscuss" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="forum" />
                  </q-item-section>

                  <q-item-section>
                    Discuss
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'account'" clickable @click="clickPage('account')" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="account_circle" />
                  </q-item-section>

                  <q-item-section>
                    Account
                  </q-item-section>
                </q-item>

                <q-item v-if="$store.state.accessToken && $store.state.needSync">
                    <q-btn color="green" flat @click="showModalAndSync">Sync Changes</q-btn>
                </q-item>
              </q-list>


            </q-scroll-area>
          </q-drawer>

          <q-page-container :class="{nopadding: page === 'player' && isMobile}" >
            <q-page :padding="page !== 'player' && isDesktop">
                <PlayerPage v-show="page === 'player'" /> <!-- use v-show to keep alive video iframe -->
                <ShowTable v-show="page === 'content'" />
                <HistoryPage v-show="page === 'history'" />
                <StarTable v-show="page === 'star'" />
                <AccountPage v-show="page === 'account'" />
            </q-page>
          </q-page-container>
        </q-layout>

        <q-dialog seamless v-model="showNonEmbeddableDialog">
            <q-card>
                <q-card-section class="row items-center">
                    <span class="q-ml-sm">This show can't be embedded in this web app</span>
                </q-card-section>

                <q-card-actions align="right">
                    <q-btn flat label="Cancel" color="primary" v-close-popup />
                    <q-btn flat label="Go to external video (new tab)" color="green" v-close-popup @click="goExternal" />
                </q-card-actions>
            </q-card>
        </q-dialog>
        <AccountDialog />
        <SyncDialog />
    </div>
</template>

<script>
import ShowTable from './ShowTable.vue'
import StarTable from './StarTable.vue'
import AccountPage from './AccountPage.vue'
import PlayerPage from './PlayerPage.vue'
import HistoryPage from './HistoryPage.vue'
import AccountDialog from './AccountDialog.vue'
import SyncDialog from './SyncDialog.vue'

export default {
    mixins: [mixin],
    components: {
        ShowTable,
        StarTable,
        AccountPage,
        PlayerPage,
        HistoryPage,
        AccountDialog,
        SyncDialog,
    },
    data: function() { return {
        drawer: this.isDesktop,
    }},
    methods: {
        clickPage: function(page) {
            this.$store.commit('setPage', page);
            if (this.isMobile) this.drawer = false; // close after tap if on mobile
        },
        clickDiscuss: function() {
            const self = this;
            if (this.$store.state.accessToken === null) {
                this.showAccountModalWithCallback(function() {
                    document.location = DISCOURSE_URL;
                });
            }
            else {
                document.location = DISCOURSE_URL;
            }
        },
    },
    computed: {
        page: {
            get: function() { return this.$store.state.page; },
            set: function(val) { this.$store.commit('setPage', val); },
        },
        pageTitle: function() {
            return this.page[0].toUpperCase() + this.page.substring(1);
        },
        showNonEmbeddableDialog: {
            get: function() { return this.$store.state.showDialog.embeddable; },
            set: function(val) { this.$store.commit('setShowDialog', {dialog: 'embeddable', value: val}); },
        },
    },
};
</script>

<style>
.q-page-container.nopadding {
    padding-top: 0px !important;
}
</style>

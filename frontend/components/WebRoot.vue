<template>
    <div>
        <q-layout view="lHh Lpr lff" container class="shadow-2 rounded-borders">
          <q-drawer
            v-model="drawer"
            show-if-above
            bordered
            :width="200"
            :breakpoint="400"
            style="text-align: left;"
            class="bg-grey-3"
          >
            <q-scroll-area style="border-right: 1px solid #ddd">
              <q-img src="/static/images/lazybug_sanstext.svg" width="250" style="margin-top: 15px; margin-bottom: 15px; margin-left: -25px; vertical-align: middle; filter: drop-shadow(5px 5px 5px rgba(0,0,0,0.5))" />
              <q-list padding>
                <q-item v-if="$store.state.playerShowInfo" :active="page === 'player'" clickable @click="page = 'player'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="tv" />
                  </q-item-section>

                  <q-item-section>
                    Player
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'content'" clickable @click="page = 'content'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="list" />
                  </q-item-section>

                  <q-item-section>
                    Content
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'history'" clickable @click="page = 'history'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="history" />
                  </q-item-section>

                  <q-item-section>
                    History
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'star'" clickable @click="page = 'star'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="star" />
                  </q-item-section>

                  <q-item-section>
                    Starred
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'account'" clickable @click="page = 'account'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="account_circle" />
                  </q-item-section>

                  <q-item-section>
                    Account
                  </q-item-section>
                </q-item>

              </q-list>

            </q-scroll-area>
          </q-drawer>

          <q-page-container>
            <q-page :padding="page !== 'player'">
                <PlayerPage v-show="page === 'player'" /> <!-- use v-show to keep alive video iframe -->
                <ShowTable v-if="page === 'content'" />
                <HistoryPage v-if="page === 'history'" />
                <StarTable v-if="page === 'star'" />
                <AccountPage v-if="page === 'account'" />
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
                    <q-btn flat label="Go to Youtube (new tab)" color="green" v-close-popup @click="goYoutube" />
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
    },
    computed: {
        page: {
            get: function() { return this.$store.state.webPage; },
            set: function(val) { this.$store.commit('setWebPage', val); },
        },
        showNonEmbeddableDialog: {
            get: function() { return this.$store.state.showNonEmbeddableDialog; },
            set: function(val) { this.$store.commit('setShowNonEmbeddableDialog', val); },
        },
    },
};
</script>

<style>
</style>

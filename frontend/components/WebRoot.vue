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
              <q-img src="images/lazybug_sanstext.svg" width="250" style="margin-top: 15px; margin-bottom: 15px; margin-left: -25px; vertical-align: middle; filter: drop-shadow(5px 5px 5px rgba(0,0,0,0.5))" />
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

                <q-item :active="page === 'settings'" clickable @click="page = 'settings'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="settings" />
                  </q-item-section>

                  <q-item-section>
                    Settings
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'help'" clickable @click="page = 'help'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="help" />
                  </q-item-section>

                  <q-item-section>
                    Help
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
                <Settings v-if="page === 'settings'" />
            </q-page>
          </q-page-container>
        </q-layout>
    </div>
</template>

<script>
import ShowTable from './ShowTable.vue'
import StarTable from './StarTable.vue'
import Settings from './Settings.vue'
import PlayerPage from './PlayerPage.vue'
import HistoryPage from './HistoryPage.vue'

export default {
    components: {
        ShowTable,
        StarTable,
        Settings,
        PlayerPage,
        HistoryPage,
    },
    computed: {
        page: {
            get: function() { return this.$store.state.webPage; },
            set: function(val) { this.$store.commit('setWebPage', val); },
        },
    }
};
</script>

<style>
#webroot {
    /*text-align: center;*/
}
</style>

<template>
    <div v-if="applicationReady">
        <q-layout view="lHh Lpr lff" container class="shadow-2 rounded-borders">
           <q-header v-if="isMobile" elevated class="bg-blue">
               <q-toolbar>
                   <q-btn flat @click="drawer = !drawer" round dense icon="menu" />
                   <q-toolbar-title>{{pageTitle}}</q-toolbar-title>
               </q-toolbar>
           </q-header>

          <q-drawer
            v-model="drawer"
            show-if-above
            :behavior="mobile"
            :width="200"
            style="text-align: left; overflow: hidden !important"
            :class="{ 'bg-grey-3': !mini, 'bg-grey-10': mini }"
            :mini="mini"
            :mini-to-overlay="! this.isMobile && page === 'player'"
            @mouseover="mouseOverDrawer = true"
            @mouseout="mouseOverDrawer = false"
          >
              <q-img
                  @click="clickPage('content')"
                  src="/static/images/lazybug_sanstext.svg"
                  class="logoimg"
                  :width="mini ? 0 : 250"
              />
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

                <q-item :active="page === 'words'" clickable @click="clickPage('words')" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="star" />
                  </q-item-section>

                  <q-item-section>
                    Words
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

                <q-item :active="page === 'about'" clickable @click="clickAbout()" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="info" />
                  </q-item-section>

                  <q-item-section>
                    About
                  </q-item-section>
                </q-item>

                <q-item v-if="$store.state.accessToken && $store.state.needSync">
                    <q-btn color="green" flat @click="showModalAndSync">{{ mini ? 'Sync' : 'Sync Changes' }}</q-btn>
                </q-item>
              </q-list>
          </q-drawer>

          <q-page-container :class="{nopadding: page === 'player' && isMobile}" >
            <q-page :padding="page !== 'player' && isDesktop">
                <PlayerPage v-show="page === 'player'" /> <!-- use v-show to keep alive video iframe -->
                <ShowTable v-show="page === 'content'" />
                <HistoryPage v-if="page === 'history'" />
                <WordTable v-if="page === 'words'" />
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
        <IntroDialog />

        <!--
            Add an iframe to Discourse if we log in to automatically log in there as well
            so that we can fetch comments from here right away
        -->
        <iframe
            ref="discourseIframe"
            v-if="!$store.state.isLocal && $store.state.loggedInThisSession"
            @load="onIframeLoaded()"
            :src="discourseURL"
            hidden
        />
    </div>
</template>

<script>
import ShowTable from './ShowTable.vue'
import WordTable from './WordTable.vue'
import AccountPage from './AccountPage.vue'
import PlayerPage from './PlayerPage.vue'
import HistoryPage from './HistoryPage.vue'
import AccountDialog from './AccountDialog.vue'
import SyncDialog from './SyncDialog.vue'
import IntroDialog from './IntroDialog.vue'

export default {
    mixins: [mixin],
    components: {
        ShowTable,
        WordTable,
        AccountPage,
        PlayerPage,
        HistoryPage,
        AccountDialog,
        SyncDialog,
        IntroDialog,
    },
    data: function() { return {
        drawer: this.isDesktop,
        iframeLoaded: false,
        inactivityTimer: null,
        mouseOverDrawer: false,
    }},
    mounted: function() {
        const self = this;

        // Set up timers to sync data if we've been inactive for a long time
        // NOTE: turning this off for now, may be a bug where a failed sync wipes the local database
        // Also focus/blur events don't seem to trigger correctly
        /*
        window.onfocus = function() {
            if (self.inactivityTimer) {
                clearTimeout(self.inactivityTimer);
                self.inactivityTimer = null;
            }
        }
        window.onblur = function() {
            if (self.inactivityTimer) {
                clearTimeout(self.inactivityTimer);
                self.inactivityTimer = null;
            }

            self.inactivityTimer = setTimeout(function() {
                if (self.$store.state.needSync && self.$store.state.accountEmail) {
                    self.showModalAndSync(true);
                }
            }, 60*60*1000); // 1 hour
        }
        */
    },
    methods: {
        onIframeLoaded: function() {
            if (this.iframeLoaded) return;
            this.iframeLoaded = true;
            // Reload iframe since the first time we could be stuck in "You've logged out", and SSO is never initiated
            this.$refs.discourseIframe.src = DISCOURSE_LOGIN_URL;
        },
        clickAbout: function() {
            window.open('https://github.com/martindbp/lazybug#readme', '_blank');
        },
        clickPage: function(page) {
            this.$store.commit('setPage', page);
            if (this.isMobile) this.drawer = false; // close after tap if on mobile
        },
        clickDiscuss: function() {
            window.open(DISCOURSE_URL, '_blank');
        },
    },
    watch: {
        mini: {
            immediate: true,
            handler: function() {
                if (this.mini) {
                    let $body = document.querySelector('body');
                    $body.classList.remove('body--light');
                    $body.classList.add('body--dark');
                }
                else {
                    let $body = document.querySelector('body');
                    $body.classList.remove('body--dark');
                    $body.classList.add('body--light');
                }
            }
        }
    },
    computed: {
        mini: function() {
            return ! this.isMobile && ! this.mouseOverDrawer && this.page === 'player';
        },
        page: {
            get: function() { return this.$store.state.page; },
            set: function(val) { this.$store.commit('setPage', val); },
        },
        pageTitle: function() {
            if (this.page === 'player') return this.showName;
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

.body--dark .q-card {
    background: #212121 !important;
}

.logoimg {
    height: 140px;
    margin-top: 15px;
    margin-bottom: 15px;
    margin-left: -25px;
    vertical-align: middle;
    filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5));
    cursor: pointer;
}
</style>

<template>
    <div>
        <q-layout view="lHh Lpr lff" container class="shadow-2 rounded-borders">
          <q-drawer
            v-model="drawer"
            show-if-above
            :width="200"
            :breakpoint="400"
            style="text-align: left;"
          >
            <q-scroll-area style="border-right: 1px solid #ddd">
              <q-img src="images/lazybug_sanstext.svg" width="250" style="margin-top: 15px; margin-bottom: 15px; margin-left: -25px; vertical-align: middle; filter: drop-shadow(5px 5px 5px rgba(0,0,0,0.5))" />
              <q-list padding>
                <q-item :active="page === 'videos'" clickable @click="page = 'videos'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="list" />
                  </q-item-section>

                  <q-item-section>
                    Videos
                  </q-item-section>
                </q-item>

                <q-item :active="page === 'star'" clickable @click="page = 'star'" v-ripple>
                  <q-item-section avatar>
                    <q-icon name="star" />
                  </q-item-section>

                  <q-item-section>
                    Star
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
            <q-page padding>
                <ShowTable v-if="page === 'videos'" />
                <StarTable v-if="page === 'star'" />
                <Settings v-if="page === 'settings'" />
            </q-page>
          </q-page-container>
        </q-layout>

        <EmbeddedCaption />
    </div>
</template>

<script>
import ShowTable from './ShowTable.vue'
import StarTable from './StarTable.vue'
import Settings from './Settings.vue'
import EmbeddedCaption from './EmbeddedCaption.vue'

export default {
    data: function() { return {
        page: 'videos',
    }},
    mounted: function() {
    },
    components: {
        ShowTable,
        StarTable,
        Settings,
        EmbeddedCaption,
    },
};
</script>

<style>
#webroot {
    /*text-align: center;*/
}
</style>

const web = Vue.createApp({
    render: h => Vue.h(WebRoot),
})

web.use(store)
web.use(Quasar)
web.mount('#webroot')

// Need to define this global callback for the Youtube iframe API
let youtubeAPIReady = false;
function onYouTubeIframeAPIReady() {
    store.commit('setYoutubeAPIReady');
}

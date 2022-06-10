Quasar.Dark.set(false);

const web = Vue.createApp({
    render: h => Vue.h(WebRoot),
})

web.use(store)
web.use(Quasar)
web.mount('#webroot')
Quasar.Dark.set(false);

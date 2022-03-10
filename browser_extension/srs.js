const srs = Vue.createApp({
    render: h => Vue.h(SRSRoot),
})

srs.use(Quasar)
srs.mount('#srsroot')

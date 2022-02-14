const popup = Vue.createApp({
    render: h => Vue.h(PopupRoot),
})

popup.use(Quasar)
popup.mount('#popuproot')

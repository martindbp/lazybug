const dashboard = Vue.createApp({
    render: h => Vue.h(DashboardRoot),
})

dashboard.use(Quasar)
dashboard.mount('#dashboardroot')

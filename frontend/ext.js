const mut = new MutationObserver((mutations) => {
    for(let mutation of mutations) {
        for(let node of mutation.addedNodes) {
            if (node.nodeType !== 1) continue;
            if (node.classList.contains('q-dialog')) {
                node.parentNode.classList.add('lazybugquasardialog');
            }
            if (node.classList.contains('q-dialog') || node.id === 'q-notify' || node.id === 'q-loading-bar') {
                node.classList.add('lazybugcaption');
                break;
            }
        }
    }
});
mut.observe(document, {subtree: true, childList: true});

var captionRoot = document.createElement('div');
captionRoot.setAttribute('id', 'extroot');
captionRoot.setAttribute('class', 'lazybugcaption');

document.body.appendChild(captionRoot);

const app = Vue.createApp({
    render: h => Vue.h(ExtensionCaption),
})

app.use(store)
app.use(Quasar)
app.mount('#extroot')

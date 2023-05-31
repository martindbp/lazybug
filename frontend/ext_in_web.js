// Append an empty div with the id "haslazybugextension" so that the lazybug web app
// can find it and know whether extension is installed or not

let hasExtIndicator = document.createElement('div');
hasExtIndicator.setAttribute('id', 'haslazybugextension');
document.body.appendChild(hasExtIndicator);

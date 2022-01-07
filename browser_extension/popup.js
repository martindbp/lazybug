document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('measurecaption').addEventListener('click', (event) => {
        chrome.tabs.query({}, tabs => {
            tabs.forEach(tab => {
            chrome.tabs.sendMessage(tab.id, 'measurecaption');
          });
        });
    });
    document.getElementById('printplaylist').addEventListener('click', (event) => {
        chrome.tabs.query({}, tabs => {
            tabs.forEach(tab => {
            chrome.tabs.sendMessage(tab.id, 'printplaylist');
          });
        });
    });
});

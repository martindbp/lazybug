const ZIMUDEVMODE = true;

if (ZIMUDEVMODE) {
    let translationInProgress = false;
    let lastTranslationTime = null;
    let nextWaitTime = 0;

    let inputTextArea = document.querySelector('textarea')
    let outputTextArea = document.querySelectorAll('textarea')[1]

    function pollTranslate() {
        translationInProgress = true;
        chrome.runtime.sendMessage({'type': 'poll'}, function onResponse(message) {
            if (message === undefined || message == null) {
                console.log('Failed to get');
                translationInProgress = false;
                return false;
            }
            console.log('Got text', message.data);
            inputTextArea.value = message.data;
            inputTextArea.dispatchEvent(new Event('input', { 'bubbles': true, 'cancelable': true }));
            lastTranslationTime = Date.now();
            nextWaitTime = 60000 * Math.random(); // Wait somewhere beteen 0 and 60 seconds
            if (message.data.length < 100) nextWaitTime = 2000;

            const originalValue = outputTextArea.value;
            const interval = setInterval(function() {
                if (
                    outputTextArea.value !== originalValue &&
                    outputTextArea.value.split('\n').length === message.data.split('\n').length
                ) {
                    console.log('Got translation', outputTextArea.value);
                    translationInProgress = false;
                    clearInterval(interval);
                    chrome.runtime.sendMessage({'type': 'translation', 'data': outputTextArea.value});
                }
            }, 500);
            return true;
        });
    };

    setInterval(function() {
        if (translationInProgress) return;

        const timeSinceLast = lastTranslationTime !== null ? Date.now() - lastTranslationTime : 999999999999;
        if (timeSinceLast < nextWaitTime) {
            return;
        }

        pollTranslate();
    }, 1000);
}

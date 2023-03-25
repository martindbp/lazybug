if (DEVMODE) {
    let translationInProgress = false;
    let lastTranslationTime = null;
    let nextWaitTime = 0;

    let inputTextArea = document.querySelector('d-textarea div')
    let outputTextArea = document.querySelectorAll('d-textarea div')[1]

    function sleep(delay) {
        return new Promise(resolve => setTimeout(resolve, delay));
    }

    async function pollTranslate() {
        translationInProgress = true;
        const message = await new Promise(resolve => {
            chrome.runtime.sendMessage({'type': 'poll'}, resolve);
        });
        if (message === undefined || message == null) {
            console.log('Failed to get');
            translationInProgress = false;
            return false;
        }
        console.log('Got text', message.data.slice(0, 100));
        inputTextArea.focus();
        document.execCommand('selectAll', false);
        await sleep(100);
        document.execCommand('delete', false);
        await sleep(100);
        document.execCommand('insertText', false, message.data);
        lastTranslationTime = Date.now();
        nextWaitTime = 5*60000 * Math.random(); // Wait somewhere beteen 0 and 5 minutes
        if (message.data.length < 100) nextWaitTime = 10000; // 10 s

        const originalValue = outputTextArea.textContent;
        const interval = setInterval(function() {
            const outputLines = [...outputTextArea.querySelectorAll('p')].map(($el) => $el.innerText);
            if (
                outputTextArea.textContent !== originalValue &&
                outputLines.length === message.data.split('\n').length
            ) {
                console.log('Got translation', outputTextArea.textContent.slice(0, 100));
                translationInProgress = false;
                clearInterval(interval);
                chrome.runtime.sendMessage({'type': 'translation', 'data': outputLines.join('\n')});
            }
            else {
                console.log('output textarea textContent did not change');
            }
        }, 500);
        return true;
    };

    setInterval(async function() {
        if (translationInProgress) return;

        const timeSinceLast = lastTranslationTime !== null ? Date.now() - lastTranslationTime : 999999999999;
        if (timeSinceLast < nextWaitTime) {
            return;
        }

        await pollTranslate();
        await sleep(1000); // sleep for 1 second before polling again
    }, 1000);

    // When there's a javascript error on deepl.com, we reload the page
    window.onerror = function(message, source, lineno, colno, error) {
        location.reload();
    };
}

chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.type === 'poll') {
        console.log('Polling');
        fetch('http://localhost:8000')
        .then(function(response) {
            if (!response.ok) {
                console.log('No server running');
                sendResponse(null);
                return null;
            }
            return response;
        })
        .then(response => response.text())
        .then(data => sendResponse({'data': data}))
        .catch((error) => {
            console.log('No server running');
            sendResponse(null);
            return null;
        });
    }
    else if (message.type === 'translation') {
        fetch('http://localhost:8000', { method: 'POST', body: message.data })
    }

    return true;
});

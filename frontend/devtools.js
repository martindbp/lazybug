let AVElement = null;
let videoMenu = null;

let mouseDownClientX = null;
let mouseDownClientY = null;
let videoRect = null;
let captionTop = null;
let captionBottom = null;
let captionLeft = null;
let captionRight = null;
let captionTopPx = null;
let captionBottomPx = null;
let captionLeftPx = null;
let captionRightPx = null;

let timings = null;

chrome.runtime.onMessage.addListener(msgObj => {
    if (AVElement === null) {
        switch (getCurrentSite()) {
            case 'youtube':
                AVElement = document.querySelector("#primary video");
                videoMenu = document.querySelector('.ytp-chrome-bottom');
                break;
            case 'bilibili':
                AVElement = document.querySelector("video");
                videoMenu = null;
                break;
        }
    }

    if (msgObj === 'togglerecording') {
        if (timings !== null) {
            download('timings.json', JSON.stringify(timings));
            return;
        }

        let flashDiv = document.createElement("div");
        flashDiv.style.cssText = "position:absolute;";
        document.body.appendChild(flashDiv);

        flashDiv.style.left = mouseDownClientX + "px";
        flashDiv.style.top = mouseDownClientY + "px";
        flashDiv.style.width = (captionRightPx - captionLeftPx) + "px";
        flashDiv.style.height = (captionBottomPx - captionTopPx) + "px";
        flashDiv.style.background = 'rgb(0, 255, 0)';
        timings = [];
        setTimeout(function() {
            flashDiv.remove();
            const start = window.performance.now() / 1000;
            let interval = setInterval(function() {
                if (timings === null) {
                    clearInterval(interval);
                    return;
                }
                const offset = window.performance.now() / 1000 - start;
                console.log(offset, AVElement.currentTime, AVElement.duration);
                timings.push([offset, AVElement.currentTime, AVElement.duration]);
            }, 500);
        }, 100);
    }
    if (msgObj === 'measurecaption') {
        if (videoMenu) videoMenu.style.visibility = 'hidden';

        let clientX = null;
        let clientY = null;
        mouseDownClientX = null;
        mouseDownClientY = null;
        let measureDiv = null;
        let moveHandler = null;
        window.addEventListener("mousemove", function(event) {
            clientX = event.clientX;
            clientY = event.clientY;
        });

        function stopMeasuring() {
            console.log('Stop measuring');
            videoRect = AVElement.getBoundingClientRect();
            captionTopPx = mouseDownClientY - videoRect.top;
            captionTop = captionTopPx / videoRect.height;
            captionBottomPx = clientY - videoRect.top;
            captionBottom = captionBottomPx / videoRect.height;
            captionLeftPx = mouseDownClientX - videoRect.left;
            captionLeft = captionLeftPx / videoRect.width;
            captionRightPx = clientX - videoRect.left;
            captionRight = captionRightPx / videoRect.width;
            measureDiv.remove();
            measureDiv = null;
            window.removeEventListener("mousemove", moveHandler);
            moveHandler = null;
            videoMenu.style.visibility = 'visible';

            const data = {
                "ocr_params": [
                    {
                        "type": "hanzi",
                        "caption_top": captionTop,
                        "caption_bottom": captionBottom,
                        "caption_left": captionLeft,
                        "caption_right": captionRight,
                        "start_time": 0
                    }
                ]
            };
            prompt('Copy:', JSON.stringify(data, null, 2));
        }

        function startMeasuring() {
            console.log('Start measuring');
            measureDiv = document.createElement("div");
            measureDiv.style.cssText = "position:absolute; color: white; border-color: black; border: 2px solid black;";
            document.body.appendChild(measureDiv);

            mouseDownClientX = clientX;
            mouseDownClientY = clientY;
            measureDiv.style.left = clientX + "px";
            measureDiv.style.top = clientY + "px";
            measureDiv.style.width = 0 + "px";
            measureDiv.style.height = 0 + "px";

            moveHandler = (moveEvent) => {
                measureDiv.style.width = (moveEvent.clientX - mouseDownClientX) + "px";
                measureDiv.style.height = (moveEvent.clientY - mouseDownClientY) + "px";
            };

            window.addEventListener("mousemove", moveHandler);
            window.addEventListener("mouseup", (upEvent) => {
                upEvent.preventDefault();
                upEvent.stopPropagation();
                stopMeasuring();
            }, { once: true, capture: true });
        }

        window.addEventListener("mousedown", (downEvent) => {
            downEvent.preventDefault();
            downEvent.stopPropagation();
            startMeasuring();
        }, { once: true, capture: true });
    }
    else if (msgObj === 'printvideo') {
        let captionId = extractCurrentCaptionId(document.location.href); // eslint-disable-line
        let data = {
            "name": {
                "hz": "",
                "py": "",
                "en": ""
            },
            "description": "",
            "seasons": [
                {
                    "episodes": [
                        {
                            "id": captionId,
                        }
                    ]
                }
            ],
            "ocr_params": [
                {
                    "type": "hanzi",
                    "caption_top": captionTop,
                    "caption_bottom": captionBottom,
                    "caption_left": captionLeft,
                    "caption_right": captionRight,
                    "start_time": 0
                }
            ],
        };
    }
    else if (msgObj === 'printplaylist') {
        let data = {};
        switch (getCurrentSite()) {
            case 'youtube':
                const title = document.querySelector('#playlist #video-title');
                const urlSearchParams = new URLSearchParams(window.location.search);
                const params = Object.fromEntries(urlSearchParams.entries());
                const playlistId = params["list"];

                let data = {
                    "name": {
                        "hz": "",
                        "py": "",
                        "en": ""
                    },
                    "description": "",
                    "seasons": [
                        {
                            "playlist_id": playlistId,
                            "episodes": [
                            ]
                        }
                    ],
                    "ocr_params": [
                        {
                            "type": "hanzi",
                            "caption_top": captionTop,
                            "caption_bottom": captionBottom,
                            "start_time": 0
                        }
                    ],
                };
                for (var el of document.querySelectorAll("ytd-playlist-panel-renderer a.ytd-playlist-panel-video-renderer")) {
                    let videoId = getYoutubeIdFromURL(el.href); // eslint-disable-line
                    data.seasons[0].episodes.push({
                        "id": "youtube-" + videoId
                    });
                }
            case 'bilibili':
                console.log('asd');
        }

        console.log(JSON.stringify(data, null, 2));
    }
});

let AVElement = null;
let videoMenu = null;

let captionTop = null;
let captionBottom = null;

chrome.runtime.onMessage.addListener(msgObj => {
    if (msgObj === 'measurecaption') {
        if (AVElement === null) {
            AVElement = document.querySelector("#primary video");
            videoMenu = document.querySelector('.ytp-chrome-bottom');
        }

        videoMenu.style.visibility = 'hidden';

        let clientX = null;
        let clientY = null;
        let mouseDownClientX = null;
        let mouseDownClientY = null;
        let measureDiv = null;
        let moveHandler = null;
        window.addEventListener("mousemove", function(event) {
            clientX = event.clientX;
            clientY = event.clientY;
        });

        function stopMeasuring() {
            console.log('Stop measuring');
            var videoRect = AVElement.getBoundingClientRect();
            var videoTop = (mouseDownClientY - videoRect.top) / videoRect.height;
            var videoBottom = (clientY - videoRect.top) / videoRect.height;
            var videoLeft = (mouseDownClientX - videoRect.left) / videoRect.width;
            var videoRight = (clientX - videoRect.left) / videoRect.width;
            measureDiv.remove();
            measureDiv = null;
            window.removeEventListener("mousemove", moveHandler);
            moveHandler = null;
            mouseDownClientX = null;
            mouseDownClientY = null;
            videoMenu.style.visibility = 'visible';

            const data = {
                "ocr_params": [
                    {
                        "type": "hanzi",
                        "caption_top": videoTop,
                        "caption_bottom": videoBottom,
                        "caption_left": videoLeft,
                        "caption_right": videoRight,
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
    else if (msgObj === 'printplaylist') {
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
                    "youtube_playlist": playlistId,
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

        console.log(JSON.stringify(data, null, 2));
    }
});
let AVElement = null;

let captionTop = null;
let captionBottom = null;

chrome.runtime.onMessage.addListener(msgObj => {
    if (msgObj === 'measurecaption') {
        window.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
        }, { once: true });

        window.addEventListener("mousedown", (downEvent) => {
            downEvent.preventDefault();
            downEvent.stopPropagation();
            if (AVElement === null) {
                AVElement = document.querySelector("video");
            }

            const measureDiv = document.createElement("div");
            measureDiv.style.cssText = "position:absolute; color: white; border-color: black; border: 2px solid black;";
            document.body.appendChild(measureDiv);

            measureDiv.style.left = downEvent.clientX + "px";
            measureDiv.style.top = downEvent.clientY + "px";
            measureDiv.style.width = 0 + "px";
            measureDiv.style.height = 0 + "px";

            const moveHandler = (moveEvent) => {
                measureDiv.style.width = (moveEvent.clientX - downEvent.clientX) + "px";
                measureDiv.style.height = (moveEvent.clientY - downEvent.clientY) + "px";
            };

            window.addEventListener("mousemove", moveHandler);
            window.addEventListener("mouseup", (upEvent) => {
                upEvent.preventDefault();
                upEvent.stopPropagation();
                var videoRect = AVElement.getBoundingClientRect();
                var videoTop = Math.round(AVElement.videoHeight * (downEvent.clientY - videoRect.top) / videoRect.height);
                var videoBottom = Math.round(AVElement.videoHeight * (upEvent.clientY - videoRect.top) / videoRect.height);
                captionBottom = videoBottom / AVElement.videoHeight;
                captionTop = videoTop / AVElement.videoHeight;
                measureDiv.remove();
                window.removeEventListener("mousemove", moveHandler);

                const data = {
                    "ocr_params": [
                        {
                            "type": "hanzi",
                            "caption_top": captionTop,
                            "caption_bottom": captionBottom,
                            "start_time": 0
                        }
                    ]
                };
                prompt('Copy:', JSON.stringify(data, null, 2));
            }, { once: true });
        }, { once: true });
    }
    else if (msgObj === 'printplaylist') {
        const title = document.querySelector('#header-description > h3:nth-child(1) > yt-formatted-string > a').innerText;
        const urlSearchParams = new URLSearchParams(window.location.search);
        const params = Object.fromEntries(urlSearchParams.entries());
        const playlistId = params["list"];

        let data = {
            "name": "",
            "description": "",
            "seasons": [
                {
                    "name": title,
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
        prompt('Copy:', JSON.stringify(data, null, 2));
    }
});

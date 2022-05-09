{{#CLOZE_TYPE}}
<div id="root"></div>

<script>

// NOTE: we don't declare global variables with e.g. const, because it breaks with importing the FrontSide in anki cards
cardType = 'CLOZE_TYPE';
json = {{ data }};

function truncateTranslationLength(py, hz) {
    // Calculates a max length based on the length of `py` and `hz`
    return Math.max(15, Math.ceil(Math.max(py.length, hz.length) * 2));  // add 100% to longest
}

getYoutubeEmbedCode = (id, t0, t1, autoplay = false, width = 560, height = 315) => `<iframe width="${width}" height="${height}" src="https://www.youtube-nocookie.com/embed/${id}?start=${Math.floor(t0)}&end=${Math.ceil(t1)}&autoplay=${autoplay ? 1 : 0}&rel=0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;

function addEmbedding(event) {
    const [site, id] = json.captionId.split('-');
    const embedding = getYoutubeEmbedCode(id, json.t0, json.t1, true);
    event.target.outerHTML = embedding;
}

function clozeContent(data) {
    return `<span class="clozeplaceholder" style="color:blue">[...]</span><span class="clozedata" style="display:none;color:blue">${data}</span>`;
}

function makeCloze(wordData, hiddenStates, cardType, wordIdx, t0, t1, captionId) {
    let html = `<table>\n`;
    let nextClozeIdx = 0;
    for (const rowType of ['py', 'hz', 'tr']) {
        let row = '<tr>\n';
        for (let j = 0; j < wordData[rowType].length; j++) {
            let data = wordData[rowType][j];

            if (wordIdx == j && cardType !== 'cloze_translation') {
                if (rowType === 'py' || rowType === 'hz') {
                    if (['cloze_word_py_hz', 'cloze_word_all'].includes(cardType)) {
                        row += `<td>${clozeContent(data)}</td>\n`;
                    }
                    else {
                        row += `<td>${data}</td>\n`;
                    }
                }
                else if (rowType === 'tr') {
                    if (['cloze_word_tr', 'cloze_word_all'].includes(cardType)) {
                        row += `<td>${clozeContent(data)}</td>\n`;
                    }
                    else {
                        row += `<td>${data}</td>\n`;
                    }
                }
            }
            else {
                let visibilityStr = '';

                if (cardType === 'cloze_translation' && rowType === 'tr') {
                    visibilityStr = 'style="visibility: hidden"';
                }

                let title = null;
                if (rowType === 'tr') {
                    const truncateLength = truncateTranslationLength(wordData.py[j], wordData.hz[j]);
                    const doTruncate = data.length > truncateLength;
                    title = data;
                    data = data.slice(0, truncateLength) + (doTruncate ? '...' : '');
                }
                if (rowType !== 'hz' && hiddenStates[rowType][j]) {
                    data = `<span style="display: none">${data}</span>`;
                }
                if (title !== null) {
                    row += `<td ${visibilityStr} title="${title}">${data}</td>\n`;
                }
                else {
                    row += `<td ${visibilityStr} >${data}</td>\n`;
                }
            }
        }
        row += '</tr>\n';
        html += row;
    }
    html += '</table>';
    html += `<br><button onClick="document.querySelectorAll('td').forEach((el) => el.style.visibility = 'visible')">Show context</button>`;
    html += `<br><hr><br><div>${clozeContent(wordData.translation)}</div>`;
    html += `<br><hr><button onClick="addEmbedding(event)">Play</button>`;

    return html;
}

document.getElementById('root').innerHTML = makeCloze(json.wordData, json.hidden, cardType, json.wordIdx, json.t0, json.t1, json.captionId);

</script>
{{/CLOZE_TYPE}}

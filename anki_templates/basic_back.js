{{#CLOZE_TYPE}}
<div id="root"></div>

<script>

const cardType = 'CLOZE_TYPE';

const json = {{ data }};

let html = '';
if (cardType === 'basic_py_hz') {
    html = json.wordData.hz[json.wordIdx] + ' - ' + json.wordData.py[json.wordIdx];
}
else if (cardType === 'basic_tr') {
    html = json.wordData.tr[json.wordIdx];
}
else if (cardType === 'basic_hz') {
    html = json.wordData.hz[json.wordIdx];
}
document.getElementById('root').innerHTML = html;

</script>
{{/CLOZE_TYPE}}

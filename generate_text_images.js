const fs = require('fs')
const { registerFont, createCanvas } = require('canvas')
const UtfString = require('utfstring');

let fonts = []
fs.readdirSync('data/remote/private/fonts/').forEach(file => {
    const name = file.split('.')[0];
    const path = 'data/remote/private/fonts/' + file;
    registerFont(path, { family: name });
    fonts.push(name);
});

async function saveCanvasAsPNG(canvas, filename){
    return new Promise(resolve => {
        const out = fs.createWriteStream(filename);
        const stream = canvas.createPNGStream();
        stream.pipe(out);
        out.on('finish', resolve);
    });
}

async function generate(text, textWidth, textColor, font, fontSize, lineWidth, lineColor, bold, italic, outFilename) {
    const buffer = 30;
    let canvasHeight = 2*buffer + fontSize;
    bold = bold ? 'bold' : ''
    italic = italic ? 'italic' : ''

    const fontStr = `${bold} ${italic} ${fontSize}px ${font}`;
    let canvas = createCanvas(200, canvasHeight);

    let measurementCtx = canvas.getContext('2d');
    measurementCtx.font = fontStr;
    measurementCtx.textBaseline = 'ideographic';
    let textMeasurement = measurementCtx.measureText(text);

    let textWidths = [0];
    let cutOffIndex = undefined;
    for (let i = 0; i < text.length; i++) {
        const offset = measurementCtx.measureText(UtfString.slice(text, 0, i+1));
        if (offset.width >= textWidth) {
            cutOffIndex = i;
            break
        }
        textWidths.push(offset.width);
    }

    if (cutOffIndex !== undefined) {
        text = UtfString.slice(text, 0, cutOffIndex);
    }

    canvas = createCanvas(textMeasurement.width, canvasHeight);

    let ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgba(0, 0, 0, 0.0)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.textBaseline = 'ideographic';
    ctx.font = fontStr;
    ctx.fillStyle = textColor;
    if (lineWidth > 0) {
        ctx.shadowBlur = 0;
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = lineColor;
        ctx.strokeText(text, 0, buffer);
    }

    ctx.fillText(text, 0, buffer);

    if (lineWidth > 0) {
        ctx.stroke();
    }
    ctx.fill();

    await saveCanvasAsPNG(canvas, outFilename+'.png');

    ctx = canvas.getContext('2d');
    ctx.fillStyle = 'black';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.textBaseline = 'ideographic';
    ctx.font = fontStr;
    ctx.fillStyle = 'white';
    ctx.fillText(text, 0, buffer);

    await saveCanvasAsPNG(canvas, outFilename+'_mask.png');

    return textWidths;
}

(async () => {
    const data = fs.readFileSync(process.argv[2], 'utf8')
    const lines = data.split('\n');
    let textWidthLines = '';
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].length == 0) {
            continue
        }
        const splits = lines[i].split(';;');
        [text, textWidth, textColor, font, fontSize, lineWidth, lineColor, bold, italic] = splits;
        outFilename = `${process.argv[3]}/text_${i}`;
        console.log(lines[i], outFilename);
        const textWidths = await generate(
            text,
            parseInt(textWidth),
            textColor,
            font,
            parseInt(fontSize),
            parseInt(lineWidth),
            lineColor,
            bold == 'true',
            italic == 'true',
            outFilename
        );
        textWidthLines += textWidths.join(',') + '\n';
    }
    fs.writeFile(process.argv[4], textWidthLines, function (err, data) {
        if (err) {
            return console.log(err);
        }
    });
})().catch(e => {
});

const translate = require("baidu-translate-api");

translate("让我们来翻译吧!").then(res => {
    console.log(res.trans_result.dst);
    // Let's translate it!
});

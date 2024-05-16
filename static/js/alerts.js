// ポップアップを表示する関数
function showMessage(message){
    alert("Message: " + message); //メッセージをポップアップで表示
}

// フォーム送信時のリクエスト処理
function registerMonthlyRecord(yearmonth, assettype, moneyamount) {
    fetch('/monthly_record', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            YearMonth: yearmonth,
            AssetType: assettype,
            MoneyAmount: moneyamount
        })
    })
    .then(response => {
        if (response.status === 409) {  // エラーが発生する条件
            // エラーポップアップを表示
            response.text().then(text => showMessage(text));  // エラーメッセージを表示
        } else if (response.status === 201) {  // 登録成功時
            // 登録が成功した場合、メッセージを表示してページをリロード
            response.text().then(text => {showMessage(text);
            location.reload();
        });
        } else {
            showMessage("An unexpected error occurred.");
        }
    })
    .catch(error => {
        console.error("An error occurred:", error);
        showMessage("予期しないエラーが発生しました。");
    });
}
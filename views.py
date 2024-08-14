from flask import render_template, request, redirect, url_for, abort, flash, session
from app import app,RecordDetailsView
from models import db,BalanceManagement, FinanceManagement, TransactionDetails, TransactionItem, Users
from sqlalchemy import text,desc
from datetime import datetime,date
from forms import LoginForm, SignUpForm
from flask_login import login_user, logout_user, login_required

#===========================================================
# トランザクション処理関数
#===========================================================
def commit_transaction(session, description):
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise Exception(f"Error during {description}: {e}")
    
#===========================================================
# カスタムフィルター
#===========================================================
def format_with_commas(value):
    # 渡された数値をカンマ付きの文字列に変換
    if isinstance(value,int) or isinstance(value,float):
        return "{:,}".format(value)
    else:
        return value

# カスタムフィルターをFlaskアプリケーションに登録
app.jinja_env.filters['comma_format'] = format_with_commas

#===========================================================
# ルーティング
#===========================================================
# トップぺージ
@app.route("/top")
@login_required
def top():
    return render_template("top.html")

#===========================================================
# 登録画面
#===========================================================
@app.route("/record",methods=["GET","POST"])
@login_required
def record():
    # POST時はDB登録
    if request.method == "POST":
        
        # 日付情報を取得しYYYYMM型の文字列データへ変換
        datestr = request.form["Date"]
        dateobj = datetime.strptime(datestr,"%Y-%m-%d")
        YearMonth = dateobj.strftime("%Y%m")
        userid = session['user_id'] # ssessionからログイン中のユーザーIDを取得
        
        # 登録フォームの入力内容を取得
        data = (
            request.form["Date"],
            request.form["Event"],
            int(request.form["TransactionAmount"]),
            request.form["PaymentMethod"],
            request.form["Memo"],
            request.form["TransactionItemName"],
            request.form["Income_OutgoType"],
            request.form["Suppliers"],
            request.form["Category"],
            YearMonth,
            request.form["AssetType"],
            userid
            )
        
        # ストアドプロシージャ名を変数へ格納
        proc_name = "FM_Schema_AddData"
            
        # [:data(i)]でプレースホルダーを設置
        sql = f"CALL {proc_name}({', '.join([':data' + str(i) for i in range(len(data))])})"

        # 引数の辞書を作成 {data0:YYYY-MM-DD}の形で辞書を作成
        params = {f'data{i}': item for i, item in enumerate(data)}
        
        # text(sql)でプレースホルダー付きの生SQL文を生成し、
        # paramsの辞書データでプレースホルダーに値をバインドし命令実行
        db.session.execute(text(sql), params)
        
        # 登録画面へリダイレクト
        return redirect(url_for("record"))
    
    # GETの場合は登録画面を表示
    return render_template("record.html")

#===========================================================
# 現金引出画面
#===========================================================
@app.route("/draw",methods=["GET","POST"])
@login_required
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 関数名    ：cash_draw
# 機能      ：現金引出操作をした場合に
#             引出元と引出先の視点で二つのレコードを生成する
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def cash_draw():
    #POST時はDB登録
    if request.method == "POST":
        
        # 日付情報を取得しYYYYMM型の文字列データへ変換
        datestr = request.form["Date"]
        dateobj = datetime.strptime(datestr,"%Y-%m-%d")
        yyyymmstr = dateobj.strftime("%Y%m")
        userid = session['user_id'] # sessionからログイン中のユーザーIDを取得
        
        # リクエストからタプルへデータを取得
        data = (
            request.form["Date"],   #data0:Date
            "現金引出",             #data1:Event
            int(request.form["Draw_Amount"]) + int(request.form["Commission"]), #data2:TransactionAmount
            "-",                    #data3:PaymentMethod
            request.form["Memo"],   #data4:Memo
            "-",                    #data5:TransactionItemName
            "支出",                 #data6:Income_OutgoType
            request.form["Draw_Destination"],   #data7:Suppliers
            "現金移動",             #data8:Category
            yyyymmstr,              #data9:YearMonth
            request.form["Draw_Sauce"],  #data10:AssetType
            userid                  #data11:UserID
        )
        # ストアドプロシージャを使用し引出元のレコードを作成
        proc_name = "FM_Schema_AddData"
        
        # [:data(i)]でプレースホルダーを設置
        sql = f"CALL {proc_name}({', '.join([':data' + str(i) for i in range(len(data))])})"
        # sql = "CALL FM_Schema_AddData(:data0,:data1,:data2,:data3…)":data〇がプレースホルダー
        
        # 引数の辞書を作成 {data0:YYYY-MM-DD}の形で辞書を作成
        params = {f'data{i}': item for i, item in enumerate(data)}
        # enumerateでリスト(data)内のインデックスと要素をiとitemへ格納
        # data1:買い物 等

        # text(sql)でプレースホルダー付きの生SQL文を生成し、
        # paramsの辞書データでプレースホルダーに値をバインドし命令実行
        db.session.execute(text(sql), params)
        
        # リクエストデータを引出先用のデータへ書き換え
        params['data2'] = int(request.form["Draw_Amount"])
        params['data6'] = "収入"
        params['data7'] = request.form["Draw_Sauce"]
        params['data10'] = request.form["Draw_Destination"]
        
        # 書き換えたデータでもう一度ストアドプロシージャを起動
        db.session.execute(text(sql), params)

        return redirect(url_for("history"))

    #GET時は現金引出画面表示
    return render_template("cash_draw.html")
    
#===========================================================
# 削除処理
#===========================================================
@app.route("/delete/<int:td_id>")
@login_required
def delete(td_id):
    delrec1 = TransactionDetails.query.filter_by(TransactionID=td_id).first_or_404()
    delrec2 = FinanceManagement.query.filter_by(FinanceManagementID=delrec1.FinanceManagementID).first_or_404()
    delrec3 = TransactionItem.query.filter_by(TransactionItemID=delrec2.TransactionItemID).first_or_404()

    db.session.delete(delrec1)
    db.session.delete(delrec2)
    db.session.delete(delrec3)
    
    db.session.commit()
    
    return redirect(url_for("history"))

#===========================================================
# 修正画面
#===========================================================
@app.route("/update/<int:td_id>",methods=["GET","POST"])
@login_required
def update(td_id):
    
    # POSTメソッドの場合
    if request.method == "POST":
        # 各テーブルの修正対象のレコードを取得
        updrec1 = TransactionDetails.query.filter_by(TransactionID=td_id).first_or_404()
        updrec2 = FinanceManagement.query.filter_by(FinanceManagementID=updrec1.FinanceManagementID).first_or_404()
        updrec3 = TransactionItem.query.filter_by(TransactionItemID=updrec2.TransactionItemID).first_or_404()

        # 各レコードのカラム内容を書き換え
        updrec1.Date = request.form["Date"]
        updrec1.Event = request.form["Event"]
        updrec1.TransactionAmount = request.form["TransactionAmount"]
        updrec1.PaymentMethod = request.form["PaymentMethod"]
        updrec1.Memo = request.form["Memo"]
        updrec3.Income_OutgoType = request.form["Income_OutgoType"]
        updrec3.Suppliers = request.form["Suppliers"]
        updrec3.Category = request.form["Category"]
        updrec3.TransactionItemName = request.form["TransactionItemName"]
        
        # DB更新
        db.session.commit()
        
        # 一覧画面へ遷移
        return redirect(url_for("history"))

    # GETメソッドの場合
    # 一覧画面からのID情報(td_id)を元にレコードを特定するクエリを作成
    detail = db.session.query(TransactionDetails,TransactionItem,BalanceManagement)\
        .join(FinanceManagement,TransactionDetails.FinanceManagementID == FinanceManagement.FinanceManagementID)\
            .join(TransactionItem,FinanceManagement.TransactionItemID == TransactionItem.TransactionItemID)\
                .join(BalanceManagement,FinanceManagement.BalanceManagementID == BalanceManagement.BalanceManagementID)\
                    .filter(TransactionDetails.TransactionID==td_id).first_or_404()
        
    # 取得したレコードを引数として修正画面を呼び出し
    return render_template("update.html",detail=detail)

#===========================================================
# 一覧画面
#===========================================================
@app.route("/history")
@login_required
def history():
    # フォームから年月情報を取得
    year = request.args.get("year",None,type=int)
    month = request.args.get("month",None,type=int)
    account = request.args.get("account","")
    userid = session['user_id']
    current_year = datetime.now().year
    current_month = datetime.now().month

    # 取引履歴表示用のクエリを設定
    query = db.session.query(RecordDetailsView).filter(RecordDetailsView.c.UserID == userid)

    # 検索情報が指定されている場合、クエリにフィルタを追加
    if year and month:
        query = query.filter(db.extract("year",RecordDetailsView.c.Date) == year)
        query = query.filter(db.extract("month",RecordDetailsView.c.Date) == month)
    elif year and not month:
        query = query.filter(db.extract("year",RecordDetailsView.c.Date) == year)
    elif not year and month:
        query = query.filter(db.extract("year",RecordDetailsView.c.Date) == current_year)
        query = query.filter(db.extract("month",RecordDetailsView.c.Date) == month)
    else:
        query = query.filter(db.extract("year",RecordDetailsView.c.Date) == current_year)
        query = query.filter(db.extract("month",RecordDetailsView.c.Date) == current_month)

    if account:        
        query = query.filter(RecordDetailsView.c.AssetType == account)
        
    query = query.order_by(RecordDetailsView.c.Date,RecordDetailsView.c.AssetType)

    # resultにフィルター結果をリストとして代入
    result = query.all()

    # リストのままだと引数受渡でエラーとなる為アンパックして辞書にパッキング
    packed_data = []
    for date, event, transaction_amount, income_outgo_type, suppliers, category, transaction_item_name, payment_method, asset_type, money_amount, running_balance,memo,td_id,fm_id,ti_id,bm_id,fm_userid in result:
        record = {
            'Date': date,
            'Event': event,
            'TransactionAmount': transaction_amount,
            'Income_OutgoType': income_outgo_type,
            'Suppliers': suppliers,
            'Category': category,
            'TransactionItemName': transaction_item_name,
            'PaymentMethod': payment_method,
            'AssetType': asset_type,
            'MoneyAmount': money_amount,
            'RunningBalance': running_balance,
            'Memo' : memo,
            'TransactionID' : td_id,
            'FinanceManagementID' : fm_id,
            'TransactionItemID' : ti_id,
            'BalanceManagementID' : bm_id,
            'UserID' : fm_userid
        }
        packed_data.append(record)
        
    # 収支表示用のクエリを設定
    total_payment = sum(detail.TransactionAmount for detail in result if detail.Income_OutgoType == "支出" and detail.Category != "現金移動")
    total_income = sum(detail.TransactionAmount for detail in result if detail.Income_OutgoType == "収入" and detail.Category != "現金移動")
    total_balance = total_income - total_payment
    
    # htmlファイルへの引数としてクエリ結果を渡す
    return render_template(
        "history.html",
        transaction_details=packed_data,
        total_payment = total_payment,
        total_income = total_income,
        total_balance = total_balance,
        year=year,
        month=month,
        account=account,
        )

#===========================================================
# 月次残高一覧画面
#===========================================================
@app.route("/monthly_history")
@login_required
def monthly_history():
    # フォームから年月情報を取得
    year = request.args.get("year",None,type=int)
    month = request.args.get("month",None,type=int)
    account = request.args.get("account","")
    userid = session['user_id'] # sessionからログイン中のユーザーIDを取得
    
    # ユーザー毎の月次残高テーブル全件取得クエリを設定
    query = db.session.query(BalanceManagement).filter(BalanceManagement.UserID_bm == userid)
    
    # 検索情報が指定されている場合、クエリにフィルタを追加
    if year:
        query = query.filter(BalanceManagement.YearMonth.like(year))
    if month:
        query = query.filter(BalanceManagement.YearMonth.like(month))
    if account:        
        query = query.filter(BalanceManagement.AssetType == account)
    
    query = query.order_by(BalanceManagement.YearMonth,BalanceManagement.AssetType)
    
    # resultにフィルター後のクエリオブジェクトを代入
    result = query.all()
        
    # htmlファイルへの引数としてクエリオブジェクトを渡す
    return render_template(
        "monthly_history.html",
        monthly_amounts=result,
        year=year,
        month=month,
        account=account,
        )
    
#===========================================================
# 月次残高修正画面
#===========================================================
@app.route("/monthly_update/<int:bm_id>",methods=["GET","POST"])
@login_required
def monthly_update(bm_id):
    
    # POSTメソッドの場合
    if request.method == "POST":
        
        # 残高テーブルの修正対象のレコードを取得
        updrec = BalanceManagement.query.filter_by(BalanceManagementID=bm_id).first_or_404()

        # 各レコードのカラム内容を書き換え
        updrec.MoneyAmount = request.form["MoneyAmount"]
        
        # DB更新
        db.session.commit()
        
        # 一覧画面へ遷移
        return redirect(url_for("monthly_history"))
    
    # GETメソッドの場合
    # 月次残高一覧画面からのID情報(bm_id)を元にレコードを特定するクエリを作成
    detail = db.session.query(BalanceManagement).filter(BalanceManagement.BalanceManagementID==bm_id).first_or_404()
        
    # 取得したレコードを引数として修正画面を呼び出し
    return render_template("monthly_update.html",detail=detail)

#===========================================================
# 月初残高登録画面
#===========================================================
@app.route("/monthly_record",methods=["GET","POST"])
@login_required
def monthly_record():
    # POST時はDB登録
    if request.method == "POST":
        
        # 辞書型としてjson形式データを取得(デシリアライズ)
        data = request.json 
        
        # 登録内容を変数へ格納
        yearmonth = data["YearMonth"]
        assettype = data["AssetType"]
        moneyamount = int(data["MoneyAmount"])
        userid = session['user_id'] # sessionからログイン中のユーザーIDを取得
        
        # 同年同月同口座の登録レコードがあるか検索
        exists_record = db.session.query(BalanceManagement).filter(
            BalanceManagement.YearMonth == yearmonth,
            BalanceManagement.AssetType == assettype,
            BalanceManagement.UserID_bm == userid
        ).first()
        
        if exists_record:
            # レコードが存在する場合、abortで処理を中断し、HTTP 409 Conflictでエラーメッセージを返す
            abort(409,description="既にレコードが存在しているため登録できません")
        else: # レコードが存在しない場合、DBへ登録処理を実行
            new_record = BalanceManagement(
                YearMonth = yearmonth,
                AssetType = assettype,
                MoneyAmount = moneyamount,
                UserID_bm = userid
                )
            
            # セッションに新しいレコードを追加
            db.session.add(new_record)
            # データベースへコミットして変更を確定
            db.session.commit()

            # 成功時のHTTPレスポンス
            return "正常に登録処理が完了しました", 201  
    
    # GETの場合は登録画面を表示
    return render_template("monthly_record.html")
    
#===========================================================
# 口座残高棚卸画面
#===========================================================
@app.route("/inv_balance_record",methods=["GET","POST"])
@login_required
def inv_balance_record():
    
    # 最初に本日の日付を取得
    today = date.today()
    
    # POSTメソッドの場合
    if request.method == "POST":
        
        # 入力情報を変数へ格納
        yearmonth = today.strftime("%Y%m")  # `YYYYMM`の形にフォーマット
        assettype = request.form["AssetType"]
        now_amount = int(request.form["NowAmount"])
        userid = session['user_id'] # sessionからログイン中のユーザーIDを取得
    
        # 現在の残高情報を抽出
        query = db.session.query(RecordDetailsView.c.running_balance)\
            .filter(RecordDetailsView.c.AssetType == assettype,RecordDetailsView.c.UserID == userid)\
                .order_by(desc(RecordDetailsView.c.Date),desc(RecordDetailsView.c.TransactionID)).first()
        
        # レコードが存在しなければ残高を0として計算
        # 後程jsにてエラーハンドリング機能を実装予定
        if query is not None:
            balance_value = query.running_balance
        else:
            balance_value = 0
        
        # 残高より多ければ収入用データを作成、少なければ支出用でデータを作成
        if now_amount >= balance_value:
            transactionamount = now_amount - balance_value
            income_outgo_type = "収入"
            category = "棚卸収入"
        elif balance_value > now_amount:
            transactionamount = balance_value - now_amount
            income_outgo_type = "支出"
            category = "棚卸支出"
        
        # 登録用のデータセットを作成
        data = (
            today,                  #data0:Date
            "棚卸登録",             #data1:Event
            int(transactionamount), #data2:TransactionAmount
            "-",                    #data3:PaymentMethod
            request.form["Memo"],   #data4:Memo
            "-",                    #data5:TransactionItemName
            income_outgo_type,      #data6:Income_OutgoType
            "-",                    #data7:Suppliers
            category,               #data8:Category
            yearmonth,              #data9:YearMonth
            assettype,              #data10:AssetType
            userid                  #data11:UserID
            )

        # ストアドプロシージャを使用しレコードを作成
        proc_name = "FM_Schema_AddData"
        
        # [:data(i)]でプレースホルダーを設置
        sql = f"CALL {proc_name}({', '.join([':data' + str(i) for i in range(len(data))])})"
        
        # 引数の辞書を作成 {data0:YYYY-MM-DD}の形で辞書を作成
        params = {f'data{i}': item for i, item in enumerate(data)}

        # DB登録
        db.session.execute(text(sql), params)
        
        # 棚卸登録が完了したら一覧画面にリダイレクト
        return redirect(url_for("history"))

    # GETの場合は日付を引数として登録画面を表示
    return render_template("inv_balance_record.html",today = today)
    
#===========================================================
# ログイン画面（Form使用）
#===========================================================
@app.route("/", methods=["GET", "POST"])
def login():
    
    # Formインスタンス生成
    form = LoginForm()
    
    if request.method == "POST":
        
        #どのボタンを押したのか判定
        action = request.form.get("action")
        
        #ゲストログイン時の処理
        if action == "ゲストログイン":
            #guestユーザーのレコードを格納
            guest_user = Users.query.filter_by(username="guest").first()
        
            #ゲストユーザーが見つかったらログイン
            if guest_user is not None:
                login_user(guest_user)
                session['user_id']=guest_user.UserID # ゲストユーザーのユーザーIDをセッションへ格納
                return redirect(url_for("top"))
            else: #見つからなかったらアナウンス
                flash("ゲストユーザーが見つかりません")
                
        else: # 通常ログイン時の処理
            # データ入力取得
            username = form.username.data
            password = form.password.data
        
            # 対象User取得
            user = Users.query.filter_by(username=username).first()
        
            # 認証判定
            if user is not None and user.check_password(password):
                # 成功
                # 引数として渡されたuserオブジェクトを使用して、ユーザーをログイン状態にする
                login_user(user)
                session['user_id']=user.UserID # ユーザーIDをセッションへ格納
                # 画面遷移
                return redirect(url_for("top"))
            # 失敗
            flash("認証不備です")
            
    # GET時
    # 画面遷移
    return render_template("login_form.html", form=form)

# ログアウト
@app.route("/logout")
@login_required
def logout():
    # 現在ログインしているユーザーをログアウトする
    logout_user()
    # セッション情報をクリアする
    session.clear()
    # フラッシュメッセージ
    flash("ログアウトしました")   
    # 画面遷移
    return redirect(url_for("login"))

# サインアップ（Form使用）
@app.route("/register", methods=["GET", "POST"])
def register():
    
    #自分のメールアドレスをホワイトリストへ追加
    AUTHORIZED_EMAILS = ['kn.ui.101@outlook.jp']
    
    # Formインスタンス生成
    form = SignUpForm()
    if form.validate_on_submit():
        
        #アカウント認証
        email = form.email.data
        
        if email in AUTHORIZED_EMAILS:
        
            # データ入力取得
            username = form.username.data
            password = form.password.data
            # モデルを生成
            user = Users(username=username)
            # パスワードハッシュ化
            user.set_password(password)
            # 登録処理
            db.session.add(user)
            db.session.commit()
            # フラッシュメッセージ
            flash("ユーザー登録しました")  
            # 画面遷移 
            return redirect(url_for("login"))
        
        #失敗
        flash("このメールアドレスは使用できません")
        
    # GET時
    # 画面遷移
    return render_template("register_form.html", form=form)
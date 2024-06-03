from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

#============================================
#モデル
#============================================

class BalanceManagement(db.Model):
    #残高管理テーブル
    __tablename__ = 'balance_management_table' 
    #残高管理ID(PK)
    BalanceManagementID = db.Column(db.Integer, primary_key=True)
    #年月情報
    YearMonth = db.Column(db.String(45))
    #資産種別
    AssetType = db.Column(db.String(45))
    #貯金額
    MoneyAmount = db.Column(db.Numeric(10,2))
    
class FinanceManagement(db.Model):
    #収支管理テーブル 
    #リレーションのための中間テーブル
    __tablename__ = 'finance_management_table'
    #収支管理ID(PK)
    FinanceManagementID = db.Column(db.Integer, primary_key=True)
    #残高管理ID(FK)
    BalanceManagementID = db.Column(db.Integer, db.ForeignKey('balance_management_table.BalanceManagementID'))
    #取引項目ID(FK)
    TransactionItemID = db.Column(db.Integer,db.ForeignKey('transaction_item_table.TransactionItemID'))

class TransactionDetails(db.Model):
    #取引詳細テーブル 
    # 発生したイベント内容を記録するテーブル
    __tablename__ = 'transaction_details_table'
    #取引詳細ID(PK)
    TransactionID = db.Column(db.Integer, primary_key=True)
    #日付
    Date = db.Column(db.Date)
    #イベント内容
    Event = db.Column(db.String(255))
    #finance_management_tableへの外部キー
    FinanceManagementID = db.Column(db.Integer, db.ForeignKey('finance_management_table.FinanceManagementID'))
    #取引金額
    TransactionAmount = db.Column(db.Numeric(10, 2))
    #支払い方法
    PaymentMethod = db.Column(db.String(255))
    #備考
    Memo = db.Column(db.String(255))

class TransactionItem(db.Model):
    #取引項目テーブル
    #収支の種類や取引先を記録するテーブル 
    __tablename__ = 'transaction_item_table'
    #取引項目ID(PK)
    TransactionItemID = db.Column(db.Integer, primary_key=True)
    #取引品目名
    TransactionItemName = db.Column(db.String(255))
    #収入/支出フラグ
    Income_OutgoType = db.Column(db.String(255))
    #取引先
    Suppliers = db.Column(db.String(255))
    #カテゴリ
    Category = db.Column(db.String(255))

class Users(UserMixin,db.Model):
    # ユーザーテーブル
    __tablename__ = 'users_table'
    # UserID(PK)
    UserID = db.Column(db.Integer, primary_key=True)
    # ユーザー名
    username = db.Column(db.String(50), unique=True, nullable=False)
    # パスワード
    password = db.Column(db.String(120), nullable=False)
    
    # パスワードをハッシュ化して設定
    def set_password(self,password):
        self.password = generate_password_hash(password)
    # 入力したパスワードとハッシュ化されたパスワードの比較
    def check_password(self, password):
        return check_password_hash(self.password,password)
    # get_idメソッドをオーバーライド
    def get_id(self):
        return str(self.UserID)
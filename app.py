from flask import Flask
from sqlalchemy import Table, MetaData
from flask_login import LoginManager

#============================================
# Flask定義
#============================================
app = Flask(__name__)  # Flaskアプリケーションを定義
app.config.from_object("config.Config")

# DBとFlaskの紐づけ
from models import db,Users
db.init_app(app)

# LoginManagerインスタンス
login_manager = LoginManager()
# LoginmanagerとFlaskの紐づけ
login_manager.init_app(app)

# 未ログイン時のメッセージを変更
login_manager.login_message = "認証されていません：ログインしてください"
# 未認証のユーザーがアクセスしようとした際にリダイレクトされる関数名を設定
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# appコンテキスト内でViewを定義
with app.app_context():
    metadata = MetaData()
    # Viewを定義
    RecordDetailsView = Table(
        'v_record_details',  # テーブル/ビューの名前
        metadata,
        mysql_autoload=True,  # テーブル/ビューの構造を自動的に読み込む
        autoload_with=db.engine  # データベースエンジン
    )

# viewsのインポート
from views import *

#============================================
# 実行
#============================================
if __name__ == "__main__":
    app.run()
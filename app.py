from flask import Flask
from sqlalchemy import Table, MetaData

#============================================
# Flask定義
#============================================
app = Flask(__name__)  # Flaskアプリケーションを定義
app.config.from_object("config.Config")
# DBとFlaskの紐づけ
from models import db
db.init_app(app)
#ブランチテスト
print("ブランチテスト")
# appコンテキスト内でViewを定義
with app.app_context():
    metadata = MetaData()
    #metadata.reflect(bind=db.engine,mysql_reflect=True)
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
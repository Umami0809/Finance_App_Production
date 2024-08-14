from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, ValidationError,Email
from models import Users

# ベースフォームクラス
class BaseForm(FlaskForm):
    username = StringField('ユーザー名：', validators=[DataRequired('ユーザー名は必須入力です')])
    # パスワード：パスワード入力
    password = PasswordField('パスワード: ', validators=[Length(4, 10,'パスワードの長さは4文字以上10文字以内です')])
    email = EmailField('メールアドレス：', validators=[Email('メールアドレスのフォーマットではありません')])
    # ボタン
    submit = SubmitField()
    
    # カスタムバリデータ
    # 英数字と記号が含まれているかチェックする
    def validate_password(self, password):
        if not (any(c.isalpha() for c in password.data) and \
            any(c.isdigit() for c in password.data) and \
            any(c in '!@#$%^&*()' for c in password.data)):
            raise ValidationError('パスワードには【英数字と記号：!@#$%^&*()】を含める必要があります')

# ログイン用入力クラス
class LoginForm(BaseForm):
    submit = SubmitField('ログイン')

# サインアップ用入力クラス
class SignUpForm(LoginForm):
    # ボタン
    submit = SubmitField('サインアップ')

    # usernameバリデータ
    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('そのユーザー名は既に使用されています')
        
    # Emailアドレスバリデータ
    def validate_email(self, email):
        email = Users.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('そのメールアドレスは既に使用されています')
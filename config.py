#============================================
#設定
#============================================

class Config(object):
    #デバッグモード
    DEBUG=False
    #警告対策
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #DB設定
    SQLALCHEMY_DATABASE_URI = "mysql://admin_FinanceManagement:masa_7610@financemanagement-dbserver.mysql.database.azure.com/financialmanagement"
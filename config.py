import os

S3_BUCKET                       = "coms4156-strategies"
DB_HOST                         = os.environ.get('ALCHEMIST_RDB_HOST')
S3_LOCATION                     = 's3://{}/'.format(S3_BUCKET)
S3_LOCATION_HTTP                = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)
SECRET_KEY                      = os.urandom(16)
USER_SERVICE_USER               = os.environ.get('USER_SERVICE_USER')
USER_SERVICE_PASSWORD           = os.environ.get('USER_SERVICE_PASSWORD')
S3_ACCESS_KEY                   = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY                   = os.environ.get('S3_SECRET_KEY')
S3_REGION                       = 'us-east-1'
SQLALCHEMY_DATABASE_URI         = f'mysql+pymysql://{USER_SERVICE_USER}:{USER_SERVICE_PASSWORD}@{DB_HOST}:3306/backtest'
ALLOWED_EXTENSIONS              = {'py'}  # allowed upload file extension
SQLALCHEMY_TRACK_MODIFICATIONS  = False
DEBUG                           = True
PORT                            = 5000
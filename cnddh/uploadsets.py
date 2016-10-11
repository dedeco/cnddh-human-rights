from flask_uploads import UploadSet

req_exts = ('txt','doc','docx','xls','xlsx','zip','pdf')

anexos_upload = UploadSet('anexos', extensions=req_exts)
from cnddh import app
from cnddh.utils import template_checa_permissao

from sqlalchemy import func

import locale

from config import TIMEZONE, LOCALE, EMAIL_LOGIN

@app.context_processor
def inject_functions():
    return dict(
        checa_permissao = template_checa_permissao
        )

@app.template_filter('tamanho')
def length(object):
    return len(object)+2

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%H:%M / %d-%m-%Y', blank_message=u"N/A"):
    if value:
        return value.strftime(format)
    else:
        return blank_message    
        
@app.template_filter('getdatelocalized')        
def getdatelocalized(value):
    if value:         
        from datetime import datetime 
        from babel.dates import format_datetime,get_timezone
        return format_datetime(value,tzinfo=get_timezone(TIMEZONE), locale=LOCALE,  format="d 'de' MMMM 'em' HH':'mm")
    else:
        return u"-"

@app.template_filter('emailfrom')        
def emailfrom(value):
    return EMAIL_LOGIN
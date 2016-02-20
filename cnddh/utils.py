# coding=latin-1

from flask import flash
from flask import current_app, request, g
from wtforms.fields import FormField, _unset_value
import datetime, time
import logging
import logging.handlers   

from email.mime.text import MIMEText

from config import EMAIL_HOST, EMAIL_PORT, EMAIL_LOGIN, EMAIL_PASSWORD, DEBUG

class NonLazyFormField(FormField):

    def __init__(self, form_class, label=u'', validators=None, separator='-', **kwargs):
        super(NonLazyFormField, self).__init__(form_class, label, validators, separator, **kwargs)
        prefix = self.name + self.separator
        self.form = self.form_class(prefix=prefix)

    def process(self, formdata, data=_unset_value):
        if data is _unset_value:
            try:
                data = self.default()
            except TypeError:
                data = self.default
            self._obj = data

        if isinstance(data, dict):
            self.form.process(formdata=formdata, **data)
        else:
            self.form.process(formdata=formdata, obj=data)

def datestring_to_date(datestr, formatstr="%d/%m/%Y"):
    try:
        dt = time.strptime(datestr, formatstr)
    except ValueError:
        dt = None
    
    if dt:
        dd = datetime.date(*dt[:3])
    else:
        dd = None

    return dd

def limpa_unicode(astr):
    if not astr:
        return None

    s = astr
    s = s.replace(u'\u200b', u' ')
    s = s.replace(u'\u2010', u'-')
    s = s.replace(u'\u2011', u'-')
    s = s.replace(u'\u2012', u'-')
    s = s.replace(u'\u2013', u'-')
    s = s.replace(u'\u2014', u'-')
    s = s.replace(u'\u2015', u'-')
    s = s.replace(u'\u2022', u'*')
    s = s.replace(u'\u2021', u'|')
    s = s.replace(u'\u2030', u'%0')
    s = s.replace(u'\u2122', u'TM')
    s = s.replace(u'\u2018', u"'")
    s = s.replace(u'\u2019', u"'")
    s = s.replace(u'\u201a', u"'")
    s = s.replace(u'\u201b', u"'")
    s = s.replace(u'\u201c', u'"')
    s = s.replace(u'\u201d', u'"')
    s = s.replace(u'\u201e', u'"')
    s = s.replace(u'\u201f', u'"')

    return s
    
class Paginator(object):
    
    def __init__(self, obj_query, cur_page = 1, per_page = 10, eagerload=False):
        self.query = obj_query
        self.cur_page = cur_page
        self.per_page = per_page
        self.eagerload = eagerload
        self._num_pages = None

    def is_valid(self):
        return (self.num_pages > 0) and (self.cur_page > 0) and (self.cur_page <= self.num_pages)

    def objs(self):
        if self.is_valid():
            init_obj = self.per_page * (self.cur_page - 1)
            end_obj = init_obj + self.per_page
            if self.eagerload:
                objs = self.query.all()
                return objs[init_obj:end_obj]
            else:
                return self.query[init_obj:end_obj]
        else:
            return []

    def current_page(self):
        return self.cur_page

    @property
    def num_pages(self):
        if not self._num_pages:
            if isinstance(self.query, list):
                num_objs = len(self.query)
            else:
                num_objs = self.query.count()

            if (self._num_pages is None) and (num_objs > 0):
                self._num_pages = (num_objs / self.per_page)
                if (num_objs % self.per_page):
                    self._num_pages += 1
            else:
                self._num_pages = 0
        
        return self._num_pages

    def has_next(self):
        return (self.cur_page < self.num_pages)

    def has_previous(self):
        return (self.cur_page > 1)

    def has_more_previous(self, range_size = 0):
        if range_size <= 0:
            return False
        else:
            return (self.cur_page - range_size) > 1

    def has_more_next(self, range_size = 0):
        if range_size <= 0:
            return False
        else:
            return (self.cur_page + range_size) < self.num_pages

    def previous_range(self, range_size = 0):
        if range_size <= 0:
            return range(1, self.cur_page)
        else:
            r1 = self.cur_page - range_size
            if r1 < 1:
                r1 = 1
            return range(r1, self.cur_page)

    def next_range(self, range_size = 0):
        if range_size <= 0:
            return range(self.cur_page + 1, self.num_pages + 1)
        else:
            r1 = self.cur_page + range_size
            if r1 > self.num_pages:
                r1 = self.num_pages
            return range(self.cur_page + 1, r1 + 1)

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Erro no campo %s: %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')
  
class TlsSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        """
        Emit a record.
 
        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            import string # for tls add this line
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            string.join(self.toaddrs, ","),
                            self.getSubject(record),
                            formatdate(), msg)
            if self.username:
                smtp.ehlo() # for tls add this line
                smtp.starttls() # for tls add this line
                smtp.ehlo() # for tls add this line
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)    
         
def template_checa_permissao(permissao):
    try:
        return  g.user.checa_permissao(permissao)
    except AttributeError:
        return False
       
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()        

def envia_email(email_from, email_to, msg):
    if isinstance(email_to, str) or isinstance(email_to, unicode):
        email_to = [email_to]

    if DEBUG:
        email_to = ['dedeco@gmail.com'] #DEBUG
        
    try:
        import smtplib
        import string # for tls add this line
        
        try:
            from email.utils import formatdate
        except ImportError:
            formatdate = datetime.datetime.today()

        if EMAIL_HOST and EMAIL_PORT:
            s = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        else:
            s = smtplib.SMTP()            
                       
        if EMAIL_LOGIN and EMAIL_PASSWORD:
            s.ehlo() # for tls add this line
            s.starttls() # for tls add this line
            s.ehlo() # for tls add this line
            s.login(EMAIL_LOGIN, EMAIL_PASSWORD)
        try:
            s.sendmail(email_from, email_to, msg)
        finally:
            s.quit()                        
    except smtplib.SMTPException, e:
        return False
    
    return True        
    
def envia_email_excecao(erro_id, excecao_texto):
    email_base = """
    Ocorreu uma excecao (internal server error) na aplicacao newsuperbuy. Usuario: {login}, nome: {nome} , telefone: {telefone} e email: {email}. Veja os detalhes abaixo:
    
    {excecao_texto}
    
    Atenciosamente,    
    Sistema
    """   
    
    email_to = ['dedeco@gmail.com']

    if g.user:
        try:
            login = g.user.login
            nome =  g.user.nome.encode('latin-1')
            telefone = '31 3071-4827'       
            email = g.user.email
        except AttributeError:
            login = '-usuario desconhecido/nao logado-'
            nome =  '-'               
            telefone = '-'               
            email = '-'
    else:
        login = '-usuario desconhecido/nao logado-'
        nome =  '-'               
        telefone = '-'               
        email = '-'           

    email_body = email_base.format(excecao_texto=excecao_texto, login=login, nome=nome, telefone=telefone, email=email)
    msg = MIMEText(email_body, 'plain')
    msg['Subject'] = 'Erro %s no CNDDH' % erro_id
    msg['From'] = 'Sistema <sistema@cnddh.org.br>'
    msg['To'] = ', '.join(email_to)
    msg['Reply-To'] = 'Sistema <sistema@cnddh.org.br>'

    return envia_email('sistema@cnddh.org.br',email_to,msg.as_string())    
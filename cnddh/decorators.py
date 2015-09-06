# coding=latin-1
from flask import request, g
from flask import abort, flash

from functools import wraps

def checa_permissao(permissao):
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if g.user and g.user.checa_permissao(permissao):
                return f(*args, **kwargs)
            else:
                flash(u'Atenção você não possui a permissão: %s. Se isto não estiver correto, entre em contato solicitando esta permissão.' % permissao.upper(),u'notice')
                abort(401)
        return inner
    return decorator

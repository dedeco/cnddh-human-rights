# coding=latin-1
from flask import request, g
from flask import render_template
from flask import flash
from flask import jsonify
from flask import session
from flask import abort, redirect, url_for
from flask.ext.login import login_user , logout_user , current_user , login_required
from cnddh.decoder import killgremlins
from config import PROD, DEBUG

import os
import md5
import json
import datetime
import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy import asc, desc, exc, and_, or_, func
from cnddh import app
from cnddh import login_manager, logger
from database import db

from cnddh.models import  Denuncia, Vitima, Suspeito, Usuario, Cidade, TipoVitima, TipoSuspeito, TipoViolacao, Violacao, Homicidio, TipoMeioUtilizado, HomicidioMeioUtilizado, TipoFonte, Anexo, Status, Acao, Historico, Usuario, Permissao, Perfil, PermissaoPerfil, PermissaoUsuario, PerfilUsuario, TipoLocal, Encaminhamento, TipoEncaminhamento, Orgao, Oficio, Telefonema, Reuniao, Email, Generico, Retorno, TipoRetorno, RetornoGenerico, RetornoPessoasassistidas, RetornoInquerito, RetornoProcesso, RetornoBO, RetornoRCO, RetornoREDS, RetornoPoliticaPSR
from cnddh.forms import DenunciaForm, VitimaForm, SuspeitoForm, RelacionarForm, FinalizarForm, PesquisarForm, WorkflowForm, GraficoViolacaoForm, GraficoViolSuspForm, UsuarioForm, LoginForm, PermissaoForm, PesquisaUsuarioForm, EncaminhamentoForm, OficioForm, TelefonemaForm, ReuniaoForm, EmailForm, GenericoForm, RetornoForm, HomicidioForm, MotivoForm
from cnddh.uploadsets import anexos_upload
from flaskext.uploads import UploadNotAllowed
from cnddh.utils import Paginator, flash_errors, TlsSMTPHandler, shutdown_server, datestring_to_date, envia_email
from decorators import checa_permissao

from mapeamentos import estados_choices, tipoassistencia_choices, politicas_choices

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import joinedload_all, with_polymorphic

import logging
import logging.handlers 

from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

@app.route('/')
def index():
    return render_template('home.html') 
    
@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def nao_autorizado(e):
    return render_template('401.html'), 401    
    
@login_manager.user_loader
def load_user(id):
    return Usuario.query.get(int(id))

@app.route('/recuperasenha', methods=['GET', 'POST'])
def recupera_senha():
    u = db.session.query(Usuario).get(1)
    u.senhahash =  md5.new(u.login + '012288').hexdigest() 
    db.session.commit()
    return "Ok. Por enquanto."
    
@app.route('/login', methods=['GET', 'POST'])
def login():    
    val = False
    
    if request.method == 'POST':       
    
        f = LoginForm(request.form)        
        if f.validate():             
            u = None
            try:
                u = db.session.query(Usuario).filter(Usuario.login == f.login.data).one()            
            except NoResultFound:
                val = False
                
            if u:
                if(u.senhahash ==md5.new(f.login.data + f.senha.data).hexdigest()):
                    val = True
                else:
                    val = False
            else:
                val = False
                
            if val:                
                login_user(u)
                return redirect(request.args.get('next') or url_for('index'))
            else:
                flash(u"Senha e/ou usuário inválidos", u"error")
                return redirect(url_for('login'))
                
    else:
        f = LoginForm()  

    if request.method == 'GET':
        return render_template('login.html',f=f)            
        
    return render_template('login.html',f=f)   

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index')) 
    
@app.before_request
def before_request():
    g.user = current_user    
    
@app.route('/usuario/<int:usuario_id>/editar', methods=['GET', 'POST'])
@app.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
def usuario_edit(usuario_id=None):
    u=None
   
    if usuario_id:
        u = db.session.query(Usuario).get(usuario_id)
        
        if u:
            if not g.user.checa_permissao('altera-usuario'): #usuário só pode editar seus próprios dados se não tiver permissão especial
                if g.user.id != u.id: 
                    abort(401)
        else:
            abort(404)
    else:
        if g.user.checa_permissao('cria-usuario'): 
            pass
        else:
            abort(401)    
    
    if request.method == 'POST':       
    
        f = UsuarioForm(request.form)  
    
        if f.senha.data == f.confirmasenha.data:
            if usuario_id:
                if f.validate():
                
                    if u:
                        if md5.new(f.login.data + f.senhaatual.data).hexdigest() == u.senhahash or g.user.checa_permissao('altera-usuario'):                        
                            u.nome = f.nome.data
                            u.senhahash =  md5.new(f.login.data + f.senha.data).hexdigest()                             
                            u.email = f.email.data
                            u.ddd = f.telefone.ddd.data 
                            u.telefone = f.telefone.numero.data
                            u.dtultlogin = datetime.datetime.today() 
                            db.session.commit()
                            flash(u"Usuário alterado com sucesso.", u"success")  
                            return redirect(url_for('usuario_edit',usuario_id=u.id))  
                        else:
                            flash(u"Você deve digitar a senha atual corretamente para alterar dos dados.", u"error")
                            return redirect(url_for('usuario_edit',usuario_id=u.id))
                else:
                    flash(u"Verificar erros no formulários.", u"error")                                                   
            else:
                if f.validate(): 

                    if g.user.checa_permissao('cria-usuario'):     
                    
                        us = db.session.query(Usuario).filter(or_(Usuario.login == f.login.data, Usuario.email == f.email.data)).all()
                        
                        if us:
                            flash(u"O usuário já existe e este email também. Não é possível cadastrar novamente.", u"error")   
                        else:
                            u = Usuario(f.login.data, f.nome.data, f.telefone.ddd.data, f.telefone.numero.data, md5.new(f.login.data + f.senha.data).hexdigest(),f.email.data)
                                                    
                            db.session.add(u)
                            db.session.commit()
                            flash(u"Usuário criado com sucesso", u"success")  
                            return redirect(url_for('login'))
                    else:
                        flash(u"Você não tem permissão para criar um novo usuário", u"error")
                        abort(401)
                else:
                    flash(u"Verificar erros no formulários.", u"error")                       
                        
        else:    
            flash(u"A senha e a confirmação devem ser iguais.", u"error") 

    else:
        f = UsuarioForm()
        if u:
            f.login.data=u.login
            f.nome.data = u.nome
            f.telefone.ddd.data  = u.ddd
            f.telefone.numero.data = u.telefone
            f.email.data = u.email

    if request.method == 'GET':
        return render_template('usuario.html',f=f, usuario_id=usuario_id)
        
    return render_template('usuario.html',f=f, usuario_id=usuario_id)       
    
@app.route('/denuncia/<int:denuncia_id>/editar', methods=['GET', 'POST'])
@app.route('/denuncia/novo', methods=['GET', 'POST'])
@login_required
@checa_permissao('edita-denuncia')
def denuncia_edit(denuncia_id=None):
    d = None
    novo = True
            
    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)
        novo = False
    else:
        if not g.user.checa_permissao('cria-denuncia'):
            abort(401)
  
    q = db.session.query(TipoFonte.id, TipoFonte.tipofonte).order_by(TipoFonte.tipofonte.asc())    
    option_tpfonte = ([(str(x), y) for x,y in q.all()])                  
    
    q = db.session.query(TipoLocal.id, TipoLocal.local).order_by(TipoLocal.local.asc())      
    option_tplocal = ([(str(x), y) for x,y in q.all()])            
        
    if request.method == 'POST':       
  
        f = DenunciaForm(request.form, obj=d)   
               
        q = db.session.query(Cidade.cidade, Cidade.cidade)
        q = q.filter(Cidade.estado==f.endereco.estado.data)                            
        
        option_cidade = [(u"", u"")]
        option_cidade.extend([(x,y) for x,y in q.all()])                   
        f.endereco.cidade.choices = option_cidade
        
        f.tipofonte_id.choices = option_tpfonte       
        f.endereco.tipolocal.choices = option_tplocal

        if f.validate():                 
            
            if novo:                    
                d = Denuncia(f.numero.data)              

            d.numero = f.numero.data
            d.dtdenuncia = f.dtdenuncia.data
            d.resumo = f.resumo.data
            d.descricao = f.descricao.data
            d.observacao = f.observacao.data
            d.tipofonte_id = f.tipofonte_id.data            
            d.fonte = f.fonte.data
            if f.protocolo.data:
                d.protocolo = f.protocolo.data
            else:
                d.protocolo = 0 
            if _controle_status(d,1):
                d.status_id = 1
            d.tipolocal = f.endereco.tipolocal.data
            d.endereco = f.endereco.endereco.data
            d.num = f.endereco.num.data
            d.complemento = f.endereco.complemento.data
            d.referencia = f.endereco.referencia.data
            d.bairro = f.endereco.bairro.data            
            d.cidade = f.endereco.cidade.data
            d.cep = f.endereco.cep.data
            d.estado = f.endereco.estado.data
            d.pais = "Brasil"             

            if novo:    
                try:
                    if g.user.checa_permissao('cria-denuncia'):
                        if novo:
                            db.session.add(d)                                                
                        db.session.commit()
                        return redirect(url_for('vitima_edit',denuncia_id=d.id))
                    else:
                        flash(u"Você não tem permissão para criar uma denúncia nova", u"error")
                        abort(401)
                    
                except IntegrityError:
                    db.session.rollback() 
                    flash(u"Já existe uma denúncia com este número, altere o número e tente novamente.", u"error")
            else:
                
                db.session.commit()
                
                acao = request.form.get("acao")
                if acao==u"Continuar":
                    return redirect(url_for('vitima_edit',denuncia_id=d.id))    
               
                flash(u'Denúncia %s atualizada '%d.id, u'success')                
                
        else:
            flash(u"Verifique os erros no formulário abaixo.", u"error")
    else:
        f =  DenunciaForm(obj=d) 
        
        f.tipofonte_id.choices = option_tpfonte
        f.endereco.tipolocal.choices = option_tplocal          
        
        if d:
            q = db.session.query(Cidade.cidade, Cidade.cidade)
            q = q.filter(Cidade.estado==d.estado)                            
            
            option_cidade = [(u"", u"")]
            option_cidade.extend([(x, y) for x,y in q.all()])                   
            f.endereco.cidade.choices = option_cidade       
                    
        if novo == False and d:
            f.endereco.tipolocal.data = d.tipolocal
            f.endereco.endereco.data = d.endereco
            f.endereco.num.data = d.num  
            f.endereco.complemento.data = d.complemento
            f.endereco.referencia.data = d.referencia
            f.endereco.bairro.data = d.bairro
            f.endereco.cidade.data = d.cidade
            f.endereco.cep.data = d.cep
            f.endereco.estado.data = d.estado                    
            f.endereco.pais.data = d.pais        
    
    return render_template('denuncia.html', form=f, novo=novo, denuncia=d)   

@app.route('/denuncia/<int:denuncia_id>/vitima/editar', methods=['GET', 'POST'])
@login_required
@checa_permissao('edita-vitima')
def vitima_edit(denuncia_id=None, vitima_id=None):
    editar = None
    
    q = db.session.query(TipoVitima.id, TipoVitima.tipo)
    
    option_tipovitima = []
    option_tipovitima.extend([(str(x), y) for x,y in q.all()])     

    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)
        
    if request.method == 'POST':        
        f = VitimaForm(request.form)   
        if f:   
            f.tipovitima.choices = option_tipovitima           
        
        acao = request.form.get("acao")
       
        if u"Editar" in acao: 
            vitima_id = int(acao.split('_')[1]);
            if vitima_id:
                vitima = db.session.query(Vitima).get(vitima_id)     
                
                if vitima:
                    f =  VitimaForm()
                
                    f.denuncia_id.data = d.id
                    f.vitima_id.data = vitima.id
                    f.tipovitima.data = str(vitima.tipovitima_id)
                    f.qtdevitimas.data = vitima.qtdevitimas
                    if vitima.qtdevitimas > 0:
                        f.qtdenaoespecificado.data = False
                    else:
                        f.qtdenaoespecificado.data = True
                    f.nome.data = vitima.nome
                    if vitima.nome == u'Não identificado':
                        f.nomenaoidentificado.data = True
                    else:
                        f.nomenaoidentificado.data = False
                    f.idade.data = vitima.idade
                    f.sexo.data = vitima.sexo
                    f.cor.data = vitima.cor
                    
                    editar=True
                
        if u"Deletar" in acao: 
            vitima_id = int(acao.split('_')[1]);
            if vitima_id:
                vitima = db.session.query(Vitima).get(vitima_id)        
        
                if vitima:
                    try:
                        db.session.delete(vitima) 
                        db.session.commit()              
                        flash(u"Vítima deletada: %s" % vitima.nome, u"success")
                    except OperationalError:
                        db.session.rollback()
                        
                        msg = ''
                        for vio in vitima.violacoes:
                            msg = msg + ' ' + vio.tipoviolacao.microcategoria                        
                        
                        if msg:    
                            flash(u"A vítima %s não pode ser deletada, pois primeiro é necessário desfazer a relação de violação %s com a vítima-suspieto." % (vitima.nome,msg), u"error")
            
        if acao==u"Adicionar" or acao==u"Alterar":    
        
            if d:
                
                if f.validate():
                
                    if acao==u"Alterar":
                        v = db.session.query(Vitima).get(f.vitima_id.data)
                        v.tipovitima_id = f.tipovitima.data
                    else:
                        v = Vitima(f.tipovitima.data) 
                    
                    if v:
                        v.nomenaoidentificado = f.nomenaoidentificado.data
                        if f.nomenaoidentificado.data:
                            v.nome = u'Não identificado'
                        else:                    
                            v.nome = f.nome.data
                        if f.idade.data:
                            v.idade = f.idade.data
                        else:
                            v.idade = 0
                            
                        v.sexo = f.sexo.data
                        v.cor = f.cor.data
                            
                        if f.qtdevitimas.data:
                            v.qtdevitimas = f.qtdevitimas.data 
                        else:
                            v.qtdevitimas = 1
                            
                        if f.qtdenaoespecificado.data:
                            v.qtdevitimas = 0                        
                    
                        if acao==u"Adicionar":
                            d.vitimas.append(v)
                       
                        db.session.commit() 
                        f =  VitimaForm()                        
                        flash(u"Vítima alterada ou inserida: %s" % v.nome, u"success")
                    
                else:
                    flash(u"Verifique os erros no formulário abaixo.", u"error")                        
        
        if acao==u"Continuar":
            return redirect(url_for('suspeito_edit',denuncia_id=denuncia_id))         
           
    else:
        f =  VitimaForm()

    f.denuncia_id.data = denuncia_id  
    if f:
        f.tipovitima.choices = option_tipovitima    
        
    q = db.session.query(Vitima).filter(Vitima.denuncia_id==denuncia_id).order_by(Vitima.id) 
    vitimas = q.all()  
    
    i=1
    objs = []    
    for v in vitimas:
       objs.append((i,v))
       i=i+1
    
    return render_template('vitimas.html', f=f, objs=objs, d=d, editar=editar)
    
@app.route('/denuncia/<int:denuncia_id>/suspeito/editar', methods=['GET', 'POST'])
@login_required
@checa_permissao('edita-suspeito')
def suspeito_edit(denuncia_id=None):
    editar = None
    
    q = db.session.query(TipoSuspeito.tipo,TipoSuspeito.tipo)
    q = q.group_by(TipoSuspeito.tipo)
    
    option_tipo = [(u"", u"")]
    option_tipo.extend([(x, y) for x,y in q.all()])   
    
    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)    
   
    if request.method == 'POST':        
        f = SuspeitoForm(request.form)   
        
        acao = request.form.get("acao")
        
        if u"Editar" in acao: 
            suspeito_id = int(acao.split('_')[1]);
            if suspeito_id:
                suspeito = db.session.query(Suspeito).get(suspeito_id)     
                
                if suspeito:
                    f =  SuspeitoForm()
                
                    if suspeito.tiposuspeito.instituicao:
                    
                        f.tiposuspeito.data = option_tipo
                        
                        q = db.session.query(TipoSuspeito.instituicao,TipoSuspeito.instituicao)
                        q = q.filter(TipoSuspeito.tipo == suspeito.tiposuspeito.tipo)
                        q = q.group_by(TipoSuspeito.instituicao)
                        q = q.order_by(TipoSuspeito.instituicao)

                        option_instituicao = [(u"", u"")]
                        option_instituicao.extend([(x, y) for x,y in q.all()]) 
                        f.instituicao.choices = option_instituicao
                        
                        q = db.session.query(TipoSuspeito.id,TipoSuspeito.classificacao)
                        q = q.filter(TipoSuspeito.tipo == suspeito.tiposuspeito.tipo)
                        q = q.filter(TipoSuspeito.instituicao == suspeito.tiposuspeito.instituicao)
                        q = q.order_by(TipoSuspeito.classificacao)  

                        option_classificao = [(u"", u"")]
                        option_classificao.extend([(x, y) for x,y in q.all()]) 
                        f.classificacao.choices = option_classificao                        
                
                    f.denuncia_id.data = d.id
                    f.suspeito_id.data = suspeito.id
                    f.tiposuspeito.data = suspeito.tiposuspeito.tipo
                    f.instituicao.data = suspeito.tiposuspeito.instituicao
                    f.nomeinstituicao.data = suspeito.nomeinstituicao
                    f.classificacao.data = str(suspeito.tiposuspeito_id)
                    if suspeito.qtdesuspeitos > 0:
                        f.qtdenaoespecificado.data = False
                    else:
                        f.qtdenaoespecificado.data = True                    
                    f.qtdesuspeitos.data = str(suspeito.qtdesuspeitos)
                    f.nome.data = suspeito.nome
                    if suspeito.nome == u'Não identificado':
                        f.nomenaoidentificado.data = True
                    else:
                        f.nomenaoidentificado.data = False
                    f.idade.data = suspeito.idade
                    f.sexo.data = suspeito.sexo
                    f.cor.data = suspeito.cor
                    
                    editar=True                        
        
        if u"Deletar" in acao: 
            suspeito_id = int(acao.split('_')[1]);
            if suspeito_id:
                suspeito = db.session.query(Suspeito).get(suspeito_id)        
        
                if suspeito:
                    try:
                        db.session.delete(suspeito) 
                        db.session.commit()              
                        flash(u"Suspeito deletado: %s" % suspeito.nome, u"success")
                    except OperationalError:
                        db.session.rollback()
                        
                        msg = ''
                        for vio in suspeito.violacoes:
                            msg = msg + ' ' + vio.tipoviolacao.microcategoria                        
                        
                        if msg:    
                            flash(u"O suspeito %s não pode ser deletado, pois primeiro é necessário desfazer a relação de violação %s com a vítima-suspeito." % (suspeito.nome,msg), u"error")
                    
        
        if acao==u"Adicionar" or acao==u"Alterar":    
        
            option_instituicao = None
            option_classificacao = None
            
            if f.tiposuspeito.data:
                q = db.session.query(TipoSuspeito.instituicao,TipoSuspeito.instituicao)
                q = q.filter(TipoSuspeito.tipo == f.tiposuspeito.data)    
                q = q.group_by(TipoSuspeito.instituicao)
                
                option_instituicao = [(u"", u"")]
                option_instituicao.extend([(x, y) for x,y in q.all()])  

                if f.instituicao.data:
                    q = db.session.query(TipoSuspeito.id,TipoSuspeito.classificacao)
                    q = q.filter(TipoSuspeito.tipo == f.tiposuspeito.data)
                    q = q.filter(TipoSuspeito.instituicao == f.instituicao.data)
                
                    option_classificacao = [(u"", u"")]
                    option_classificacao.extend([(str(x), y) for x,y in q.all()])   
                    
            if option_tipo:
                f.tiposuspeito.choices = option_tipo
            if option_instituicao:
                f.instituicao.choices = option_instituicao
            if option_classificacao:
                f.classificacao.choices = option_classificacao 
  
            if f.validate():  
                
                if acao==u"Alterar":
                    s = db.session.query(Suspeito).get(f.suspeito_id.data)
                else:
                    s = Suspeito(f.tiposuspeito.data)
                
                if s:                
                    s.tiposuspeito_id = f.classificacao.data 
                    s.nomeinstituicao = f.nomeinstituicao.data                
                    s.nomenaoidentificado = f.nomenaoidentificado.data
                 
                    if f.qtdesuspeitos.data:
                        s.qtdesuspeitos = f.qtdesuspeitos.data 
                    else:
                        s.qtdesuspeitos = 1
                        
                    if f.qtdenaoespecificado.data:
                        s.qtdesuspeitos = 0             
                        
                    if f.nomenaoidentificado.data:
                        s.nome =u"Não identificado"
                    else:
                        s.nome = f.nome.data
                    s.sexo = f.sexo.data
                    s.cor = f.cor.data
                    s.idade = f.idade.data
                    
                    d = db.session.query(Denuncia).get(denuncia_id)
                    
                    if acao==u"Adicionar":
                        d.suspeitos.append(s)
                   
                    db.session.commit()
                    f = SuspeitoForm()                     
                    flash(u"Suspeito inserido: %s" % s.nome, u"success")                  
                
            else:
                flash(u"Verifique os erros no formulário abaixo.", u"error")            

        if acao==u"Continuar":
            return redirect(url_for('relacionar_vitima_suspeito',denuncia_id=denuncia_id))            
            
        suspeito_id = request.form.get("suspeito-remove")
        if suspeito_id:
            s = db.session.query(Suspeito).get(suspeito_id)
            db.session.delete(s)
            db.session.commit()                                            
            flash(u"Suspeito removido: %s" % s.nome, u"success")         
            
    else:
        f =  SuspeitoForm()

    if denuncia_id:     

        q = db.session.query(Suspeito).filter(Suspeito.denuncia_id==denuncia_id).order_by(Suspeito.id)       
        suspeitos = q.all()          
        
    if f:      
        f.tiposuspeito.choices = option_tipo
        
    f.denuncia_id.data = denuncia_id  
    
    i=1
    objs = []    
    for s in suspeitos:
       objs.append((i,s))
       i=i+1
    
    return render_template('suspeitos.html', form=f, objs=objs, d=d, editar=editar)  
   
@app.route('/denuncia/<int:denuncia_id>/relacionar/editar', methods=['GET', 'POST'])
@login_required
@checa_permissao('edita-violacoes')
def relacionar_vitima_suspeito(denuncia_id=None): 

    q = db.session.query(TipoViolacao.macrocategoria, TipoViolacao.macrocategoria)    
    q = q.group_by(TipoViolacao.macrocategoria)
    q = q.order_by(TipoViolacao.macrocategoria)

    option_tpviolacao = ([(x, y) for x,y in q.all()])  

    if denuncia_id: 
        denuncia = db.session.query(Denuncia).get(denuncia_id) 
           
        vitimas = db.session.query(Vitima).filter(Vitima.denuncia_id==denuncia_id).order_by(Vitima.id).all()
        option_vitima = []
        i=1
        for v in vitimas:
            option_vitima.append([str(v.id), '['+str(i)+'] ' + v.nome + ', ' + str(v.idade) + ' anos, ' + v.tipovitima.tipo])
            i=i+1

        suspeitos = db.session.query(Suspeito).filter(Suspeito.denuncia_id==denuncia_id).order_by(Suspeito.id).all()
        option_suspeito = []
        i=1
        for s in suspeitos:
            option_suspeito.append([str(s.id), '['+str(i)+'] ' + s.nome + ', ' + s.tiposuspeito.instituicao + ' , ' + s.tiposuspeito.classificacao]) 
            i=i+1          
                
    if request.method == 'POST':        
        f = RelacionarForm(request.form)  
        
        acao = request.form.get("acao")
        
        if acao==u"Relacionar":    
            f.macrocategoria.choices = option_tpviolacao
            
            if f.macrocategoria:
                q = db.session.query(TipoViolacao.id, TipoViolacao.microcategoria)    
                q = q.filter(TipoViolacao.macrocategoria==f.macrocategoria.data)
                q = q.order_by(TipoViolacao.microcategoria)
                
                option_microcategoria = ([(str(x), y) for x,y in q.all()])  
            
            if option_microcategoria:
                f.microcategoria.choices = option_microcategoria
                
            if option_vitima:
                f.vitimas.choices = option_vitima
            if option_suspeito:
                f.suspeitos.choices = option_suspeito             
            
            if f.validate():
                gravou = False
            
                for micro in f.microcategoria.data:
                    for suspeito in f.suspeitos.data:
                        for vitima in f.vitimas.data:
                            if int(micro) ==2: #Homicidio
                                r = Homicidio(denuncia_id,micro,suspeito,vitima)                               
                            else:
                                r = Violacao(denuncia_id,micro,suspeito,vitima)
                            db.session.add(r) 
                            gravou = True   
                try:
                    db.session.commit()     
                    if gravou:
                        flash(u"Relações gravadas", u"success")     
                except IntegrityError:
                    db.session.rollback()
                    flash(u"Não é permitida mais de uma mesma violação para o par suspeito-vítima", u"error")  
                
        if acao==u"Continuar":
            q = db.session.query(Violacao).filter(Violacao.denuncia_id==denuncia_id)
            v = q.all()
            
            if v:
                return redirect(url_for('finalizar_denuncia',denuncia_id=denuncia_id))             
            else:
                flash(u"É necessário relatar uma violação para continuar a denúncia.", u"error") 
                
    else:
        f =  RelacionarForm()
        
    q = db.session.query(Violacao).filter(Violacao.denuncia_id==denuncia_id)
    q = q.options(joinedload_all(Violacao.vitima))
    q = q.options(joinedload_all(Violacao.suspeito))
    q = q.options(joinedload_all(Violacao.tipoviolacao))
    objs = q.all()
         
    vitsup = {}
    for v in objs:
        if ('['+ str(v.vitima.id) +']' + v.vitima.nome + '|' + '['+ str(v.suspeito.id) + ']'  + v.suspeito.nome) in vitsup:
            vitsup[('['+ str(v.vitima.id) +']' + v.vitima.nome + '|' + '['+ str(v.suspeito.id) + ']'  + v.suspeito.nome)].append(v)
        else:
            vitsup[('['+ str(v.vitima.id) +']' + v.vitima.nome + '|' + '['+ str(v.suspeito.id) + ']'  + v.suspeito.nome)] = [v]         
    
    f.denuncia_id.data = denuncia_id    
    f.macrocategoria.choices = option_tpviolacao
    if option_vitima:
        f.vitimas.choices = option_vitima
    if option_suspeito:
        f.suspeitos.choices = option_suspeito 
   
    
    return render_template('relacionarviolacoes.html', f=f, vitsup=vitsup, denuncia=denuncia)     

@app.route('/denuncia/<int:denuncia_id>/finalizar', methods=['GET', 'POST'])
@login_required
@checa_permissao('edita-anexos')
def finalizar_denuncia(denuncia_id=None):
    objs = []
        
    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)
  
    if request.method == u'POST':
        f = FinalizarForm(request.form) 

        acao = request.form.get("acao")     

        if acao==u"Concluir":                    
            flash(u'A denúncia foi cadastrada, agora deve ser aberta para receber os encaminhamentos.', u'success')
            return redirect(url_for('workflow'))         
      
        if f.validate():
            
            if acao==u"Salvar":
                try:
                    a = Anexo(denuncia_id)
                    if f.descricaoanexo.data:
                        a.descricaoanexo = f.descricaoanexo.data
                    else:
                        a.descricaoanexo = u'Sem descrição'
                    db.session.add(a)     
                    db.session.flush() 
                
                    ff = request.files.get('arquivo', None)
                    if ff:
                        filename = anexos_upload.save(ff, name="anexo_%04d." % a.id)
                        a.arquivo = filename
                        db.session.commit()  
                    
                        flash(u'O arquivo foi enviado!', u'success')
                except UploadNotAllowed:
                    db.session.rollback()
                    flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')
                    
    else:  
        f = FinalizarForm()    
    
    if denuncia_id:
        q = db.session.query(Anexo).filter(Anexo.denuncia_id==denuncia_id)
        anexos = q.all()
            
        for a in anexos:
            if a.arquivo:
                url = anexos_upload.url(a.arquivo)
                objs.append([a,url])

    f.denuncia_id.data = denuncia_id      
        
    return render_template('finalizar.html', f=f, objs=objs, d=d)   

@app.route('/denuncia/<int:denuncia_id>/exclui/<int:anexo_id>', methods=['GET', 'POST'])
@login_required
@checa_permissao('edita-anexos')
def exclui_anexo(denuncia_id=None,anexo_id=None):
    anexo = db.session.query(Anexo).get(anexo_id)
    if anexo:
        db.session.delete(anexo)
        db.session.commit()
        flash(u"Anexo apagado com sucesso.", u"success")
    
    return redirect(url_for('finalizar_denuncia',denuncia_id=denuncia_id))    
   
             
@app.route('/denuncia/<int:denuncia_id>/violacao/homicidio/<int:homicidio_id>', methods=['GET', 'POST'])
@login_required
@checa_permissao('edita-violacoes')
def homicidio_edit(denuncia_id=None,homicidio_id=None): 
    f = None

    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)

    q = db.session.query(TipoMeioUtilizado.id, TipoMeioUtilizado.meio)
    option_tpmeio = ([(str(x), y) for x,y in q.all()])  

    acao = request.form.get("acao")
    
    if homicidio_id:
        h = db.session.query(Homicidio).get(homicidio_id)
        
        f = HomicidioForm()
        f.meioutilizado.choices = option_tpmeio
        if h:
            aux = []
            for m in h.meiosutilizados:
                aux.append(str(m.tipomeioutilizado_id))
            if aux:                
                f.meioutilizado.data = aux
            f.rco.data = h.rco
            f.bo.data= h.bo
            f.ip.data = h.ip
            f.situacao.data = h.situacao
            f.reds.data = h.reds
            f.prfato.data = h.prfato
            f.obs.data = h.obs
        
    if request.method == u'POST':        
        f = HomicidioForm(request.form)
        f.meioutilizado.choices = option_tpmeio
                                    
        if f.validate():
            
            if acao==u"Salvar":            
   
                if h:
                    db.session.query(HomicidioMeioUtilizado).filter_by(homicidio_id=h.id).delete()  
                    for meio in f.meioutilizado.data:
                        mu = HomicidioMeioUtilizado(h.id,int(meio))
                        db.session.add(mu)  
                    
                    h.rco = f.rco.data
                    h.bo = f.bo.data
                    h.ip = f.ip.data
                    h.situacao = f.situacao.data
                    h.reds = f.reds.data
                    h.prfato = f.prfato.data
                    h.obs = f.obs.data                       
                    
                    try:
                    
                        ff = request.files.get('arquivo', None)
                        if ff:
                            filename = anexos_upload.save(ff, name="homicidio_%04d." % h.id)
                            h.arquivo = filename
                            db.session.commit()  
                        
                            flash(u'O arquivo foi enviado!', u'success')                        
                    except UploadNotAllowed:
                        db.session.rollback()
                        flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')
                        
                    db.session.commit()                                  
                    flash(u'Dados do homicídio atualizado com sucesso!', u'success')
                else:
                    flash(u'Houve um problema ao relatar esta violação de homicídio. Refaça o relato.', u'error')
                    
            else:
                if acao==u"Remover anexo": 
                    if h:
                        h.arquivo = None
                        db.session.commit()
                        
        else:
            flash(u"Verifique os erros no formulário abaixo.", u"error")                    

    return render_template('homicidio.html', f=f, d=d, homicidio=h)   
    
@app.route('/denuncia/pesquisar', methods=['GET', 'POST'])
@login_required
@checa_permissao('pesquisa-denuncia')
def pesquisar_denuncia():
    p = None
    
    q = db.session.query(Status.id, Status.status)  
    option_status = ([(str(x), y) for x,y in q.all()])
    
    if request.method == u'POST':
        f = PesquisarForm(request.form)   

        q = db.session.query(Cidade.cidade, Cidade.cidade)
        q = q.filter(Cidade.estado==f.estado.data)                            
        
        option_cidade = ([(x, y) for x,y in q.all()])                   
        f.cidade.choices = option_cidade    
        f.status.choices = option_status  
        if ('0', 'Qualquer estado') not in f.estado.choices:    
            f.estado.choices.insert(0, ('0', 'Qualquer estado'))
        if ('0', 'Qualquer cidade') not in f.cidade.choices:    
            f.cidade.choices.insert(0, ('0', 'Qualquer cidade'))     
      
        if f.validate():
        
            q = db.session.query(Denuncia)
            if f.numerodenuncia.data:
                q = q.filter(Denuncia.numero==f.numerodenuncia.data)
            if f.dtcriacaoinicio.data:
                q = q.filter(Denuncia.dtcriacao >= f.dtcriacaoinicio.data)                    
            if f.dtcriacaofim.data:
                q = q.filter(Denuncia.dtcriacao < (f.dtcriacaofim.data + datetime.timedelta(days=1)) )
            if f.dtocorinicio.data:
                q = q.filter(Denuncia.dtdenuncia >= f.dtocorinicio.data)                    
            if f.dtocorfim.data:
                q = q.filter(Denuncia.dtdenuncia < (f.dtocorfim.data + datetime.timedelta(days=1)) )
            if f.estado.data:
                if not f.estado.data == "0":
                    q = q.filter(Denuncia.estado==f.estado.data)
            if f.cidade.data:
                if not f.cidade.data == "0":
                    q = q.filter(Denuncia.cidade==f.cidade.data)
            if f.palavrachave.data:
                q = q.filter(or_(Denuncia.resumo.contains(f.palavrachave.data),Denuncia.descricao.contains(f.palavrachave.data)))   
            if f.status.data:
                q = q.filter(Denuncia.status_id==f.status.data)  
           
            try:
                page = int(request.form.get("pagina", 1))
            except ValueError:
                page = 1

            p = Paginator(q, cur_page=page, per_page=10)  
           
        else:
            flash(u"Verifique os erros no formulário abaixo.", u"error")
    else:        
        f = PesquisarForm()
        
    f.status.choices = option_status
    if ('0', 'Qualquer estado') not in f.estado.choices:    
        f.estado.choices.insert(0, ('0', 'Qualquer estado'))
    if ('0', 'Qualquer cidade') not in f.cidade.choices:    
        f.cidade.choices.insert(0, ('0', 'Qualquer cidade'))        
    
    
    return render_template('pesquisar.html', f=f, paginator=p)       
  
@app.route('/denuncia/workflow/', methods=['GET', 'POST'])
@app.route('/denuncia/workflow/<int:denuncia_id>/<string:acao>/', methods=['GET', 'POST'])
@login_required
@checa_permissao('gerencia-workflow')
def workflow(denuncia_id=0,acao=None):
    p = None
    d = None
    
    q = db.session.query(Status.id, Status.status)  
    option_status = ([(str(x), y) for x,y in q.all()])
    
    if request.method == 'POST':
        f = WorkflowForm(request.form)           
        f.status.choices = option_status  
        
        q = db.session.query(Cidade.cidade, Cidade.cidade)
        q = q.filter(Cidade.estado==f.estado.data)                            
        
        option_cidade = ([(x, y) for x,y in q.all()])                   
        f.cidade.choices = option_cidade    
        f.status.choices = option_status  
        if ('0', 'Qualquer estado') not in f.estado.choices:    
            f.estado.choices.insert(0, ('0', 'Qualquer estado'))
        if ('0', 'Qualquer cidade') not in f.cidade.choices:    
            f.cidade.choices.insert(0, ('0', 'Qualquer cidade'))     
        
        q = db.session.query(Denuncia)
        if f.validate():
            if f.numerodenuncia.data:
                q = q.filter(Denuncia.numero==f.numerodenuncia.data)
            if f.dtcriacaoinicio.data:
                q = q.filter(Denuncia.dtcriacao >= f.dtcriacaoinicio.data)                    
            if f.dtcriacaofim.data:
                q = q.filter(Denuncia.dtcriacao < (f.dtcriacaofim.data + datetime.timedelta(days=1)) )
            if f.dtocorinicio.data:
                q = q.filter(Denuncia.dtdenuncia >= f.dtocorinicio.data)                    
            if f.dtocorfim.data:
                q = q.filter(Denuncia.dtdenuncia < (f.dtocorfim.data + datetime.timedelta(days=1)) )
            if f.estado.data:
                if not f.estado.data == "0":
                    q = q.filter(Denuncia.estado==f.estado.data)
            if f.cidade.data:
                if not f.cidade.data == "0":
                    q = q.filter(Denuncia.cidade==f.cidade.data)
            if f.palavrachave.data:
                q = q.filter(or_(Denuncia.resumo.contains(f.palavrachave.data),Denuncia.descricao.contains(f.palavrachave.data)))   
            if f.status.data:
                q = q.filter(Denuncia.status_id.in_(f.status.data))  
            if f.dtlimiteinicio.data or f.dtlimitefim.data:
                q = q.options(joinedload_all(Denuncia.historico)) 
                if f.dtlimiteinicio.data:    
                    q = q.filter(Encaminhamento.dtretorno == None)
                    q = q.filter(Encaminhamento.dtlimite >= f.dtlimiteinicio.data)                    
                if f.dtlimitefim.data:
                    q = q.filter(Encaminhamento.dtretorno == None)
                    q = q.filter(Encaminhamento.dtlimite < f.dtlimitefim.data + datetime.timedelta(days=1))                
                                
        else:
            flash(u"Verifique os erros no formulário abaixo.", u"error")
    
        #q = q.options(joinedload_all(Denuncia.historico))                        
        
        try:
            page = int(request.form.get("pagina", 1))
        except ValueError:
            page = 1

        p = Paginator(q, cur_page=page, per_page=10)              
        
    else: 
        f = WorkflowForm()       
        f.status.choices = option_status    

        if ('0', 'Qualquer estado') not in f.estado.choices:    
            f.estado.choices.insert(0, ('0', 'Qualquer estado'))
        if ('0', 'Qualquer cidade') not in f.cidade.choices:    
            f.cidade.choices.insert(0, ('0', 'Qualquer cidade'))            
    
        if denuncia_id:
            d = db.session.query(Denuncia).get(denuncia_id)    
        
    if d:
    
        if acao==u"abrir":           

                q = db.session.query(Denuncia)
                q = q.filter(Denuncia.id==d.id) 
                p = Paginator(q, cur_page=1, per_page=30)                      
                
                if _controle_status(d,2):                
                    d.status_id = 2 # Aberta
                    
                    h = Historico(d.id)
                    h.acao_id = 1 # Abrir denuncia
                    db.session.add(h)                       
                    
                    db.session.commit()            
                else:
                    flash(u"A demanda %s já está aberta." %d.resumo, u"notice")
        else:
            if acao==u"reabrir": 
                if d.status_id ==4 or d.status_id ==5:
                    h = Historico(d.id)
                    h.acao_id = 6 # Reabrir a demanda 
                    db.session.add(h)                     
                
                    d.status_id = 2
                    db.session.commit()
                    flash(u"A demanda %s reaberta." %d.resumo, u"notice")                    
                else:
                    flash(u"Esta ação não é possível.", u"error")
            else:        
                flash(u"Esta ação não existe, favor tentar efetuar outra ação.", u"error")
            
    dthoje = datetime.datetime.today()
    dtlimite = dthoje + datetime.timedelta(days=30) 
    dtvencido = dthoje - datetime.timedelta(days=1)    
    
    return render_template('workflow.html', f=f,  paginator=p, dthoje=dthoje, dtlimite=dtlimite, dtvencido=dtvencido)     
    
def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj
    
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/', methods=['GET', 'POST'])
@login_required
@checa_permissao('faz-encaminhamento')
def fazer_encaminhamento(denuncia_id=None):
    d = None
    
    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)            
    
    q = db.session.query(TipoEncaminhamento.id, TipoEncaminhamento.tipo)
    option_tpencaminhamento = ([(str(x), y) for x,y in q.all()])                  
        
    q = db.session.query(Orgao.id, Orgao.orgao).order_by(Orgao.orgao)    
    option_orgao = ([(str(x), y) for x,y in q.all()])    
        
    if request.method == 'POST':
        f = EncaminhamentoForm(request.form) 
        
        f.tipo.choices = option_tpencaminhamento     
        f.orgao.choices = option_orgao    
        
        if f.validate():
            
            encaminhamento = { 
                'orgao_id': f.orgao.data,
                'tipo_id': f.tipo.data,
                'dtenvio': (f.dtenvio.data).strftime('%d/%m/%Y'),
                'dtlimite': (f.dtlimite.data).strftime('%d/%m/%Y')                    
            }               
            
            session['encaminhamento'] = encaminhamento
            
            if int(f.tipo.data) == 1:   #oficio            
                return redirect(url_for('encaminhamento_oficio',denuncia_id=d.id))                
            elif int(f.tipo.data) == 2: #telefonema
                return redirect(url_for('encaminhamento_telefonema',denuncia_id=d.id))                
            elif int(f.tipo.data) == 3: #reunião            
                return redirect(url_for('encaminhamento_reuniao',denuncia_id=d.id))                
            elif int(f.tipo.data) == 4: #email            
                return redirect(url_for('encaminhamento_email',denuncia_id=d.id))                
            else:                       #outros            
                return redirect(url_for('encaminhamento_generico',denuncia_id=d.id))                            
        else:
            flash(u"Verifique os erros no formulário abaixo.", u"error")                    
        
    else: 
        f = EncaminhamentoForm()      
        
        f.tipo.choices = option_tpencaminhamento     
        f.orgao.choices = option_orgao          
    
    return render_template('encaminhamento.html', f=f)     

def _controle_status(denuncia=None, status_id=None):
    if denuncia and status_id:                
        if status_id > denuncia.status_id:
            return status_id
        else:
            return None
    else:
        return None

def _altera_status(denuncia_id=None, status_id=None):
    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)
        if _controle_status(d,status_id):
            d.status_id = status_id
            db.session.commit()
            return True
        else:    
            return False
    return False           
    
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/oficio/<int:oficio_id>/editar', methods=['GET', 'POST'])
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/oficio/novo', methods=['GET', 'POST'])
@login_required
@checa_permissao('faz-encaminhamento')
def encaminhamento_oficio(denuncia_id=None, oficio_id=None):
    denuncia = None
    o = None
    editar = False
    
    f = OficioForm() 
    
    q = db.session.query(Orgao.id, Orgao.orgao).order_by(Orgao.orgao)    
    option_orgao = ([(str(x), y) for x,y in q.all()])    
    
    if oficio_id:
        o = db.session.query(Oficio).get(oficio_id)
        
        f.orgao.choices = option_orgao        

        if o:
            editar = True
            f.orgao.data = str(o.orgao_id)
            f.dtenvio.data = o.dtenvio
            f.dtlimite.data = o.dtlimite        
            f.numero.data = o.numero
            f.assunto.data = o.assunto
            f.obs.data = o.obs

    acao = request.form.get("acao")            
            
    if request.method == 'POST':        
        f = OficioForm(request.form) 
        
        if oficio_id:                
            f.orgao.choices = option_orgao
        else:
            del f.orgao
            del f.dtenvio
            del f.dtlimite        

        if f.validate(): 

            if acao==u"Salvar":     
        
                if o:            
                    try:
                        o.orgao_id = f.orgao.data
                        o.dtenvio = f.dtenvio.data
                        o.dtlimite = f.dtlimite.data                    
                        o.numero = f.numero.data
                        o.assunto = f.assunto.data
                        o.obs = f.obs.data                                
                    
                        ff = request.files.get('arquivo', None)
                        if ff:
                            filename = anexos_upload.save(ff, name="oficio_%04d." % o.id)
                            o.arquivo = filename
                    
                        db.session.commit() 
                    
                        flash(u"Ofício cadastrado com sucesso", u"success")   
                        return redirect(url_for('timeline',denuncia_id=denuncia_id))                            
                            
                    except UploadNotAllowed:                
                        db.session.rollback()                    
                        flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')       
     
                else:            
                    if session['encaminhamento']:                    
                        dictenc = session.pop('encaminhamento')                   
                        if dictenc:                    
                            try:         

                                h = Historico(denuncia_id)
                                h.acao_id = 2 # Fazer um encaminhamento
                                
                                db.session.add(h)
                                db.session.flush()  
                            
                                o = Oficio(h.id)                        
                                
                                o.orgao_id = dictenc['orgao_id']
                                o.tipo_id = dictenc['tipo_id']
                                o.dtenvio = datestring_to_date(dictenc['dtenvio'])
                                o.dtlimite =  datestring_to_date(dictenc['dtlimite'])
                                o.numero = f.numero.data
                                o.assunto = f.assunto.data
                                o.obs = f.obs.data   
                                o.dtcriacao = func.sysdate()                        
                                
                                db.session.add(o)
                                db.session.flush() 
                                
                                ff = request.files.get('arquivo', None)
                                if ff:
                                    filename = anexos_upload.save(ff, name="oficio_%04d." % o.id)
                                    o.arquivo = filename                            
                                    flash(u'O arquivo foi enviado!', u'success')
       
                            except UploadNotAllowed:                        
                                db.session.rollback()                            
                                flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')                   
                            db.session.commit()
                            _altera_status(denuncia_id,3)
                            flash(u"Ofício cadastrado com sucesso", u"success") 
                            
                            return redirect(url_for('timeline',denuncia_id=denuncia_id))
                    else:                
                        flash(u"Retorne ao histórico e tente novamente", u"success")
            
            if acao==u"Remover anexo": 
                if o:
                    o.arquivo = None
                    db.session.commit()
                    flash(u"Arquivo deletado!", u"success")
       
        else:        
            for field, errors in f.errors.items():   
                for error in errors:                    
                    flash(u'Erro %s no campo %s' %(field,error), u"error")  
                    
    return render_template('encaminhamento_oficio.html', f=f, oficio=o, editar=editar)     

@app.route('/denuncia/<int:denuncia_id>/encaminhamento/telefonema/<int:telefonema_id>/editar', methods=['GET', 'POST'])    
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/telefonema/novo', methods=['GET', 'POST'])
@login_required
@checa_permissao('faz-encaminhamento')
def encaminhamento_telefonema(denuncia_id=None, telefonema_id=None):
    denuncia = None
    t = None
    editar = False

    f = TelefonemaForm()  

    q = db.session.query(Orgao.id, Orgao.orgao).order_by(Orgao.orgao)    
    option_orgao = ([(str(x), y) for x,y in q.all()])    
            
    
    if telefonema_id:        
        t = db.session.query(Encaminhamento).get(telefonema_id)        
        
        f.orgao.choices = option_orgao
                
        if t:
            editar = True
            f.orgao.data = str(t.orgao_id)
            f.dtenvio.data = t.dtenvio
            f.dtlimite.data = t.dtlimite
            f.numero.data = t.numero
            f.destinatario.data = t.destinatario
            f.obs.data = t.obs   

    acao = request.form.get("acao")                
            
    if request.method == 'POST':    
        f = TelefonemaForm(request.form)

        if telefonema_id:                
            f.orgao.choices = option_orgao
        else:
            del f.orgao
            del f.dtenvio
            del f.dtlimite

        if f.validate():
        
            if acao==u"Salvar":     
                
                if t:   
                    t.orgao_id = f.orgao.data
                    t.dtenvio = f.dtenvio.data
                    t.dtlimite = f.dtlimite.data
                    t.numero = f.numero.data
                    t.destinatario = f.destinatario.data
                    t.obs = f.obs.data
                    
                    db.session.commit()
                    
                    flash(u"Telefonema cadastrado com sucesso", u"success")                
                    return redirect(url_for('timeline',denuncia_id=denuncia_id))                                                
                else:
                    if session['encaminhamento']:                    
                        dictenc = session.pop('encaminhamento')                   
                        
                        if dictenc:
                        
                            h = Historico(denuncia_id)
                            h.acao_id = 2 # Fazer um encaminhamento
                            
                            db.session.add(h)
                            db.session.flush()                      
                        
                            t = Telefonema(h.id)                        
                            
                            t.orgao_id = dictenc['orgao_id']
                            t.tipo_id = dictenc['tipo_id']
                            t.dtenvio = datestring_to_date(dictenc['dtenvio'])
                            t.dtlimite =  datestring_to_date(dictenc['dtlimite'])
                            t.numero = f.numero.data
                            t.destinatario = f.destinatario.data
                            t.obs = f.obs.data                
                            t.dtcriacao = func.sysdate()                        
                        
                            db.session.add(t)    
                            db.session.commit()  
                            _altera_status(denuncia_id,3)                    
                            flash(u"Telefonema cadastrado com sucesso", u"success")
                            
                            return redirect(url_for('timeline',denuncia_id=denuncia_id))
                    else:                
                        flash(u"Retorne ao histórico e tente novamente", u"success")
                    
        else:
            for field, errors in f.errors.items():   
                for error in errors:                    
                    flash(u'Erro %s no campo %s' %(field,error), u"error")  

    return render_template('encaminhamento_telefonema.html', f=f, editar=editar)  


@app.route('/denuncia/<int:denuncia_id>/encaminhamento/reuniao/<int:reuniao_id>/editar', methods=['GET', 'POST'])    
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/reuniao/novo', methods=['GET', 'POST'])
@login_required
@checa_permissao('faz-encaminhamento')
def encaminhamento_reuniao(denuncia_id=None, reuniao_id=None):
    denuncia = None
    r = None
    editar = False    
    
    f = ReuniaoForm()
    
    q = db.session.query(Orgao.id, Orgao.orgao).order_by(Orgao.orgao)    
    option_orgao = ([(str(x), y) for x,y in q.all()])        
    
    if reuniao_id:
        r = db.session.query(Reuniao).get(reuniao_id)
        
        f.orgao.choices = option_orgao                

        if r:
            editar = True
            f.orgao.data = str(r.orgao_id)
            f.dtenvio.data = r.dtenvio
            f.dtlimite.data = r.dtlimite       
            f.pauta.data = r.pauta
            f.participantes.data = r.participantes 
            f.obs.data = r.obs  

    acao = request.form.get("acao")
            
    if request.method == 'POST':    
        f = ReuniaoForm(request.form)
        
        if reuniao_id:                
            f.orgao.choices = option_orgao
        else:
            del f.orgao
            del f.dtenvio
            del f.dtlimite           
        
        if f.validate():            
        
            if acao==u"Salvar":      
        
                if r:                
                    try:
                        r.orgao_id = f.orgao.data
                        r.dtenvio = f.dtenvio.data
                        r.dtlimite = f.dtlimite.data                        
                        r.pauta = f.pauta.data
                        r.participantes = f.participantes.data
                        r.obs = f.obs.data                
                    
                        ff = request.files.get('arquivo', None)
                        if ff:
                            filename = anexos_upload.save(ff, name="reuniao_%04d." % r.id)
                            r.arquivo = filename 
                            
                        db.session.commit()  
                        flash(u"Reunião cadastrada com sucesso", u"success")                        
                        
                        return redirect(url_for('timeline',denuncia_id=denuncia_id))
                            
                    except UploadNotAllowed:                
                        db.session.rollback()                    
                        flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')                
                else:
                
                    if session['encaminhamento']:                    
                        dictenc = session.pop('encaminhamento')                   
                        if dictenc:                    
                            try:   

                                h = Historico(denuncia_id)
                                h.acao_id = 2 # Fazer um encaminhamento
                                
                                db.session.add(h)
                                db.session.flush() 
                                
                                r = Reuniao(h.id)                        
                                
                                r.orgao_id = dictenc['orgao_id']
                                r.tipo_id = dictenc['tipo_id']
                                r.dtenvio = datestring_to_date(dictenc['dtenvio'])
                                r.dtlimite =  datestring_to_date(dictenc['dtlimite'])
                                r.pauta = f.pauta.data
                                r.participantes = f.participantes.data
                                r.obs = f.obs.data
                                r.dtcriacao = func.sysdate()
     
                                db.session.add(r)
                                db.session.flush() 
                            
                                ff = request.files.get('arquivo', None)
                                if ff:
                                    filename = anexos_upload.save(ff, name="reuniao_%04d." % r.id)
                                    r.arquivo = filename                            
                                    flash(u'O arquivo foi enviado!', u'success')
                                
                                db.session.commit()  
                                _altera_status(denuncia_id,3)
                                flash(u"Reunião cadastrada com sucesso", u"success") 
                            
                            except UploadNotAllowed:                        
                                db.session.rollback()                            
                                flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')       
                                        
                            return redirect(url_for('timeline',denuncia_id=denuncia_id))
                    else:                
                        flash(u"Retorne ao histórico e tente novamente", u"success")
            
            if acao==u"Remover anexo": 
                if r:
                    r.arquivo = None
                    db.session.commit()
                    flash(u"Arquivo deletado!", u"success")
                
        else:
            for field, errors in f.errors.items():   
                for error in errors:                    
                    flash(u'Erro %s no campo %s' %(field,error), u"error")  
                    
    return render_template('encaminhamento_reuniao.html', f=f, reuniao=r, editar=editar)  
    
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/email/<int:email_id>/editar', methods=['GET', 'POST'])    
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/email/novo', methods=['GET', 'POST'])
@login_required
@checa_permissao('faz-encaminhamento')
def encaminhamento_email(denuncia_id=None, email_id=None):
    denuncia = None
    e = None 
    editar = False      

    f = EmailForm()     
    
    q = db.session.query(Orgao.id, Orgao.orgao).order_by(Orgao.orgao)    
    option_orgao = ([(str(x), y) for x,y in q.all()])       

    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)  

        f.orgao.choices = option_orgao    

    if g.user:
        f.de.data = g.user.email
    
    if email_id:
        e = db.session.query(Email).get(email_id)

        if e:
            editar = True
            f.orgao.data = str(e.orgao_id)
            f.dtenvio.data = e.dtenvio
            f.dtlimite.data = e.dtlimite            
            f.de.data = e.de 
            f.para.data = e.para 
            f.assunto.data = e.assunto 
            f.texto.data = e.texto  
    
    acao = request.form.get("acao")         
            
    if request.method == 'POST':    
        f = EmailForm(request.form) 
        
        if email_id:                
            f.orgao.choices = option_orgao
        else:
            del f.orgao
            del f.dtenvio
            del f.dtlimite             
        
        if f.validate(): 

            if acao==u"Enviar":     
        
                if e:                
                    try:
                        e.orgao_id = f.orgao.data
                        e.dtenvio = f.dtenvio.data
                        e.dtlimite = f.dtlimite.data                        
                        e.de = f.de.data
                        e.para = f.para.data
                        e.assunto = f.assunto.data
                        e.texto = f.texto.data                
                    
                        ff = request.files.get('arquivo', None)
                        if ff:
                            filename = anexos_upload.save(ff, name="email%04d." % e.id)
                            e.arquivo = filename

                        t = render_template('encaminhamento-email.txt', denuncia=d, encaminhamento=e, usuario=g.user)          
                                          
                        if e.arquivo:
                            filepath = anexos_upload.path(filename)
                            msg = MIMEMultipart()
                            part1 = MIMEText(t, 'html', 'utf-8')                                                
                            msg.attach(part1)                        
                            part2 = MIMEApplication(open(filepath,"rb").read())                                   
                            part2.add_header('Content-Disposition', 'attachment', filename="%s" %os.path.basename(filepath))
                            msg.attach(part2)  
                        else:
                            msg = MIMEText(t, 'html', 'utf-8')
                                            
                        from_header = 'sistema@cnddh.org.br'
                        subject = e.assunto
                        email_to = [e.para,]
                        email_cc = [g.user.email,]
                        
                        msg['From'] = from_header
                        msg['Subject'] = '[Encaminhamento] ' + subject
                        msg['To'] = ', '.join(email_to)
                        if email_cc:
                            msg['Cc'] = ', '.join(email_cc)
                        msg['Reply-To'] = g.user.email
                            
                        enviado = envia_email(from_header,email_to,msg.as_string())
                        
                        if enviado:                    
                            db.session.commit()
                            flash(u"Email reenviado com sucesso", u"success")
                        else:
                            db.session.rollback()
                            flash(u"Email não foi enviado", u"error")
        
                        return redirect(url_for('timeline',denuncia_id=denuncia_id))

                    except UploadNotAllowed:                
                        db.session.rollback()                    
                        flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')       
                
                else:
                
                    if session['encaminhamento']:                    
                        dictenc = session.pop('encaminhamento')                   
                        if dictenc:                    
                            try:
                                h = Historico(denuncia_id)
                                h.acao_id = 2 # Fazer um encaminhamento
                                
                                db.session.add(h)
                                db.session.flush()                         
                            
                                e = Email(h.id)                            
                                e.orgao_id = dictenc['orgao_id']
                                e.tipo_id = dictenc['tipo_id']
                                e.dtenvio = datestring_to_date(dictenc['dtenvio'])
                                e.dtlimite =  datestring_to_date(dictenc['dtlimite'])
                                e.de = f.de.data
                                e.para = f.para.data
                                e.assunto = f.assunto.data
                                e.texto = f.texto.data                
                                e.dtcriacao = func.sysdate()                                                    
                                
                                db.session.add(e)      
                                db.session.flush() 
                            
                                ff = request.files.get('arquivo', None)
                                if ff:
                                    filename = anexos_upload.save(ff, name="email%04d." % e.id)
                                    e.arquivo = filename
                                    flash(u'O arquivo foi enviado!', u'success')
                                
                                db.session.commit() 
                                _altera_status(denuncia_id,3)
                                
                                t = render_template('encaminhamento-email.txt', denuncia=d, encaminhamento=e, usuario=g.user)          
                                                  
                                if e.arquivo:
                                    filepath = anexos_upload.path(filename)
                                    msg = MIMEMultipart()
                                    part1 = MIMEText(t, 'html', 'utf-8')                                                
                                    msg.attach(part1)                        
                                    part2 = MIMEApplication(open(filepath,"rb").read())                                   
                                    part2.add_header('Content-Disposition', 'attachment', filename="%s" %os.path.basename(filepath))
                                    msg.attach(part2)  
                                else:
                                    msg = MIMEText(t, 'html', 'utf-8')
                                                    
                                from_header = 'sistema@cnddh.org.br'
                                subject = e.assunto
                                email_to = [e.para,]
                                #email_cc = [g.user.email,]
                                email_cc = None
                                
                                msg['From'] = from_header
                                msg['Subject'] = '[Encaminhamento] ' + subject
                                msg['To'] = ', '.join(email_to)
                                if email_cc:
                                    msg['Cc'] = ', '.join(email_cc)
                                msg['Reply-To'] = g.user.email
                                    
                                enviado = envia_email(from_header,email_to,msg.as_string())
                                
                                if enviado:                    
                                    db.session.commit()
                                    flash(u"Email enviado com sucesso", u"success")
                                else:
                                    db.session.rollback()
                                    flash(u"Email não foi enviado", u"error")
                                                        
                                return redirect(url_for('timeline',denuncia_id=denuncia_id))
                            
                            except UploadNotAllowed:                        
                                db.session.rollback()                            
                                flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')       
                                        
                            return redirect(url_for('timeline',denuncia_id=denuncia_id))
                    else:                
                        flash(u"Retorne ao histórico e tente novamente", u"success")
                
        else:
            for field, errors in f.errors.items():   
                for error in errors:                    
                    flash(u'Erro %s no campo %s' %(field,error), u"error")  

        if acao==u"Remover anexo": 
            if e:
                e.arquivo = None
                db.session.commit()
                flash(u"Arquivo deletado!", u"success")
                   
            
    return render_template('encaminhamento_email.html', f=f,email=e, editar=editar)   

@app.route('/denuncia/<int:denuncia_id>/encaminhamento/generico/<int:generico_id>/editar', methods=['GET', 'POST'])    
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/generico/novo', methods=['GET', 'POST'])
@login_required
@checa_permissao('faz-encaminhamento')
def encaminhamento_generico(denuncia_id=None, generico_id=None):
    denuncia = None
    g = None
    editar = False
    
    f = GenericoForm() 
    
    q = db.session.query(Orgao.id, Orgao.orgao).order_by(Orgao.orgao)    
    option_orgao = ([(str(x), y) for x,y in q.all()])           
    
    if generico_id:
        g = db.session.query(Generico).get(generico_id)
        
        f.orgao.choices = option_orgao          

        if g:
            editar = True
            f.orgao.data = str(g.orgao_id)
            f.dtenvio.data = g.dtenvio
            f.dtlimite.data = g.dtlimite          
            f.obs.data = g.obs

    acao = request.form.get("acao")            
            
    if request.method == 'POST':    
        f = GenericoForm(request.form) 
        
        if generico_id:                
            f.orgao.choices = option_orgao
        else:
            del f.orgao
            del f.dtenvio
            del f.dtlimite           
        
        if f.validate():   

            if acao==u"Salvar":     
        
                if g:            
                    try:
                        g.orgao_id = f.orgao.data
                        g.dtenvio = f.dtenvio.data
                        g.dtlimite = f.dtlimite.data                      
                        g.obs = f.obs.data             
                        
                        ff = request.files.get('arquivo', None)
                        if ff:
                            filename = anexos_upload.save(ff, name="generico_%04d." % g.id)
                            g.arquivo = filename
                            
                        db.session.commit()
                        flash(u"Encaminhamento genérico cadastrada com sucesso", u"success") 
                    
                    except UploadNotAllowed:                        
                        db.session.rollback()                    
                        flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')                     
                    
                    return redirect(url_for('timeline',denuncia_id=denuncia_id))
                    
                else:            
                    if session['encaminhamento']:                    
                        dictenc = session.pop('encaminhamento')                   
                        if dictenc:                    
                            try:
                                h = Historico(denuncia_id)
                                h.acao_id = 2 # Fazer um encaminhamento
                                
                                db.session.add(h)
                                db.session.flush()                          
                            
                                g = Generico(h.id)
                                g.orgao_id = dictenc['orgao_id']
                                g.tipo_id = dictenc['tipo_id']
                                g.dtenvio = datestring_to_date(dictenc['dtenvio'])
                                g.dtlimite =  datestring_to_date(dictenc['dtlimite'])
                                g.obs = f.obs.data
                                g.dtcriacao = func.sysdate()                                                                                
                                
                                db.session.add(g)      
                                db.session.flush() 
                            
                                ff = request.files.get('arquivo', None)
                                if ff:
                                    filename = anexos_upload.save(ff, name="generico_%04d." % g.id)
                                    g.arquivo = filename
                                    flash(u'O arquivo foi enviado!', u'success')
                                    
                                db.session.commit()
                                _altera_status(denuncia_id,3)
                                flash(u"Encaminhamento genérico cadastrada com sucesso", u"success")                                           
                                return redirect(url_for('timeline',denuncia_id=denuncia_id))
                            
                            except UploadNotAllowed:                        
                                db.session.rollback()                            
                                flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')       
                                        
                            return redirect(url_for('timeline',denuncia_id=denuncia_id))
                    else:                
                        flash(u"Retorne ao histórico e tente novamente", u"success")            

            if acao==u"Remover anexo": 
                if g:
                    g.arquivo = None
                    db.session.commit()
                    flash(u"Arquivo deletado!", u"success")
                               
        else:        
            for field, errors in f.errors.items():   
                for error in errors:                    
                    flash(u'Erro %s no campo %s' %(field,error), u"error")                       

    return render_template('encaminhamento_generico.html', f=f, generico=g, editar=editar)
    
todos_encaminhamentos = with_polymorphic(Encaminhamento, [Oficio, Telefonema, Reuniao, Email, Generico])


@app.route('/denuncia/<int:denuncia_id>/cancelar/', methods=['GET', 'POST'])
@login_required
@checa_permissao('cancela-denuncia')
def cancelar_denuncia(denuncia_id=None):
    d = None
    
    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)            
        
    if request.method == 'POST':
        f = MotivoForm(request.form)         
        
        if f.validate():

            if _controle_status(d,4):
                h = Historico(denuncia_id)
                h.acao_id = 4 #Cancelar denuncia
                h.motivo = f.motivo.data
                
                d.status_id = 4 #Cancelada
                                
                db.session.add(h)
                db.session.commit()          
                
                flash(u"Denúncia cancelada.", u"success")
                return redirect(url_for('timeline',denuncia_id=d.id))
            else:
                flash(u"Denúncia não pode ser cancelada. A mudança de status não prevista, pode que esta denúncia já tenho sido cancelada.", u"error")
                
        else:
            flash(u"Verifique os erros no formulário abaixo.", u"error")                    
        
    else: 
        f = MotivoForm()      
    
    return render_template('cancelar.html', f=f, d=d)   
    
@app.route('/denuncia/<int:denuncia_id>/fechar/', methods=['GET', 'POST'])
@login_required
@checa_permissao('fecha-denuncia')
def fechar_denuncia(denuncia_id=None):
    d = None
    
    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)            
        
    if request.method == 'POST':
        f = MotivoForm(request.form)         
        
        if f.validate():
        
            if _controle_status(d,5):
                h = Historico(denuncia_id)
                h.acao_id = 5 #Fechar denuncia
                h.motivo = f.motivo.data
                                
                d.status_id = 5 #Fechada
                                
                db.session.add(h)
                db.session.commit()          
                
                flash(u"Denúncia fechada e não poderá mais fazer encaminhamentos e receber retornos.", u"success")
                return redirect(url_for('timeline',denuncia_id=d.id))
            else:
                flash(u"Denúncia não pode ser fechada. Esta mudança de status não está prevista, pode que esta denúncia já tenho sido fechada.", u"error")
                
        else:
            flash(u"Verifique os erros no formulário abaixo.", u"error")                    
        
    else: 
        f = MotivoForm()      
    
    return render_template('fechar.html', f=f, d=d)       

    
@app.route('/denuncia/<int:denuncia_id>/timeline', methods=['GET', 'POST'])
@app.route('/denuncia/<int:denuncia_id>/timeline/historico/<int:historico_id>/deletar', methods=['GET', 'POST'])
@app.route('/denuncia/<int:denuncia_id>/timeline/historico/<int:historico_id>/retorno/<int:retorno_id>/deletar', methods=['GET', 'POST'])
@login_required
@checa_permissao('visualiza-timeline')
def timeline(denuncia_id=None,historico_id=None,retorno_id=None):    
    denuncia = None
    
    if denuncia_id:
        q = db.session.query(Denuncia).filter(Denuncia.id==denuncia_id)      
        q = q.options(joinedload_all(Denuncia.historico))        
    
        denuncia = q.one()      

    dtatual = datetime.datetime.today()  
    
    if historico_id and retorno_id:
        r = db.session.query(Retorno).get(retorno_id) 
        db.session.delete(r)
        db.session.commit()
        flash(u"Retorno deletado!", u"success")
        return redirect(url_for('timeline',denuncia_id=denuncia_id))          
    elif historico_id and not retorno_id:
        h = db.session.query(Historico).get(historico_id) 
        db.session.delete(h)
        db.session.commit()
        flash(u"Encaminhamento deletado!", u"success")
        return redirect(url_for('timeline',denuncia_id=denuncia_id))         
       
    return render_template('timeline.html', denuncia=denuncia, dtatual=dtatual)      

@app.route('/denuncia/<int:denuncia_id>/encaminhamento/<int:encaminhamento_id>/retorno/<int:retorno_id>/editar', methods=['GET', 'POST'])
@app.route('/denuncia/<int:denuncia_id>/encaminhamento/<int:encaminhamento_id>/retorno/novo', methods=['GET', 'POST'])
@login_required
@checa_permissao('recebe-retorno')
def receber_retorno(denuncia_id=None, encaminhamento_id=None, retorno_id=None):
    denuncia = None
    e = None
    r = None
   
    if denuncia_id:
        d = db.session.query(Denuncia).get(denuncia_id)     
   
    q = db.session.query(TipoRetorno.id, TipoRetorno.nome).order_by(TipoRetorno.nome)    
    option_retorno = []
    option_retorno.extend([(str(x), y) for x,y in q.all()])      
    
    f = RetornoForm()      
    f.retorno.choices = option_retorno        
    
    if retorno_id:
        r = db.session.query(Retorno).get(retorno_id)    

        if r:
            f.descricao.data = r.descricao      
            f.retorno.data = str(r.tiporetorno_id)  
            f.dtretorno.data = r.dtretorno
              
        if r.tiporetorno.tipo =='retornopessoasassistidas':
            lista = r.tipoassistencia
            for i in lista:
                if not i:
                    lista.remove(i)
            f.tipoassistencia.data = lista

        elif r.tiporetorno.tipo =='retornoinquerito': 
            f.ip.data = r.ip
            f.situacaoip.data = r.situacao
            f.motivo.data = r.motivo
                
        elif r.tiporetorno.tipo =='retornoprocesso':    
            f.np.data = r.np
            f.situacaop.data = r.situacao
            
        elif r.tiporetorno.tipo =='retornobo':
            f.bo.data = r.bo
        
        elif r.tiporetorno.tipo =='retornorco':
            f.rco.data = r.rco

        elif r.tiporetorno.tipo =='retornoreds':
            f.reds.data = r.reds
            
        elif r.tiporetorno.tipo =='retornopoliticapsr':
            lista = r.tipopolitica
            for i in lista:
                if not i:
                    lista.remove(i)
            f.tipopolitica.data = lista      

        else:
            f.observacao.data = r.observacao            
                
    if denuncia_id and encaminhamento_id:
        e = db.session.query(Encaminhamento).get(encaminhamento_id)        
        
    acao = request.form.get("acao")                 

    if request.method == 'POST':
        f = RetornoForm(request.form) 
        f.retorno.choices = option_retorno
        f.tipoassistencia.choices = tipoassistencia_choices
        f.tipopolitica.poices = politicas_choices
        
        if f.validate():
        
            if acao==u"Salvar":    
        
                if e:
                
                    try:         

                        tr = db.session.query(TipoRetorno).get(f.retorno.data)
                        if tr:
                        
                            if tr.tipo =='retornopessoasassistidas':
                                if not retorno_id:
                                    r = RetornoPessoasassistidas(e.id)
                                aux = ''
                                for ta in f.tipoassistencia.data:
                                    aux = aux + ',' + ta
                                r.tipoassistencia = aux 
                                
                            elif tr.tipo =='retornoinquerito': 
                                if not retorno_id:
                                    r = RetornoInquerito(e.id)
                                r.ip = f.ip.data
                                r.situacao = f.situacaoip.data
                                r.motivo = f.motivo.data
                                
                            elif tr.tipo =='retornoprocesso':    
                                if not retorno_id:
                                    r = RetornoProcesso(e.id)
                                r.np = f.np.data
                                r.situacao = f.situacaop.data   
                                
                            elif tr.tipo =='retornobo':
                                if not retorno_id:
                                    r = RetornoBO(e.id)
                                r.bo = f.bo.data                        
                   
                            elif tr.tipo =='retornorco':
                                if not retorno_id:
                                    r = RetornoRCO(e.id)
                                r.rco = f.rco.data

                            elif tr.tipo =='retornoreds':
                                if not retorno_id:
                                    r = RetornoREDS(e.id)
                                e.reds = f.reds.data
                                
                            elif tr.tipo =='retornopoliticapsr':
                                if not retorno_id:
                                    r = RetornoPoliticaPSR(e.id)
                                aux = ''
                                for p in f.tipopolitica.data:
                                    aux = aux + ',' + p
                                r.tipopolitica = aux                  
                            
                            else:
                                if not retorno_id:
                                    r = RetornoGenerico(e.id)
                                r.observacao = f.observacao.data
                            
                            if r:
                                r.descricao = f.descricao.data     
                                r.tiporetorno_id = f.retorno.data                      
                                r.dtretorno = f.dtretorno.data     
                           
                                e.dtretorno = r.dtretorno
                            
                                db.session.add(r)      
                                db.session.flush()                                                             
                            
                                ff = request.files.get('arquivo', None)
                                if ff:
                                    filename = anexos_upload.save(ff, name="retorno_%04d." % r.id)
                                    r.arquivo = filename

                    except UploadNotAllowed:
                        db.session.rollback()
                        flash(u'O upload deste arquivo não é permitido devido questões de segurança, altere o tipo do arquivo para as extensões permitidas.', u'error')
                    
                    db.session.commit()
                    flash(u"Retorno  cadastrado com sucesso", u"success")
                    
                    return redirect(url_for('timeline',denuncia_id=denuncia_id))
        
            if acao==u"Remover anexo": 
                if r:
                    r.arquivo = None
                    db.session.commit()
                    flash(u"Arquivo deletado!", u"success")
        
        else:
            for field, errors in f.errors.items():   
                for error in errors:                    
                    flash(u'Erro %s no campo %s' %(field,error), u"error")                    
                   
    return render_template('retorno.html',  f=f, d=d, retorno=r)     
  
@app.route('/denuncia/relatorio/graficos/violacaoporestado', methods=['GET', 'POST'])
@login_required
def grafico_violacaoporestado():    
    f = GraficoViolacaoForm()
    
    q = db.session.query(TipoViolacao.macrocategoria, TipoViolacao.macrocategoria)    
    q = q.group_by(TipoViolacao.macrocategoria)

    option_tpviolacao = ([(x, y) for x,y in q.all()])      
    
    f.macrocategoria.choices = option_tpviolacao
            
    if f.macrocategoria:
        q = db.session.query(TipoViolacao.id, TipoViolacao.microcategoria)    
        q = q.filter(TipoViolacao.macrocategoria==f.macrocategoria.data)       

    return render_template('grafico_violacaoporestado.html', f=f)     
    
@app.route('/denuncia/relatorio/graficos/violacaoporcidade', methods=['GET', 'POST'])
@login_required
def grafico_violacaoporcidade():    
    f = GraficoViolacaoForm()
    
    q = db.session.query(TipoViolacao.macrocategoria, TipoViolacao.macrocategoria)    
    q = q.group_by(TipoViolacao.macrocategoria)

    option_tpviolacao = ([(x, y) for x,y in q.all()])      
    
    f.macrocategoria.choices = option_tpviolacao
            
    if f.macrocategoria:
        q = db.session.query(TipoViolacao.id, TipoViolacao.microcategoria)    
        q = q.filter(TipoViolacao.macrocategoria==f.macrocategoria.data)       

    return render_template('grafico_violacaoporcidade.html', f=f)       
    
@app.route('/denuncia/relatorio/graficos/violacaopormacro', methods=['GET', 'POST'])
@login_required
def grafico_violacaopormacro():    
    f = GraficoViolacaoForm()
    
    q = db.session.query(TipoViolacao.macrocategoria, TipoViolacao.macrocategoria)    
    q = q.group_by(TipoViolacao.macrocategoria)

    option_tpviolacao = ([(x, y) for x,y in q.all()])      
    
    f.macrocategoria.choices = option_tpviolacao

    return render_template('grafico_violacaopormacro.html', f=f)
    
@app.route('/denuncia/relatorio/graficos/violacaoportempo', methods=['GET', 'POST'])
@login_required
def grafico_violacaoportempo():    
    f = GraficoViolacaoForm()
    
    q = db.session.query(TipoViolacao.macrocategoria, TipoViolacao.macrocategoria)    
    q = q.group_by(TipoViolacao.macrocategoria)

    option_tpviolacao = ([(x, y) for x,y in q.all()])      
    
    f.macrocategoria.choices = option_tpviolacao
            
    if f.macrocategoria:
        q = db.session.query(TipoViolacao.id, TipoViolacao.microcategoria)    
        q = q.filter(TipoViolacao.macrocategoria==f.macrocategoria.data)   

    return render_template('grafico_violacaoportempo.html', f=f)       
    
@app.route('/denuncia/relatorio/graficos/violacaoporsupeito', methods=['GET', 'POST'])
@login_required
def grafico_violacaoporsuspeito():    
    f = GraficoViolSuspForm()
    
    q = db.session.query(TipoViolacao.macrocategoria, TipoViolacao.macrocategoria)    
    q = q.group_by(TipoViolacao.macrocategoria)

    option_tpviolacao = ([(x, y) for x,y in q.all()])      
    
    f.macrocategoria.choices = option_tpviolacao
            
    if f.macrocategoria:
        q = db.session.query(TipoViolacao.id, TipoViolacao.microcategoria)    
        q = q.filter(TipoViolacao.macrocategoria==f.macrocategoria.data)  

    q = db.session.query(TipoSuspeito.tipo,TipoSuspeito.tipo)
    q = q.group_by(TipoSuspeito.tipo)
    
    option_tipo = [(u"", u"")]
    option_tipo.extend([(x, y) for x,y in q.all()])           
    
    f.tiposuspeito.choices = option_tipo
    
    return render_template('grafico_violacaoporsuspeito.html', f=f)       
    
@app.route('/permissoes/permissoes/', methods=['GET', 'POST'])
@app.route('/permissoes/permissoes/<int:permissao>', methods=['GET', 'POST'])
@login_required
@checa_permissao('cria-permissoes')
def permissoes_permissoes(permissao=None):
    if request.method == 'POST':
        f = PermissaoForm(request.form)
        if f.validate():
            p = Permissao()
            f.populate_obj(p)
            db.session.add(p)
            try:
                db.session.commit()
                flash(u'Permissão criada com sucesso.', u'success')
            except:
                db.session.rollback()
                flash(u'Ocorreu um erro - verifique se o nome é unico.', u'error')
            f = PermissaoForm()
    else:
        f = PermissaoForm()

    q = db.session.query(Permissao).order_by(Permissao.id)
    permissoes = q.all()
    return render_template('permissoes_permissoes.html', permissoes=permissoes, f=f)
    
@app.route('/permissoes/perfis/', methods=['GET', 'POST'])
@login_required
@checa_permissao('altera-perfil')
def permissoes_perfis():
    if request.method == 'POST':
        f = PermissaoForm(request.form)
        if f.validate():
            if g.user.checa_permissao('cria-perfil'):
                p = Perfil()
                f.populate_obj(p)
                db.session.add(p)
                try:
                    db.session.commit()
                    flash(u'Perfil criado com sucesso.', u'success')
                except:
                    db.session.rollback()
                    flash(u'Ocorreu um erro.', u'error')
            else:
                abort(401)
            f = PermissaoForm()
    else:
        f = PermissaoForm()

    q = db.session.query(Perfil)
    perfis = q.all()
    return render_template('permissoes_perfis.html', perfis=perfis, f=f)  
    
@app.route('/permissoes/perfis/<int:perfil>', methods=['GET', 'POST'])
@login_required
@checa_permissao('altera-perfil')
def permissoes_perfis_edit(perfil):
    q = db.session.query(Perfil)
    q = q.filter(Perfil.id == perfil)
    p = q.first()
    if not p:
        abort(404)

    if request.method == 'POST':
        f = PermissaoForm(request.form, obj=p)
        if f.validate():
            if f.nome.data != p.nome:
                p.nome = f.nome.data
            
            if f.descricao.data != p.descricao:
                p.descricao = f.descricao.data
                
            _perms = request.form.getlist('perms')
            perms = [int(x) for x in _perms]
            for pt in p.permissoesperfis:
                if pt.permissao_id in perms:
                    #print "permissao %d existe no perfil, ignorando" % pt.permissao_id
                    perms.remove(pt.permissao_id)
                else:
                    #print "removendo permissao %d do perfil" % pt.permissao_id
                    #remove permissao
                    db.session.delete(pt)

            #print "Permissoes a serem adicionadas: ", perms #DEBUG
            for p_id in perms:
                np = PermissaoPerfil()
                np.permissao_id = p_id
                np.perfil_id = perfil
                np.tipo = 0
                db.session.add(np)

            flash(u'Permissões alteradas.', u'success')
            db.session.commit()
            
    else:
        f = PermissaoForm(obj = p)

    q = db.session.query(Permissao, PermissaoPerfil)
    q = q.outerjoin(PermissaoPerfil, and_(PermissaoPerfil.permissao_id == Permissao.id, PermissaoPerfil.perfil_id == perfil))
    q = q.order_by(Permissao.nome)
    permissoes = q.all()

    return render_template('permissoes_perfis_edit.html', f=f, permissoes=permissoes, p=p)      

@app.route('/permissoes/usuarios/', methods=['GET', 'POST'])
@login_required
@checa_permissao('altera-permissoes')
def permissoes_usuarios():
    usuarios = None
    if request.method == 'POST':
        f = PesquisaUsuarioForm(request.form)
        if f.validate():
            login = (f.login.data or '').strip()
            nome =  (f.nome.data  or '').strip()
            #email = (f.email.data or '').strip()

            q = db.session.query(Usuario)
            
            if login:
                q = q.filter(Usuario.login == login)
            if nome:
                q = q.filter(Usuario.nome.contains(nome))
            #if email:
            #    q = q.filter(Usuario.email.contains(email))    

            usuarios = q.all()
            
        else:
            flash(u'Nenhum campo de busca foi preenchido. Busca não realizada', u'notice')
            
    else:
        f = PesquisaUsuarioForm()

    return render_template('permissoes_usuarios.html', form=f, usuarios=usuarios)
    
@app.route('/permissoes/usuarios/<int:usuario>', methods=['GET', 'POST'])
@login_required
@checa_permissao('altera-permissoes')
def permissoes_usuarios_permissoes_edit(usuario):
    if request.method == 'POST':
        q = db.session.query(PermissaoUsuario)
        q = q.filter(PermissaoUsuario.usuario_id == usuario)
        permissoesusuarios = q.all()
        
        _perms = request.form.getlist('perms')
        perms = [int(x) for x in _perms]
        for pt in permissoesusuarios:
            if pt.permissao_id in perms:
                #print "permissao %d existe no perfil, ignorando" % pt.permissao_id
                perms.remove(pt.permissao_id)
            else:
                #print "removendo permissao %d do perfil" % pt.permissao_id
                #remove permissao
                db.session.delete(pt)

        #print "Permissoes a serem adicionadas: ", perms #DEBUG
        for p_id in perms:
            np = PermissaoUsuario()
            np.permissao_id = p_id
            np.usuario_id = usuario
            np.tipo = 0
            db.session.add(np)

        flash(u'Permissões alteradas.', u'success')
        db.session.commit()

    q = db.session.query(Permissao, PermissaoUsuario)
    q = q.outerjoin(PermissaoUsuario, and_(PermissaoUsuario.permissao_id == Permissao.id, PermissaoUsuario.usuario_id == usuario))
    q = q.order_by(Permissao.nome)
    permissoes = q.all()
    
    if usuario:
        u = db.session.query(Usuario).get(usuario)

    return render_template('permissoes_usuarios_permissoes_edit.html', permissoes=permissoes, u=u)
    
@app.route('/permissoes/usuarios/<int:usuario>/perfis', methods=['GET', 'POST'])
@login_required
@checa_permissao('altera-perfil')
def permissoes_usuarios_perfis_edit(usuario):
    if request.method == 'POST':
        q = db.session.query(PerfilUsuario)
        q = q.filter(PerfilUsuario.usuario_id == usuario)
        perfisusuarios = q.all()
        
        _perfs = request.form.getlist('perfs')
        perfs = [int(x) for x in _perfs]
        for pt in perfisusuarios:
            if pt.perfil_id in perfs:
                perfs.remove(pt.perfil_id)
            else:
                #print "removendo permissao %d do perfil" % pt.permissao_id
                #remove permissao
                db.session.delete(pt)

        #print "Permissoes a serem adicionadas: ", perms #DEBUG
        for p_id in perfs:
            np = PerfilUsuario()
            np.perfil_id = p_id
            np.usuario_id = usuario
            db.session.add(np)

        flash(u'Perfis alterados.', u'success')
        db.session.commit()

    q = db.session.query(Perfil, PerfilUsuario)
    q = q.outerjoin(PerfilUsuario, and_(PerfilUsuario.perfil_id == Perfil.id, PerfilUsuario.usuario_id == usuario))
    q = q.order_by(Perfil.nome)
    perfis = q.all()
    
    if usuario:
        u = db.session.query(Usuario).get(usuario)    

    return render_template('permissoes_usuarios_perfis_edit.html', perfis=perfis, u=u)
    
@app.route('/permissoes')
@login_required
@checa_permissao('altera-permissoes')
def permissoes():
    if g.user:
        t = u"Usuário: %d" % (g.user.id) + "</br>"
        t += u"Nome: %s" % (g.user.nome) + "</br>"
        t += u"Permissões no usuário: </br>"
        for p in g.user.permissoes:
            t += str(p.permissao.nome) + "</br>"
        t += u"Permissões no perfil: </br>"
        for pf in g.user.perfis:
            for pp in pf.perfil.permissoesperfis:
                t += str(pp.permissao.nome) + "</br>"            
        t += u"Checa permissões: %s" %  g.user.checa_permissao('test') + "</br>"  
        t += u"User agent: %s" % request.headers.get('User-Agent')          
        return t
    else:
        return "Não tem usuário"    
    
from cnddh.decoder import killgremlins
    
@app.route('/ajax/cidades', methods=['GET', 'POST'])
@login_required
def ajax_cidades():
    estado = request.values.get('estado', '').strip()

    q = db.session.query(Cidade.cidade, Cidade.cidade)
    q = q.filter(Cidade.estado == estado)
    q = q.order_by(Cidade.cidade)
    
    a = []
    a.extend([(x, y) for x,y in q.all()])     
    
    return jsonify(result=a)     
    
@app.route('/ajax/denuncia/<int:denuncia_id>/vitima/<int:vitima_id>/delete', methods=['GET', 'POST'])
@login_required
@checa_permissao('edita-vitima')
def ajax_vitima_delete(denuncia_id=None,vitima_id=None):

    a = []
    
    if denuncia_id:
        if vitima_id:
            v =  db.session.query(Vitima).get(vitima_id);
            id = v.id
            nome = v.nome
            
            db.session.delete(v)            
            db.session.commit()
        
            a=[id,nome]        
         
    return jsonify(result=a)     
    
@app.route('/ajax/instituicao', methods=['GET', 'POST'])
@login_required
def ajax_instituicao():
    tipo = request.values.get('tipo', '').strip()

    q = db.session.query(TipoSuspeito.instituicao,TipoSuspeito.instituicao)
    q = q.filter(TipoSuspeito.tipo == tipo)
    q = q.group_by(TipoSuspeito.instituicao)
    q = q.order_by(TipoSuspeito.instituicao)

    a = q.all()
    
    return jsonify(result=a) 
    
@app.route('/ajax/classificacao', methods=['GET', 'POST'])
@login_required
def ajax_classificacao():
    tipo = request.values.get('tipo', '').strip()
    instituicao = request.values.get('instituicao', '').strip() 

    q = db.session.query(TipoSuspeito.id,TipoSuspeito.classificacao)
    q = q.filter(TipoSuspeito.tipo == tipo)
    q = q.filter(TipoSuspeito.instituicao == instituicao)
    q = q.order_by(TipoSuspeito.classificacao)

    a = q.all()
    
    return jsonify(result=a)     
    
@app.route('/ajax/microcategoria', methods=['GET', 'POST'])
@login_required
def ajax_microcategoria():
    macrocategoria = request.values.get('macrocategoria', '').strip()

    q = db.session.query(TipoViolacao.id, TipoViolacao.microcategoria)
    q = q.filter(TipoViolacao.macrocategoria == macrocategoria)    
    q = q.order_by(TipoViolacao.microcategoria)
    
    a = q.all()
    
    return jsonify(result=a)     

@app.route('/ajax/violacao/delete', methods=['GET', 'POST'])
@login_required    
@checa_permissao('edita-violacoes')
def ajax_violacao_delete():    
    vitsup = {}    
    violacao_id = request.values.get('violacao_id', '').strip()
    if violacao_id:
        v =  db.session.query(Violacao).get(violacao_id);
        
        if v:            
            db.session.delete(v)            
            db.session.commit()               
            
            q = db.session.query(Violacao).filter(Violacao.denuncia_id==v.denuncia_id)
            q = q.options(joinedload_all(Violacao.vitima))
            q = q.options(joinedload_all(Violacao.suspeito))
            q = q.options(joinedload_all(Violacao.tipoviolacao))
            objs = q.all()
        
            denuncia = db.session.query(Denuncia).get(v.denuncia_id) 
            
            vitsup = {}
            for v in objs:
                if ('['+ str(v.vitima.id) +']' + v.vitima.nome + '|' + '['+ str(v.suspeito.id) + ']'  + v.suspeito.nome) in vitsup:
                    vitsup[('['+ str(v.vitima.id) +']' + v.vitima.nome + '|' + '['+ str(v.suspeito.id) + ']'  + v.suspeito.nome)].append(v)
                else:
                    vitsup[('['+ str(v.vitima.id) +']' + v.vitima.nome + '|' + '['+ str(v.suspeito.id) + ']'  + v.suspeito.nome)] = [v]                
    return render_template('ajax_relacao_violacao.html', vitsup=vitsup, denuncia=denuncia) 
    
@app.route('/ajax/exemplofonte', methods=['GET', 'POST'])
@login_required
def ajax_exemplofonte():
    a = []    
    tipofonte_id = request.values.get('tipofonte', '').strip()

    if tipofonte_id:
        tf = db.session.query(TipoFonte).get(tipofonte_id);         
        exemplo = tf.exemplo
        
        a=[exemplo]       
    
    return jsonify(result=a)           
    
@app.route('/ajax/grafico/violacaoporestado', methods=['GET', 'POST'])
@login_required
def ajax_violacaoporestado():        
    microcategoria = request.values.get('microcategoria', '').strip()
    dtocorinicio = request.values.get('dtocorinicio', '').strip()
    dtocorfim = request.values.get('dtocorfim', '').strip()
 
    tv =  db.session.query(TipoViolacao).get(microcategoria)
     
    q = db.session.query(Denuncia.estado,func.count(Denuncia.estado))
    if dtocorinicio:
        q = q.filter(Denuncia.dtdenuncia >= datestring_to_date(dtocorinicio))                    
    if dtocorfim:
        q = q.filter(Denuncia.dtdenuncia < (datestring_to_date(dtocorfim) + datetime.timedelta(days=1)) )      
    q = q.join(Denuncia.violacoes)
    q = q.filter(Violacao.tipoviolacoes_id==microcategoria)
    q = q.group_by(Denuncia.estado)
    q = q.order_by(func.count(Denuncia.estado))
    
    a = []    
    
    if q.all():
        a.append(['Estado', tv.microcategoria])

    for est, quant in q.all():
        a.append([est,quant])

    return jsonify(result=a)       
    
@app.route('/ajax/grafico/violacaoporcidade', methods=['GET', 'POST'])
@login_required
def ajax_violacaoporcidade():        
    microcategoria = request.values.get('microcategoria', '').strip()
    dtocorinicio = request.values.get('dtocorinicio', '').strip()
    dtocorfim = request.values.get('dtocorfim', '').strip()
    
    tv =  db.session.query(TipoViolacao).get(microcategoria)
     
    q = db.session.query(Denuncia.cidade,func.count(Denuncia.cidade))
    if dtocorinicio:
        q = q.filter(Denuncia.dtdenuncia >= datestring_to_date(dtocorinicio))                    
    if dtocorfim:
        q = q.filter(Denuncia.dtdenuncia < (datestring_to_date(dtocorfim) + datetime.timedelta(days=1)) )         
    q = q.join(Denuncia.violacoes)
    q = q.filter(Violacao.tipoviolacoes_id==microcategoria)
    q = q.group_by(Denuncia.cidade)
    q = q.order_by(func.count(Denuncia.cidade))
    
    a = []    
    
    if q.all():
        a.append(['Cidade', tv.microcategoria])

    for cid,quant in q.all():
        a.append([cid,quant])

    return jsonify(result=a)     
    
@app.route('/ajax/grafico/violacaopormacro', methods=['GET', 'POST'])
@login_required
def ajax_violacaopormacro():        
    macrocategoria = request.values.get('macrocategoria', '').strip()
    dtocorinicio = request.values.get('dtocorinicio', '').strip()
    dtocorfim = request.values.get('dtocorfim', '').strip()    
      
    q = db.session.query(TipoViolacao.microcategoria, func.count(TipoViolacao.microcategoria))
    if dtocorinicio:
        q = q.filter(Denuncia.dtdenuncia >= datestring_to_date(dtocorinicio))                    
    if dtocorfim:
        q = q.filter(Denuncia.dtdenuncia < (datestring_to_date(dtocorfim) + datetime.timedelta(days=1)) )         
    q = q.join(TipoViolacao.violacoes)
    q = q.filter(TipoViolacao.macrocategoria==macrocategoria)
    q = q.group_by(TipoViolacao.microcategoria)
    q = q.order_by(func.count(TipoViolacao.microcategoria))

    a = []    

    if q.all():
        a.append(['Microcategoria', macrocategoria])

    for mic,quant in q.all():
        a.append([mic,quant])
    
    return jsonify(result=a)         
    
@app.route('/ajax/grafico/violacaoportempo', methods=['GET', 'POST'])
@login_required
def ajax_violacaoportempo():        
    microcategoria = request.values.get('microcategoria', '').strip()
    dtocorinicio = request.values.get('dtocorinicio', '').strip()
    dtocorfim = request.values.get('dtocorfim', '').strip()    

    tv =  db.session.query(TipoViolacao).get(microcategoria)
     
    q = db.session.query(sa.func.month(Denuncia.dtdenuncia), func.count(sa.func.month(Denuncia.dtdenuncia)))
    if dtocorinicio:
        q = q.filter(Denuncia.dtdenuncia >= datestring_to_date(dtocorinicio))                    
    if dtocorfim:
        q = q.filter(Denuncia.dtdenuncia < (datestring_to_date(dtocorfim) + datetime.timedelta(days=1)) )     
    q = q.join(Denuncia.violacoes)
    q = q.filter(Violacao.tipoviolacoes_id==microcategoria)
    q = q.group_by(sa.func.month(Denuncia.dtdenuncia))
    q = q.order_by(sa.func.month(Denuncia.dtdenuncia))
        
    a = []
    b = []
   
    if q.all():
        a.append(['Meses', tv.microcategoria])

        meses = {1:'JAN', 2:'FEV', 3:'MAR', 4:'ABR', 5:'MAI', 6:'JUN',7:'JUL', 8:'AGO', 9:'SET', 10:'OUT', 11:'NOV', 12:'DEZ'}
    
        for m,quant in q.all():
            a.append([meses[m],quant])
    
        #for i in range(1,13):
        #    b.append([i,0])
    
        #for list in b:
        #    for m,quant in q.all():    
        #        if list[0] == m:
        #            list[1]= quant
    
        #for list in b:
        #    list[0] = meses[list[0]]
        #    a.append(list)        
    
    return jsonify(result=a)  
    
@app.route('/ajax/grafico/violacaoporsuspeito', methods=['GET', 'POST'])
@login_required
def ajax_violacaoporsuspeito():        
    microcategoria = request.values.get('microcategoria', '').strip() 
    tiposuspeito = request.values.get('tiposuspeito', '').strip() 

    tv =  db.session.query(TipoViolacao).get(microcategoria)
     
    q = db.session.query(sa.func.monthname(Denuncia.dtdenuncia), func.count(sa.func.month(Denuncia.dtdenuncia)))
    q = q.join(Denuncia.violacoes)
    q = q.join(Denuncia.suspeitos)
    q = q.join(Suspeito.tiposuspeito)
    q = q.filter(Violacao.tipoviolacoes_id==microcategoria)
    q = q.filter(TipoSuspeito.tipo==tiposuspeito)
    q = q.group_by(sa.func.month(Denuncia.dtdenuncia))
    q = q.order_by(sa.func.month(Denuncia.dtdenuncia))
    
    a = []    

    if q.all():
        a.append(['Meses', tv.microcategoria])

    for m,quant in q.all():
        a.append([m,quant])
    
    return jsonify(result=a)      
    
if not DEBUG:
    @app.errorhandler(500)
    def internalerror(e):
        import sys, traceback, time
        from utils import envia_email_excecao
        eid = "%d-%d" % (time.time(), id(e))
        db.session.rollback()        
        exc_info = traceback.format_exc()
        envia_email_excecao(str(eid), exc_info)
        return render_template('500.html', eid=eid), 500

@app.route('/shutdown', methods=['GET', 'POST'])
@login_required
def shutdown():
    shutdown_server()
    logger.info(u'Server shutting down...')
    return 'Server shutting down...'        
    
def log(acao):
    try:
        logger.info(g.user.login + ' ' + acao)
    except:
        logger.info(acao)

@app.route('/teste', methods=['GET', 'POST'])        
def teste_email():   
    
    from_header = 'sistema@cnddh.org.br'
    subject = 'Teste de email'
    email_to = ['dedeco@gmail.com',]
    email_cc = None
    
    t = render_template('encaminhamento-teste.txt')
    
    msg = MIMEText(t, 'html', 'latin-1')
    msg['From'] = from_header
    msg['Subject'] = subject
    msg['To'] = ', '.join(email_to)
    msg['Reply-To'] = 'dedeco@gmail.com'
    if email_cc:
        msg['Cc'] = ', '.join(email_cc)
    #if email_bcc:
    #    msg['Bcc'] = ', '.join(email_bcc)
    
    enviado = envia_email(from_header,email_to,msg.as_string())

    if enviado:
        return 'Email enviado'
    else:
        return 'Nops'        
# coding=latin-1

from database import db
from sqlalchemy.orm import relationship, backref, with_polymorphic
from sqlalchemy import Sequence, ForeignKey, UniqueConstraint

from cnddh.uploadsets import anexos_upload

import datetime

class Denuncia(db.Model):
    __tablename__ = 'denuncias'
    
    id = db.Column(db.Integer, Sequence('denuncias_id_seq'), primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    dtcriacao = db.Column(db.DateTime, unique=False, nullable=False)
    dtdenuncia = db.Column(db.DateTime, unique=False, nullable=False)
    status_id = db.Column(db.Integer, ForeignKey('status.id'), nullable=False)
    status = relationship("Status")
    tipofonte_id = db.Column(db.Integer, ForeignKey('tipofontes.id'),nullable=False)
    fonte = db.Column(db.String(240), unique=False, nullable=False)    
    protocolo = db.Column(db.Integer)    
    resumo = db.Column(db.String(1024), unique=False, nullable=False)
    descricao = db.Column(db.String(8192), unique=False, nullable=False)
    observacao = db.Column(db.String(8192), unique=False)
    tipolocal = db.Column(db.String(240), unique=False, nullable=False)
    endereco = db.Column(db.String(240), unique=False, nullable=False)
    num = db.Column(db.String(60), unique=False)
    complemento = db.Column(db.String(240), unique=False)
    referencia =  db.Column(db.String(240), unique=False)
    bairro = db.Column(db.String(240), unique=False)    
    cidade = db.Column(db.String(60), unique=False, nullable=False)
    cep = db.Column(db.String(60), unique=False, nullable=False)    
    estado = db.Column(db.String(2), unique=False, nullable=False)
    pais = db.Column(db.String(60), unique=False, nullable=False)
    
    vitimas = relationship("Vitima", backref="denuncia")
    suspeitos = relationship("Suspeito", backref="denuncia")
    violacoes = relationship("Violacao", backref="denuncia")
    anexos = relationship("Anexo", backref="denuncia")
    historico = relationship("Historico", backref="denuncia",order_by="asc(Historico.dtcriacao)") 
    
    def __init__(self, numero):
        self.numero = numero
        self.status_id = 1
        self.dtcriacao = datetime.datetime.today()  
        
class Vitima(db.Model):
    __tablename__ = 'vitimas'
    
    id = db.Column(db.Integer, Sequence('vitimas_id_seq'), primary_key=True)  
    denuncia_id =  db.Column(db.Integer, ForeignKey('denuncias.id'), nullable=False)
    tipovitima_id = db.Column(db.Integer, ForeignKey('tipovitimas.id'), nullable=False)
    qtdevitimas = db.Column(db.Integer, unique=False, nullable=False, default=1)
    nomenaoidentificado = db.Column(db.String(1), unique=False)
    nome = db.Column(db.String(100), unique=False, nullable=False)    
    idade = db.Column(db.Integer, unique=False, nullable=False, default=0)
    sexo = db.Column(db.String(20), unique=False, nullable=False)
    cor = db.Column(db.String(20), unique=False, nullable=False)
    
    violacoes = relationship("Violacao", backref="vitima")
    tipovitima = relationship("TipoVitima")
        
    def __init__(self, tipovitima_id):
        self.tipovitima_id = tipovitima_id   

class TipoVitima(db.Model):
    __tablename__ = 'tipovitimas'
    
    id = db.Column(db.Integer, Sequence('tipovitimas_id_seq'), primary_key=True)
    tipo = db.Column(db.String(100), unique=False, nullable=False)
    legenda = db.Column(db.String(255), unique=False)

    def __init__(self, tipo, legenda):
        self.tipo = tipo
        self.legenda = legenda
        
class Suspeito(db.Model):
    __tablename__ = 'suspeitos'
    
    id = db.Column(db.Integer, Sequence('suspeitos_id_seq'), primary_key=True)
    denuncia_id =  db.Column(db.Integer, ForeignKey('denuncias.id'), nullable=False) 
    tiposuspeito_id =db.Column(db.Integer, ForeignKey('tiposuspeitos.id'), nullable=False)
    qtdesuspeitos = db.Column(db.Integer, unique=False, nullable=False, default=1)
    nomeinstituicao = db.Column(db.String(255), unique=False, nullable=False)
    nomenaoidentificado = db.Column(db.String(1), unique=False)
    nome = db.Column(db.String(255), unique=False, nullable=False)   
    idade = db.Column(db.Integer, unique=False, nullable=False, default=0)
    sexo = db.Column(db.String(20), unique=False, nullable=False)    
    cor = db.Column(db.String(20), unique=False, nullable=False)
   
    violacoes = relationship("Violacao", backref="suspeito")
    tiposuspeito = relationship("TipoSuspeito")
   
    def __init__(self, tiposuspeito_id):
        self.tiposuspeito_id = tiposuspeito_id
        
class TipoSuspeito(db.Model):
    __tablename__ = 'tiposuspeitos'
    
    id = db.Column(db.Integer, Sequence('tiposuspeitos_id_seq'), primary_key=True)
    tipo = db.Column(db.String(100), unique=False, nullable=False)
    legenda = db.Column(db.String(255), unique=False)
    instituicao = db.Column(db.String(255), unique=False, nullable=False)
    classificacao = db.Column(db.String(255), unique=False, nullable=False)

    def __init__(self, tipo, legenda, instituicao, classificacao):
        self.tipo = tipo
        self.legenda = legenda
        self.instituicao = instituicao      
        self.classificacao = classificacao           

class TipoViolacao(db.Model):
    __tablename__ = 'tipoviolacoes'
    
    id = db.Column(db.Integer, Sequence('tipoviolacoes_id_seq'), primary_key=True)
    macrocategoria = db.Column(db.String(255), unique=False, nullable=False)
    microcategoria = db.Column(db.String(255), unique=False, nullable=False)        

    violacoes = relationship("Violacao", backref="tipoviolacao")
    
    def __init__(self, macrocategoria, microcategoria):
        self.macrocategoria = macrocategoria
        self.microcategoria = microcategoria      

class Violacao(db.Model):
    __tablename__ = 'violacoes'
    
    id = db.Column(db.Integer, Sequence('violacoes_id_seq'), primary_key=True)
    tipoviolacoes_id = db.Column(db.Integer, ForeignKey('tipoviolacoes.id'), nullable=False)
    tipo = db.Column(db.String(20))
    denuncia_id =  db.Column(db.Integer, ForeignKey('denuncias.id'), nullable=False)    
    vitima_id = db.Column(db.Integer, ForeignKey('vitimas.id'), nullable=False)    
    suspeito_id = db.Column(db.Integer, ForeignKey('suspeitos.id'), nullable=False)
    
    __table_args__ = (UniqueConstraint('tipoviolacoes_id', 'denuncia_id', 'vitima_id', 'suspeito_id', name='uix_violacao'),)
   
    def __init__(self, denuncia_id, tipoviolacoes_id, suspeito_id, vitima_id):
        self.denuncia_id = denuncia_id
        self.tipoviolacoes_id = tipoviolacoes_id
        self.suspeito_id = suspeito_id          
        self.vitima_id = vitima_id      
        
    __mapper_args__ = {
        'polymorphic_on':tipo,
        'polymorphic_identity':'violacoes',
        'with_polymorphic':'*'
    } 
    
class Homicidio(Violacao):
    __tablename__ = 'homicidios'
    
    id = db.Column(db.Integer, ForeignKey('violacoes.id'),primary_key=True)
    rco = db.Column(db.String(100), unique=False)
    bo = db.Column(db.String(100), unique=False)
    ip = db.Column(db.String(100), unique=False)
    reds = db.Column(db.String(100), unique=False)    
    dtfato = db.Column(db.DateTime, unique=False)    
    prfato = db.Column(db.String(20), unique=False)
    situacao = db.Column(db.String(20), unique=False)
    obs = db.Column(db.String(255), unique=False)
    
    arquivo = db.Column(db.String(255), unique=False)
    
    meiosutilizados = relationship("HomicidioMeioUtilizado",cascade="all,delete")
    
    __mapper_args__ = {'polymorphic_identity':'homicidios'}    
    
    def _get_url(self):
        if self.arquivo:
            return anexos_upload.url(self.arquivo)
        else:
            return None
            
    url = property(_get_url)         

class TipoMeioUtilizado(db.Model):
    __tablename__ = 'tipomeioutilizados'
    
    id = db.Column(db.Integer, Sequence('tipomeioutilizados_id_seq'), primary_key=True)
    meio = db.Column(db.String(255), unique=False, nullable=False)    
    
    def __init__(self, meio):
        self.meio = meio        
        
class HomicidioMeioUtilizado(db.Model):
    __tablename__ = 'homicidiomeioutilizado'     
    
    homicidio_id = db.Column(db.Integer, ForeignKey('homicidios.id'), primary_key=True)
    tipomeioutilizado_id = db.Column(db.Integer, ForeignKey('tipomeioutilizados.id'), primary_key=True)
    
    __table_args__ = (UniqueConstraint('homicidio_id', 'tipomeioutilizado_id', name='uix_meioutilizado'),)
    
    def __init__(self, homicidio_id, tipomeioutilizado_id):
        self.homicidio_id = homicidio_id
        self.tipomeioutilizado_id = tipomeioutilizado_id
        
class TipoFonte(db.Model):
    __tablename__ = 'tipofontes'
    
    id = db.Column(db.Integer, Sequence('tipofontes_id_seq'), primary_key=True)
    tipofonte = db.Column(db.String(255), unique=False, nullable=False)
    legenda = db.Column(db.String(255), unique=False)
    exemplo = db.Column(db.String(255), unique=False)   
    
    def __init__(self, tipofonte, legenda, exemplo):
        self.tipofonte = tipofonte        
        self.legenda = legenda       
        self.exemplo = exemplo     
        
class Status(db.Model):
    __tablename__ = 'status'
    
    id = db.Column(db.Integer, Sequence('status_id_seq'), primary_key=True)
    status = db.Column(db.String(255), unique=False, nullable=False)
    legenda = db.Column(db.String(255), unique=False)
    
    def __init__(self, status, legenda):
        self.status = status        
        self.legenda = legenda            
        
class Acao(db.Model):
    __tablename__ = 'acoes'
    
    id = db.Column(db.Integer, Sequence('acoes_id_seq'), primary_key=True)
    acao = db.Column(db.String(255), unique=False, nullable=False,)
    legenda = db.Column(db.String(255), unique=False)
    
    def __init__(self, acao, legenda):
        self.acao = acao        
        self.legenda = legenda        
       
class Historico(db.Model):
    __tablename__ = 'historico'
    
    id = db.Column(db.Integer, Sequence('historico_id_seq'), primary_key=True)
    denuncia_id = db.Column(db.Integer, ForeignKey('denuncias.id'), nullable=False)   
    acao_id = db.Column(db.Integer, ForeignKey('acoes.id'), nullable=False)   
    dtcriacao = db.Column(db.DateTime, unique=False, nullable=False)
    motivo = db.Column(db.String(1024), unique=False)
        
    acao = relationship("Acao")    
    encaminhamento = relationship("Encaminhamento", backref="historico", lazy='joined',cascade="all,delete")
        
    def __init__(self, denuncia_id):
        self.denuncia_id = denuncia_id 
        self.dtcriacao = datetime.datetime.today()       
        
class TipoEncaminhamento(db.Model):
    __tablename__ = 'tipoencaminhamentos'
    
    id = db.Column(db.Integer, Sequence('tipoencaminhamentos_id_seq'), primary_key=True)
    tipo = db.Column(db.String(100), unique=False, nullable=False)
    legenda = db.Column(db.String(255), unique=False)

    def __init__(self, tipo):
        self.tipo = tipo

class Orgao(db.Model):
    __tablename__ = 'orgaos'
    
    id = db.Column(db.Integer, Sequence('orgaos_id_seq'), primary_key=True)
    orgao = db.Column(db.String(200), unique=False, nullable=False)  

    def __init__(self, orgao):
        self.orgao = orgao     
      
class Encaminhamento(db.Model):
    __tablename__ = 'encaminhamentos'
    
    id = db.Column(db.Integer, Sequence('encaminhamentos_id_seq'), primary_key=True)
    historico_id = db.Column(db.Integer, ForeignKey('historico.id'), nullable=False)   
    orgao_id = db.Column(db.Integer, ForeignKey('orgaos.id'), nullable=False)
    tipo_id = db.Column(db.Integer, ForeignKey('tipoencaminhamentos.id'), nullable=False)
    dtenvio = db.Column(db.DateTime, unique=False, nullable=False)
    dtlimite = db.Column(db.DateTime, unique=False)
    dtretorno = db.Column(db.DateTime, unique=False)
    dtcriacao = db.Column(db.DateTime, unique=False, nullable=False)
    tipo = db.Column(db.String(20))
    
    orgao = relationship("Orgao")    
    tipo_encaminhamento = relationship("TipoEncaminhamento")
    retorno = relationship("Retorno",cascade="all,delete")   
    
    __mapper_args__ = {
        'polymorphic_on':tipo,
        'polymorphic_identity':'encaminhamentos',
        'with_polymorphic':'*'
    } 
    
    def __init__(self, historico_id):
        self.historico_id = historico_id
        dtcriacao = datetime.datetime.today()  
        
class Oficio(Encaminhamento):
    __tablename__ = 'oficios'
    
    id = db.Column(db.Integer, ForeignKey('encaminhamentos.id'),primary_key=True)
    numero = db.Column(db.String(255), nullable=False)
    assunto = db.Column(db.String(255), nullable=False)
    obs = db.Column(db.String(255), nullable=False)
    
    arquivo = db.Column(db.String(255), unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'oficios'}
    
    def _get_url(self):
        if self.arquivo:
            return anexos_upload.url(self.arquivo)
        else:
            return None
            
    url = property(_get_url)     

class Telefonema(Encaminhamento):
    __tablename__ = 'telefonemas'
    
    id = db.Column(db.Integer, ForeignKey('encaminhamentos.id'),primary_key=True)
    numero = db.Column(db.String(255), unique=False, nullable=False)
    destinatario = db.Column(db.String(255), nullable=True, unique=False)
    obs = db.Column(db.String(255), nullable=True, unique=False)

    __mapper_args__ = {'polymorphic_identity':'telefonemas'}
        
class Reuniao(Encaminhamento):
    __tablename__ = 'reunioes'
    
    id = db.Column(db.Integer, ForeignKey('encaminhamentos.id'),primary_key=True)
    pauta = db.Column(db.String(255), nullable=False, unique=False)
    participantes = db.Column(db.String(4000), nullable=False, unique=False)
    obs = db.Column(db.String(255), nullable=False, unique=False)

    arquivo = db.Column(db.String(255), unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'reunioes'}    
    
    def _get_url(self):
        if self.arquivo:
            return anexos_upload.url(self.arquivo)
        else:
            return None
            
    url = property(_get_url)          

class Email(Encaminhamento):
    __tablename__ = 'emails'
    
    id = db.Column(db.Integer, ForeignKey('encaminhamentos.id'),primary_key=True)
    para = db.Column(db.String(255), nullable=False, unique=False)
    de = db.Column(db.String(255), nullable=False, unique=False)
    assunto = db.Column(db.String(255), nullable=False, unique=False)
    texto = db.Column(db.String(4000), nullable=False, unique=False)
    
    arquivo = db.Column(db.String(255), unique=False)

    __mapper_args__ = {'polymorphic_identity':'emails'}    
    
    def _get_url(self):
        if self.arquivo:
            return anexos_upload.url(self.arquivo)
        else:
            return None
            
    url = property(_get_url)        

class Generico(Encaminhamento):
    __tablename__ = 'genericos'
    
    id = db.Column(db.Integer, ForeignKey('encaminhamentos.id'),primary_key=True)
    obs = db.Column(db.String(255), nullable=False, unique=False)
    
    arquivo = db.Column(db.String(255), unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'genericos'}    
    
    def _get_url(self):
        if self.arquivo:
            return anexos_upload.url(self.arquivo)
        else:
            return None
            
    url = property(_get_url)        
        
class Retorno(db.Model):
    __tablename__ = 'retornos'
    
    id = db.Column(db.Integer, Sequence('retornos_id_seq'), primary_key=True)
    encaminhamento_id =  db.Column(db.Integer, ForeignKey('encaminhamentos.id'), nullable=False)     
    descricao = db.Column(db.String(255), nullable=False, unique=False)
    dtretorno = db.Column(db.Date, unique=False)
    dtcriacao = db.Column(db.DateTime, unique=False)
    tiporetorno_id = db.Column(db.Integer, ForeignKey('tiporetornos.id'), nullable=False)   
    tipo = db.Column(db.String(80))
    
    tiporetorno = relationship("TipoRetorno")
    
    arquivo = db.Column(db.String(255), unique=False)
    
    def _get_url(self):
        if self.arquivo:
            return anexos_upload.url(self.arquivo)
        else:
            return None
            
    url = property(_get_url)        
    
    __mapper_args__ = {
        'polymorphic_on':tipo,
        'polymorphic_identity':'retornos',
        'with_polymorphic':'*'
    }     

    def __init__(self, encaminhamento_id):
        self.encaminhamento_id = encaminhamento_id
        dtcriacao = datetime.datetime.today()  

class RetornoGenerico(Retorno):
    __tablename__ = 'retornogenerico'
    
    id = db.Column(db.Integer, ForeignKey('retornos.id'),primary_key=True)
    observacao = db.Column(db.String(255), nullable=False, unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'retornogenerico'}           
        
class RetornoPessoasassistidas(Retorno):
    __tablename__ = 'retornopessoasassistidas'
    
    id = db.Column(db.Integer, ForeignKey('retornos.id'),primary_key=True)
    tipoassistencia = db.Column(db.String(255), nullable=False, unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'retornopessoasassistidas'}
    
class RetornoInquerito(Retorno):
    __tablename__ = 'retornoinquerito'
    
    id = db.Column(db.Integer, ForeignKey('retornos.id'),primary_key=True)
    ip = db.Column(db.String(100), unique=False)
    situacao = db.Column(db.String(20), unique=False)
    motivo = db.Column(db.String(80), nullable=False, unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'retornoinquerito'}    

class RetornoProcesso(Retorno):
    __tablename__ = 'retornoprocesso'
    
    id = db.Column(db.Integer, ForeignKey('retornos.id'),primary_key=True)
    np = db.Column(db.String(100), unique=False)
    situacao = db.Column(db.String(20), unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'retornoprocesso'}    

class RetornoBO(Retorno):
    __tablename__ = 'retornobo'
    
    id = db.Column(db.Integer, ForeignKey('retornos.id'),primary_key=True)
    bo = db.Column(db.String(100), unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'retornobo'}          

class RetornoRCO(Retorno):
    __tablename__ = 'retornorco'
    
    id = db.Column(db.Integer, ForeignKey('retornos.id'),primary_key=True)
    rco = db.Column(db.String(100), unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'retornorco'}        
        
class RetornoREDS(Retorno):
    __tablename__ = 'retornoreds'
    
    id = db.Column(db.Integer, ForeignKey('retornos.id'),primary_key=True)
    reds = db.Column(db.String(100), unique=False)    
    
    __mapper_args__ = {'polymorphic_identity':'retornoreds'}     
    
class RetornoPoliticaPSR(Retorno):
    __tablename__ = 'retornopoliticapsr'
    
    id = db.Column(db.Integer, ForeignKey('retornos.id'),primary_key=True)
    tipopolitica = db.Column(db.String(255), nullable=False, unique=False)
    
    __mapper_args__ = {'polymorphic_identity':'retornopoliticapsr'}      
        
class TipoRetorno(db.Model):
    __tablename__ = 'tiporetornos'
    
    id = db.Column(db.Integer, Sequence('tiporetorno_id_seq'), primary_key=True)
    nome = db.Column(db.String(255), unique=False, nullable=False)
    tipo = db.Column(db.String(100), unique=False, nullable=False)
    legenda = db.Column(db.String(255), unique=False)
    
    def __init__(self, nome, tipo, legenda):
        self.nome = nome    
        self.tipo = tipo
        self.legenda = legenda
        
class Anexo(db.Model):
    __tablename__ = 'anexos'
    
    id = db.Column(db.Integer, Sequence('anexos_id_seq'), primary_key=True)
    denuncia_id =  db.Column(db.Integer, ForeignKey('denuncias.id'),  nullable=False) 
    descricaoanexo = db.Column(db.String(255), nullable=False, unique=False)
    arquivo = db.Column(db.String(255), unique=False)
    
    def __init__(self, denuncia_id):
        self.denuncia_id = denuncia_id    

    def _get_url(self):
        if self.arquivo:
            return anexos_upload.url(self.arquivo)
        else:
            return None
            
    url = property(_get_url)          
       
class Cidade(db.Model):
    __tablename__ = 'cidades'
    
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(2), nullable=False)
    cidade = db.Column(db.String(200), nullable=False)

    def __init__(self, estado, cidade):
        self.estado = estado
        self.cidade = cidade                   
        
class TipoLocal(db.Model):
    __tablename__ = 'tipolocais'
    
    id = db.Column(db.Integer, Sequence('tipolocais_id_seq'), primary_key=True)
    local = db.Column(db.String(100), unique=False, nullable=False)  

    def __init__(self, local):
        self.local = local

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, Sequence('usuarios_id_seq'), primary_key=True)
    login =  db.Column(db.String(16), nullable=False, unique=True, index=True)
    nome = db.Column(db.String(80), nullable=False, unique=False)
    ddd = db.Column(db.String(2), nullable=False, unique=False)
    telefone = db.Column(db.String(10), nullable=False, unique=False)
    senhahash = db.Column(db.String(80), nullable=False, unique=False)
    email = db.Column(db.String(200), nullable=False, unique=True, index=True)
    dtregistro = db.Column(db.DateTime, nullable=False, unique=False)
    dtultlogin = db.Column(db.DateTime, nullable=True, unique=False)    
    
    permissoes = relationship("PermissaoUsuario", backref="usuario")
    perfis = relationship("PerfilUsuario", backref="usuario")   
        
    __table_args__ = (UniqueConstraint('login', 'email', name='uix_usuario'),)    
    
    def __init__(self, login, nome, ddd, telefone, senhahash, email):
        self.login = login
        self.nome = nome
        self.ddd = ddd
        self.telefone = telefone
        self.senhahash = senhahash
        self.email = email
        self.dtregistro = datetime.datetime.today()    

    def checa_permissao(self, permissao):
        if permissao in self.permissoes:
            if permissao == p.permissao.nome:
                return True
        for pf in self.perfis:
            for pp in pf.perfil.permissoesperfis:
                if permissao == pp.permissao.nome:
                    return True
        return False
        
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return unicode(self.id)
 
    def __repr__(self):
        return '<Usuário %r>' % (self.login)       

class Permissao(db.Model):
    __tablename__ = 'permissoes'
    
    id = db.Column(db.Integer, Sequence('permissoes_id_seq'), primary_key=True) 
    nome = db.Column(db.String(80), nullable=False, unique=True)    
    descricao = db.Column(db.String(255), nullable=False, unique=False) 
    
    permissoesusuario = relationship("PermissaoUsuario", backref="permissao")
    permissoesperfis = relationship("PermissaoPerfil", backref="permissao")
    
class PermissaoUsuario(db.Model):
    __tablename__ = 'permissoesusuarios'
    
    id = db.Column(db.Integer, Sequence('permissoesusuarios_id_seq'), primary_key=True) 
    usuario_id = db.Column(db.Integer, ForeignKey('usuarios.id'), nullable=False)    
    permissao_id = db.Column(db.Integer, ForeignKey('permissoes.id'), nullable=False)
    tipo = db.Column(db.Integer)
    
    __table_args__ = (UniqueConstraint('usuario_id', 'permissao_id', name='uix_permmissao_usuario'),)    

class Perfil(db.Model):
    __tablename__ = 'perfis'
    
    id = db.Column(db.Integer, Sequence('perfis_id_seq'), primary_key=True) 
    nome = db.Column(db.String(80), nullable=False, unique=True)    
    descricao = db.Column(db.String(255), nullable=False, unique=False) 
    
    permissoesperfis = relationship("PermissaoPerfil", backref="perfil")
    perfisusuarios = relationship("PerfilUsuario", backref="perfil")
    
class PermissaoPerfil(db.Model):
    __tablename__ = 'permissoesperfis'
    
    id = db.Column(db.Integer, Sequence('permissoesperfis_id_seq'), primary_key=True) 
    permissao_id = db.Column(db.Integer, ForeignKey('permissoes.id'), nullable=False)    
    perfil_id = db.Column(db.Integer, ForeignKey('perfis.id'), nullable=False)
    tipo = db.Column(db.Integer)    
    
    __table_args__ = (UniqueConstraint('permissao_id', 'perfil_id', name='uix_permissaoperfil'),)    
    
class PerfilUsuario(db.Model):
    __tablename__ = 'perfisusuarios'
    
    id = db.Column(db.Integer, Sequence('permissoesusuarios_id_seq'), primary_key=True) 
    perfil_id = db.Column(db.Integer, ForeignKey('perfis.id'), unique=False)    
    usuario_id = db.Column(db.Integer, ForeignKey('usuarios.id'), unique=False)
    tipo = db.Column(db.Integer)
    
    __table_args__ = (UniqueConstraint('perfil_id', 'usuario_id', name='uix_perfisusuario'),)    
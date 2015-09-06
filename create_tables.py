# coding=latin-1
from cnddh import app
from cnddh.models import *
from cnddh.decoder import killgremlins

import csv
import md5

from cnddh.utils import datestring_to_date

def populate():        
    
    print u'Inserindo cidades...'    
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\cidades.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',',1)))

    for i in t:
        lista.append(Cidade(i[0],i[1]))
        
    for i in lista:
        db.session.add(i)     
    
    print u'Inserindo tipo de violações...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\macro_micro_categorias.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',',1)))

    for i in t:
        if len(i[0]) > 1:
            lista.append(TipoViolacao(killgremlins(i[0]),killgremlins(i[1])))
        
    for i in lista:
        db.session.add(i)          
    
    
    print u'Inserindo tipo de vitimas...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\vitimas.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',',1)))

    for i in t:
        if len(i[0]) > 1:
            lista.append(TipoVitima(killgremlins(i[0]),killgremlins(i[1])))
        
    for i in lista:
        db.session.add(i)          
    
    
    print u'Inserindo tipo de suspeitos...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\suspeitos.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(TipoSuspeito(killgremlins(i[0]),None,killgremlins(i[1]),killgremlins(i[2])))
        
    for i in lista:
        db.session.add(i)    
        
    print u'Inserindo tipo de fontes...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\fontes.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(TipoFonte(killgremlins(i[0]),killgremlins(i[1]),killgremlins(i[2])))
        
    for i in lista:
        db.session.add(i)        

    print u'Inserindo tipo de status...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\status.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(Status(killgremlins(i[0]),killgremlins(i[1])))
        
    for i in lista:
        db.session.add(i)          
        
        
    print u'Inserindo tipo de ações...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\acoes.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(Acao(killgremlins(i[0]),killgremlins(i[1])))
        
    for i in lista:
        db.session.add(i)        
    
    db.session.commit() 
    
    print u'Inserindo tipo de tipo locais...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\tipolocais.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(TipoLocal(killgremlins(i[0])))
        
    for i in lista:
        db.session.add(i)        
    
    db.session.commit()     
    
    
    print u'Inserindo tipo de orgaos...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\orgaos.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(Orgao(killgremlins(i[0])))
        
    for i in lista:
        db.session.add(i)        
    
    db.session.commit()     
    
    print u'Inserindo tipo de tipos de retorno...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\tiporetorno.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
        
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(TipoRetorno(killgremlins(i[0]),killgremlins(i[1]).strip(), killgremlins(i[2]).strip()))
        
    for i in lista:
        db.session.add(i)        
    
    db.session.commit()     
    
    print u'Inserindo tipo de meios utilizados...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\tipomeioutilizados.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
        
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(TipoMeioUtilizado(killgremlins(i[0])))
        
    for i in lista:
        db.session.add(i)        
    
    db.session.commit()         
    
    print u'Inserindo tipo de encaminhamentos...'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\tipoencaminhamentos.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass           
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            lista.append(TipoEncaminhamento(killgremlins(i[0])))
        
    for i in lista:
        db.session.add(i)        
    
    db.session.commit()       
   
    print u'Inserindo usuário ADM...'   
    u = Usuario('adm','Administrador','31','3071-4827',md5.new('adm' + 'xpto123456').hexdigest(),'dedeco@gmail.com')
    db.session.add(u)  
    
    print u'Inserindo permissões..'        
    lista = []   
    lines = []
    try:
        f = open(".\\cnddh\\static\\docs\\permissoes.txt", "r")
        try:
            lines = f.readlines()
        finally:
            f.close()
    except IOError:
        pass    
    
    #print lines
  
    t = [('','')]
    for i in lines:
        t.append(tuple(i.strip().split(',')))

    for i in t:
        if len(i[0]) > 1:
            p = Permissao()
            p.nome = killgremlins(i[0])
            p.descricao = killgremlins(i[1])
            lista.append(p)
        
    for p in lista:
        db.session.add(p)          
    
    pf = Perfil()
    pf.nome = u'Administrador'
    pf.descricao = u'Administra o site, cria usuários e gerencia os perfis e permissões'
    db.session.add(pf)
    
    db.session.flush()
    
    for p in lista:
        pp = PermissaoPerfil()
        pp.permissao_id = p.id
        pp.perfil_id = pf.id
        pp.tipo = 1
        db.session.add(pp)
     
    pu =  PerfilUsuario()
    pu.perfil_id = pf.id
    pu.usuario_id = u.id
    pu.tipo = 1
    db.session.add(pu)
     
    db.session.commit()   
    
    print u'Informações inseridas com sucesso'         
        

with app.test_request_context():
    db.drop_all() 
    db.create_all()
    populate()
 
    


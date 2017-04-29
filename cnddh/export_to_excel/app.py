# -*- coding: utf-8 -*-
from datetime import datetime

from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

import xlsxwriter

from cnddh.database import db
from cnddh.models import Denuncia, Violacao, Vitima, Suspeito


export_app = Blueprint('exportar-dados', __name__,url_prefix='/exportar-dados',
                        template_folder='templates')


LIMIT_ROW = 1048576


def str_to_unicode_utf8(string):
    return unicode(string,'utf-8')

def normalize_str(string):
    if string:
        if isinstance(string, unicode):
            return string
        else:
            return str_to_unicode_utf8(str(string))
    else:
        return ""


def _criar_cabecalho_violacoes(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Violação ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Tipo'), negrito)
    aba.write('C1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('D1', str_to_unicode_utf8('Vítima ID'), negrito)
    aba.write('E1', str_to_unicode_utf8('Suspeitos ID'), negrito)
    
    #Largura
    aba.set_column('A:E', 13)

    #Filtro
    aba.autofilter('A1:E1')


def _criar_aba_violacoes(planilha, filtros, negrito, date_format):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Violações'))
    limit_quantidade = 0

    _criar_cabecalho_violacoes(aba, negrito)

    for index, violacao in enumerate(db.session.query(Violacao).all(), start=1):
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(str_to_unicode_utf8('Violações_'+str(1+limit_quantidade)))
            _criar_cabecalho_violacoes(aba, negrito)
            limit_quantidade +=1

        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, violacao.id)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 1, normalize_str(violacao.tipo))
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 2, violacao.denuncia_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 3, violacao.vitima_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 4, violacao.suspeito_id)


def _create_cabecalho_denuncia(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Número'), negrito)
    aba.write('C1', str_to_unicode_utf8('Data Criação'), negrito)
    
    aba.write('D1', str_to_unicode_utf8('Data Denúncia'), negrito)
    aba.write('E1', str_to_unicode_utf8('Status ID'), negrito)
    
    # aba.write('F1', '', negrito)
    aba.write('G1', str_to_unicode_utf8('Fonte ID'), negrito)
    aba.write('H1', str_to_unicode_utf8('Fonte'), negrito)
    aba.write('I1', str_to_unicode_utf8('Protocolo'), negrito)
    aba.write('J1', str_to_unicode_utf8('Resumo'), negrito)
    aba.write('K1', str_to_unicode_utf8('Descrição'), negrito)
    aba.write('L1', str_to_unicode_utf8('Observação'), negrito)
    aba.write('M1', str_to_unicode_utf8('Tipo de Local'), negrito)
    aba.write('N1', str_to_unicode_utf8('Endereço'), negrito)
    aba.write('O1', str_to_unicode_utf8('Número'), negrito)
    aba.write('P1', str_to_unicode_utf8('Complemento'), negrito)
    
    aba.write('Q1', str_to_unicode_utf8('Referência'), negrito)
    aba.write('R1', str_to_unicode_utf8('Bairro'), negrito)
    aba.write('S1', str_to_unicode_utf8('Cidade'), negrito)
    aba.write('T1', str_to_unicode_utf8('CEP'), negrito)
    aba.write('U1', str_to_unicode_utf8('Estado'), negrito)
    aba.write('V1', str_to_unicode_utf8('País'), negrito)
    
    #Largura
    aba.set_column('A:G', 13)
    aba.set_column('H:H', 25)
    aba.set_column('I:I', 13)
    aba.set_column('J:L', 25)
    aba.set_column('M:V', 20)

    #Filtro
    aba.autofilter('A1:V1')


def _criar_aba_denuncias(planilha, filtros, negrito, date_format):
    aba = planilha.add_worksheet(u'Denúncias')
    limit_quantidade = 0

    _create_cabecalho_denuncia(aba, negrito)

    for index, denuncia in enumerate(db.session.query(Denuncia).all(),start=1):
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(str_to_unicode_utf8('Denúncias_'+str(1+limit_quantidade)))
            _create_cabecalho_denuncia(aba, negrito)
            limit_quantidade +=1
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, denuncia.id)
        aba.write(index - limit_quantidade * LIMIT_ROW, 1, denuncia.numero)
        aba.write_datetime(index - limit_quantidade * LIMIT_ROW, 2, denuncia.dtcriacao, date_format)
        aba.write_datetime(index - limit_quantidade * LIMIT_ROW, 3, denuncia.dtdenuncia, date_format)
        aba.write(index - limit_quantidade * LIMIT_ROW, 4, denuncia.status_id)
        # aba.write(index, 5, denuncia.status)
        
        aba.write(index - limit_quantidade * LIMIT_ROW, 6, denuncia.tipofonte_id)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 7, normalize_str(denuncia.fonte))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 8, normalize_str(denuncia.protocolo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 9, normalize_str(denuncia.resumo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 10, normalize_str(denuncia.descricao))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 11, normalize_str(denuncia.observacao))
        aba.write(index - limit_quantidade * LIMIT_ROW, 12, denuncia.tipolocal)
        aba.write(index - limit_quantidade * LIMIT_ROW, 13, denuncia.endereco)
        aba.write(index - limit_quantidade * LIMIT_ROW, 14, denuncia.num)
        aba.write(index - limit_quantidade * LIMIT_ROW, 15, denuncia.complemento)
        aba.write(index - limit_quantidade * LIMIT_ROW, 16, denuncia.referencia)
        aba.write(index - limit_quantidade * LIMIT_ROW, 17, denuncia.bairro)
        aba.write(index - limit_quantidade * LIMIT_ROW, 18, denuncia.cidade)
        aba.write(index - limit_quantidade * LIMIT_ROW, 19, denuncia.cep)
        aba.write(index - limit_quantidade * LIMIT_ROW, 20, denuncia.estado)
        aba.write(index - limit_quantidade * LIMIT_ROW, 21, denuncia.pais)


def _criar_cabecalho_vitimas(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Vítimas ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('C1', str_to_unicode_utf8('Tipo Vítima ID'), negrito)
    aba.write('D1', str_to_unicode_utf8('Quantidade De Vítimas'), negrito)
    aba.write('E1', str_to_unicode_utf8('Nome não identificado'), negrito)
    aba.write('F1', str_to_unicode_utf8('Nome'), negrito)
    aba.write('G1', str_to_unicode_utf8('Idade'), negrito)
    aba.write('H1', str_to_unicode_utf8('Sexo'), negrito)
    aba.write('I1', str_to_unicode_utf8('Cor'), negrito)
    
    #Largura
    aba.set_column('A:I', 13)

    #Filtro
    aba.autofilter('A1:I1')

def _criar_aba_vitimas(planilha, filtros, negrito, date_format):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Vítimas'))
    limit_quantidade = 0

    _criar_cabecalho_vitimas(aba, negrito)
    
    for index, vitima in enumerate(db.session.query(Vitima).all(),start=1):
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(str_to_unicode_utf8('Vítimas_'+str(1+limit_quantidade)))
            _criar_cabecalho_vitimas(aba, negrito)
            limit_quantidade +=1
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, vitima.id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 1, vitima.denuncia_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 2, vitima.tipovitima_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 3, vitima.qtdevitimas)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 4, normalize_str(vitima.nomenaoidentificado))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 5, normalize_str(vitima.nome))
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 6, vitima.idade)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 7, normalize_str(vitima.sexo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 8, normalize_str(vitima.cor))


def _criar_cabecalho_suspeitos(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Vítimas ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('C1', str_to_unicode_utf8('Tipo de Suspeito ID'), negrito)
    aba.write('D1', str_to_unicode_utf8('Quantidade de Suspeitos'), negrito)
    aba.write('E1', str_to_unicode_utf8('Nome Instituição'), negrito)
    aba.write('F1', str_to_unicode_utf8('Nome não identificado'), negrito)
    aba.write('G1', str_to_unicode_utf8('Nome'), negrito)
    aba.write('H1', str_to_unicode_utf8('Idade'), negrito)
    aba.write('I1', str_to_unicode_utf8('Sexo'), negrito)
    aba.write('J1', str_to_unicode_utf8('Cor'), negrito)
    
    #Largura
    aba.set_column('A:J', 15)

    #Filtro
    aba.autofilter('A1:J1')

def _criar_aba_suspeitos(planilha, filtros, negrito, date_format):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Suspeitos'))
    limit_quantidade = 0

    _criar_cabecalho_suspeitos(aba, negrito)  

    for index, suspeito in enumerate(db.session.query(Suspeito).all(),start=1):
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(str_to_unicode_utf8('Suspeitos'+str(1+limit_quantidade)))
            _criar_cabecalho_suspeitos(aba, negrito)
            limit_quantidade +=1
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, suspeito.id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 1, suspeito.denuncia_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 2, suspeito.tiposuspeito_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 3, suspeito.qtdesuspeitos)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 4, normalize_str(suspeito.nomeinstituicao))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 5, normalize_str(suspeito.nomenaoidentificado))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 6, suspeito.nome)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 7, suspeito.idade)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 8, normalize_str(suspeito.sexo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 9, normalize_str(suspeito.cor))     

@export_app.route('/criar-planilha')
def criar_planilha():
    try:
        date_now = datetime.now().strftime("_%Y_%m_%d_%H_%M_%S")
        workbook = xlsxwriter.Workbook('planilha_de_dados'+date_now+'.xlsx')
        
        #Format
        negrito = workbook.add_format({'bold': 1})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        #Format

        _criar_aba_denuncias(workbook, [], negrito, date_format)
        _criar_aba_violacoes(workbook, [], negrito, date_format)
        _criar_aba_vitimas(workbook, [], negrito, date_format)
        _criar_aba_suspeitos(workbook, [], negrito, date_format)

        workbook.close()

        return "Gerada."
    except TemplateNotFound:
        abort(404)
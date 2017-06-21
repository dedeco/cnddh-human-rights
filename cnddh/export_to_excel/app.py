# -*- coding: utf-8 -*-
from datetime import datetime
import StringIO
from flask import Blueprint, render_template, abort, request, send_file
from jinja2 import TemplateNotFound
from flask_login import login_required
import xlsxwriter

from cnddh.database import db
from cnddh.models import Denuncia, Violacao, Vitima, Suspeito, Encaminhamento
from cnddh.models import Oficio, Telefonema, Reuniao, Email, Generico
from cnddh.models import RetornoGenerico, RetornoPessoasassistidas, RetornoInquerito
from cnddh.models import RetornoProcesso, RetornoBO, RetornoRCO, RetornoREDS, RetornoPoliticaPSR
from cnddh.models import Cidade, Status, TipoLocal, TipoViolacao
from cnddh.models import TipoVitima, TipoSuspeito, Homicidio, HomicidioMeioUtilizado, TipoMeioUtilizado

from cnddh.export_to_excel.forms import ExportToExcelFiltroForm

from cnddh.decorators import checa_permissao
from cnddh.mapeamentos import estados_choices

export_app = Blueprint(
    'exportar-dados',
    __name__,
    url_prefix='/exportar-dados',
    template_folder='templates',
    static_folder='../static')

LIMIT_ROW = 1048576


def str_to_unicode_utf8(string):
    return unicode(string, 'utf-8')


def normalize_str(string):
    if string:
        if isinstance(string, unicode):
            return string
        else:
            return str_to_unicode_utf8(str(string))
    else:
        return ""


def _criar_cabecalho_homicidios(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Violação ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('C1', str_to_unicode_utf8('Numero da denuncia'), negrito)
    aba.write('D1', str_to_unicode_utf8('Periodo'), negrito)
    aba.write('E1', str_to_unicode_utf8('Situação'), negrito)
    aba.write('F1', str_to_unicode_utf8('Obs'), negrito)
    aba.write('G1', str_to_unicode_utf8('Meio'), negrito)

    # Largura
    aba.set_column('A:G', 20)

    # Filtro
    aba.autofilter('A1:G1')


def _criar_aba_homicidios(planilha, negrito, date_format, query):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Homicídios'))
    limit_quantidade = 0
    _criar_cabecalho_homicidios(aba, negrito)

    for index, item in enumerate(query, start=1):
        homicidio, tipo_meio = item
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(
                str_to_unicode_utf8('Violações_' + str(1 + limit_quantidade)))
            _criar_cabecalho_homicidios(aba, negrito)
            limit_quantidade += 1
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, homicidio.id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 1,
                         homicidio.denuncia_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 2,
                         homicidio.denuncia.numero)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 3,
                         normalize_str(homicidio.prfato))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 4,
                         normalize_str(homicidio.situacao))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 5,
                         normalize_str(homicidio.obs))
        if tipo_meio:
            aba.write_string(index - limit_quantidade * LIMIT_ROW, 6,
                             normalize_str(tipo_meio.meio))


def _criar_cabecalho_violacoes(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Violação ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('C1', str_to_unicode_utf8('Numero da denuncia'), negrito)
    aba.write('D1', str_to_unicode_utf8('Tipo'), negrito)
    aba.write('E1', str_to_unicode_utf8('Macro Categoria'), negrito)
    aba.write('F1', str_to_unicode_utf8('Micro Categoria'), negrito)
    aba.write('G1', str_to_unicode_utf8('Vítima ID'), negrito)
    aba.write('H1', str_to_unicode_utf8('Suspeitos ID'), negrito)

    # Largura
    aba.set_column('A:H', 20)

    # Filtro
    aba.autofilter('A1:H1')


def _criar_aba_violacoes(planilha, negrito, date_format, query):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Violações'))
    limit_quantidade = 0
    _criar_cabecalho_violacoes(aba, negrito)

    for index, item in enumerate(query, start=1):
        violacao, _ = item
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(
                str_to_unicode_utf8('Violações_' + str(1 + limit_quantidade)))
            _criar_cabecalho_violacoes(aba, negrito)
            limit_quantidade += 1

        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, violacao.id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 1,
                         violacao.denuncia_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 2,
                         violacao.denuncia.numero)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 3,
                         normalize_str(violacao.tipo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 4,
                         normalize_str(violacao.tipoviolacao.macrocategoria))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 5,
                         normalize_str(violacao.tipoviolacao.microcategoria))
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 6,
                         violacao.vitima_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 7,
                         violacao.suspeito_id)


def _create_cabecalho_denuncia(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Número'), negrito)
    aba.write('C1', str_to_unicode_utf8('Data Criação'), negrito)

    aba.write('D1', str_to_unicode_utf8('Data Denúncia'), negrito)
    # aba.write('E1', str_to_unicode_utf8('Status ID'), negrito)

    aba.write('F1', str_to_unicode_utf8('Status'), negrito)
    # aba.write('G1', str_to_unicode_utf8('Fonte ID'), negrito)
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

    # Largura
    aba.set_column('A:G', 13)
    aba.set_column('H:H', 25)
    aba.set_column('I:I', 13)
    aba.set_column('J:L', 25)
    aba.set_column('M:V', 20)

    # Filtro
    aba.autofilter('A1:V1')


def _criar_aba_denuncias(planilha, negrito, date_format, query):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Denúncias'))
    limit_quantidade = 0
    _create_cabecalho_denuncia(aba, negrito)
    tipos_de_locais = db.session.query(TipoLocal).all()
    dict_tipos_de_locais = {}
    for local in tipos_de_locais:
        dict_tipos_de_locais[local.id] = local.local

    for index, denuncia in enumerate(query, start=1):

        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(
                str_to_unicode_utf8('Denúncias_' + str(1 + limit_quantidade)))
            _create_cabecalho_denuncia(aba, negrito)
            limit_quantidade += 1
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, denuncia.id)
        aba.write(index - limit_quantidade * LIMIT_ROW, 1, denuncia.numero)
        aba.write_datetime(index - limit_quantidade * LIMIT_ROW, 2,
                           denuncia.dtcriacao, date_format)
        aba.write_datetime(index - limit_quantidade * LIMIT_ROW, 3,
                           denuncia.dtdenuncia, date_format)
        aba.write(index, 5, denuncia.status.status)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 7,
                         normalize_str(denuncia.fonte))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 8,
                         normalize_str(denuncia.protocolo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 9,
                         normalize_str(denuncia.resumo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 10,
                         normalize_str(denuncia.descricao))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 11,
                         normalize_str(denuncia.observacao))

        aba.write_string(
            index - limit_quantidade * LIMIT_ROW, 12,
            normalize_str(dict_tipos_de_locais[int(denuncia.tipolocal)]))
        aba.write(index - limit_quantidade * LIMIT_ROW, 13, denuncia.endereco)
        aba.write(index - limit_quantidade * LIMIT_ROW, 14, denuncia.num)
        aba.write(index - limit_quantidade * LIMIT_ROW, 15,
                  denuncia.complemento)
        aba.write(index - limit_quantidade * LIMIT_ROW, 16,
                  denuncia.referencia)
        aba.write(index - limit_quantidade * LIMIT_ROW, 17, denuncia.bairro)
        aba.write(index - limit_quantidade * LIMIT_ROW, 18, denuncia.cidade)
        aba.write(index - limit_quantidade * LIMIT_ROW, 19, denuncia.cep)
        aba.write(index - limit_quantidade * LIMIT_ROW, 20, denuncia.estado)
        aba.write(index - limit_quantidade * LIMIT_ROW, 21, denuncia.pais)


def _criar_cabecalho_vitimas(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Vítimas ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('C1', str_to_unicode_utf8('Numero da denuncia'), negrito)
    aba.write('D1', str_to_unicode_utf8('Tipo Vítima ID'), negrito)
    aba.write('E1', str_to_unicode_utf8('Quantidade De Vítimas'), negrito)
    aba.write('F1', str_to_unicode_utf8('Nome não identificado'), negrito)
    aba.write('G1', str_to_unicode_utf8('Nome'), negrito)
    aba.write('H1', str_to_unicode_utf8('Idade'), negrito)
    aba.write('I1', str_to_unicode_utf8('Sexo'), negrito)
    aba.write('J1', str_to_unicode_utf8('Cor'), negrito)

    # Largura
    aba.set_column('A:J', 20)

    # Filtro
    aba.autofilter('A1:J1')


def _criar_aba_vitimas(planilha, negrito, date_format, qr_vitima):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Vítimas'))
    limit_quantidade = 0

    _criar_cabecalho_vitimas(aba, negrito)

    for index, vitima in enumerate(qr_vitima, start=1):
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(
                str_to_unicode_utf8('Vítimas_' + str(1 + limit_quantidade)))
            _criar_cabecalho_vitimas(aba, negrito)
            limit_quantidade += 1
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, vitima.id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 1,
                         vitima.denuncia_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 2,
                         vitima.denuncia.numero)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 3,
                         vitima.tipovitima_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 4,
                         vitima.qtdevitimas)
        if vitima.nomenaoidentificado == u'0':
            aba.write_string(index - limit_quantidade * LIMIT_ROW, 5,
                             normalize_str(u"Não"))
        else:
            aba.write_string(index - limit_quantidade * LIMIT_ROW, 5,
                             normalize_str(u"Sim"))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 6,
                         normalize_str(vitima.nome))
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 7, vitima.idade)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 8,
                         normalize_str(vitima.sexo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 9,
                         normalize_str(vitima.cor))


def _criar_cabecalho_suspeitos(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Vítimas ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('C1', str_to_unicode_utf8('Numero da denuncia'), negrito)
    aba.write('D1', str_to_unicode_utf8('Tipo de Suspeito ID'), negrito)
    aba.write('E1', str_to_unicode_utf8('Quantidade de Suspeitos'), negrito)
    aba.write('F1', str_to_unicode_utf8('Nome Instituição'), negrito)
    aba.write('G1', str_to_unicode_utf8('Nome não identificado'), negrito)
    aba.write('H1', str_to_unicode_utf8('Nome'), negrito)
    aba.write('I1', str_to_unicode_utf8('Idade'), negrito)
    aba.write('J1', str_to_unicode_utf8('Sexo'), negrito)
    aba.write('K1', str_to_unicode_utf8('Cor'), negrito)

    # Largura
    aba.set_column('A:K', 20)

    # Filtro
    aba.autofilter('A1:K1')


Denuncia.id == Suspeito.denuncia_id,
Denuncia.id == Vitima.denuncia_id,


def _criar_aba_suspeitos(planilha, negrito, date_format, qr_suspeitos):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Suspeitos'))
    limit_quantidade = 0

    _criar_cabecalho_suspeitos(aba, negrito)

    for index, suspeito in enumerate(qr_suspeitos, start=1):
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(
                str_to_unicode_utf8('Suspeitos' + str(1 + limit_quantidade)))
            _criar_cabecalho_suspeitos(aba, negrito)
            limit_quantidade += 1

        aba.write_number(index - limit_quantidade * LIMIT_ROW, 0, suspeito.id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 1,
                         suspeito.denuncia_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 2,
                         suspeito.denuncia.numero)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 3,
                         suspeito.tiposuspeito_id)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 4,
                         suspeito.qtdesuspeitos)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 5,
                         normalize_str(suspeito.nomeinstituicao))
        if suspeito.nomenaoidentificado == u"0":
            aba.write_string(index - limit_quantidade * LIMIT_ROW, 6,
                             normalize_str(u"Não"))
        else:
            aba.write_string(index - limit_quantidade * LIMIT_ROW, 6,
                             normalize_str(u"Sim"))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 7,
                         suspeito.nome)
        aba.write_number(index - limit_quantidade * LIMIT_ROW, 8,
                         suspeito.idade)
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 9,
                         normalize_str(suspeito.sexo))
        aba.write_string(index - limit_quantidade * LIMIT_ROW, 10,
                         normalize_str(suspeito.cor))


def _criar_cabecalho_encaminhamento(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Encaminhamento ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Data Envio ID'), negrito)
    aba.write('C1', str_to_unicode_utf8('Data Limite'), negrito)
    aba.write('D1', str_to_unicode_utf8('Data Retorno'), negrito)
    aba.write('E1', str_to_unicode_utf8('Data Criação'), negrito)
    aba.write('F1', str_to_unicode_utf8('Tipo'), negrito)
    aba.write('G1', str_to_unicode_utf8('Orgão'), negrito)
    aba.write('H1', str_to_unicode_utf8('Tipo de Encaminhamento'), negrito)
    aba.write('I1', str_to_unicode_utf8('Ação'), negrito)
    aba.write('J1', str_to_unicode_utf8('Denuncia ID'), negrito)
    aba.write('J1', str_to_unicode_utf8('Tipo Encaminhamento'), negrito)

    # Largura
    aba.set_column('A:J', 20)

    # Filtro
    aba.autofilter('A1:J1')


def _criar_cabecalho_retorno(aba, negrito):
    aba.write('A1', str_to_unicode_utf8('Encaminhamento ID'), negrito)
    aba.write('B1', str_to_unicode_utf8('Tipo Retorno'), negrito)
    aba.write('C1', str_to_unicode_utf8('Denúncia ID'), negrito)
    aba.write('D1', str_to_unicode_utf8('Descrição'), negrito)
    aba.write('E1', str_to_unicode_utf8('Data Retorno'), negrito)
    aba.write('F1', str_to_unicode_utf8('Data Criação'), negrito)
    aba.write('G1', str_to_unicode_utf8('Tipo Nome'), negrito)

    # Largura
    aba.set_column('A:G', 20)

    # Filtro
    aba.autofilter('A1:G1')


def _criar_aba_encaminhamento(planilha, filtros, negrito, date_format):
    aba = planilha.add_worksheet(str_to_unicode_utf8('Encaminhamentos'))
    aba_retorno = planilha.add_worksheet(str_to_unicode_utf8('Retornos'))
    limit_quantidade = 0
    limite_quantidade_retorno = 0
    index_retorno_global = 1
    _criar_cabecalho_encaminhamento(aba, negrito)
    _criar_cabecalho_retorno(aba_retorno, negrito)

    for index, encaminhamento in enumerate(
            db.session.query(Encaminhamento).all(), start=1):
        if index > (LIMIT_ROW + limit_quantidade * LIMIT_ROW):
            aba = planilha.add_worksheet(
                str_to_unicode_utf8('Encaminhamentos' +
                                    str(1 + limit_quantidade)))
            _criar_cabecalho_encaminhamento(aba, negrito)
            limit_quantidade += 1
        aba.write(index - limit_quantidade * LIMIT_ROW, 0, encaminhamento.id)
        aba.write(index - limit_quantidade * LIMIT_ROW, 1,
                  encaminhamento.dtenvio)
        if encaminhamento.dtlimite:
            aba.write_datetime(index - limit_quantidade * LIMIT_ROW, 2,
                               encaminhamento.dtlimite, date_format)
        else:
            aba.write(index - limit_quantidade * LIMIT_ROW, 2,
                      encaminhamento.dtlimite)
        if encaminhamento.dtretorno:
            aba.write_datetime(index - limit_quantidade * LIMIT_ROW, 3,
                               encaminhamento.dtretorno, date_format)
        else:
            aba.write(index - limit_quantidade * LIMIT_ROW, 3,
                      encaminhamento.dtretorno)
        if encaminhamento.dtcriacao:
            aba.write_datetime(index - limit_quantidade * LIMIT_ROW, 4,
                               encaminhamento.dtcriacao, date_format)
        else:
            aba.write(index - limit_quantidade * LIMIT_ROW, 4,
                      encaminhamento.dtcriacao)
        aba.write(index - limit_quantidade * LIMIT_ROW, 5, encaminhamento.tipo)
        aba.write(index - limit_quantidade * LIMIT_ROW, 6,
                  encaminhamento.orgao.orgao)
        aba.write(index - limit_quantidade * LIMIT_ROW, 7,
                  encaminhamento.tipo_encaminhamento.tipo)
        aba.write(index - limit_quantidade * LIMIT_ROW, 8,
                  encaminhamento.historico.acao.acao)
        aba.write(index - limit_quantidade * LIMIT_ROW, 9,
                  encaminhamento.historico.denuncia_id)

        if isinstance(encaminhamento, Oficio):
            aba.write(index - limit_quantidade * LIMIT_ROW, 10, 'Oficio.')
        elif isinstance(encaminhamento, Telefonema):
            aba.write(index - limit_quantidade * LIMIT_ROW, 10, 'Telefonema.')
        elif isinstance(encaminhamento, Reuniao):
            aba.write(index - limit_quantidade * LIMIT_ROW, 10, 'Reuniao.')
        elif isinstance(encaminhamento, Email):
            aba.write(index - limit_quantidade * LIMIT_ROW, 10, 'Email.')
        elif isinstance(encaminhamento, Generico):
            aba.write(index - limit_quantidade * LIMIT_ROW, 10, 'Generico.')
        else:
            aba.write(index - limit_quantidade * LIMIT_ROW, 10, 'Indefinido.')

        for index_retorno, retorno in enumerate(encaminhamento.retorno):
            if index > (LIMIT_ROW + limite_quantidade_retorno * LIMIT_ROW):
                aba = planilha.add_worksheet(
                    str_to_unicode_utf8('Retornos' +
                                        str(1 + limite_quantidade_retorno)))
                _criar_cabecalho_retorno(aba_retorno, negrito)
                limite_quantidade_retorno += 1
            aba_retorno.write(
                index_retorno_global - limite_quantidade_retorno * LIMIT_ROW,
                0, retorno.encaminhamento_id)

            if isinstance(retorno, RetornoGenerico):
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Retorno Generico.')
            elif isinstance(retorno, RetornoPessoasassistidas):
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Retorno Pessoas Assistidas.')
            elif isinstance(retorno, RetornoInquerito):
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Retorno Inquerito.')
            elif isinstance(retorno, RetornoProcesso):
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Retorno Processo.')
            elif isinstance(retorno, RetornoBO):
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Retorno BO.')
            elif isinstance(retorno, RetornoRCO):
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Retorno RCO.')
            elif isinstance(retorno, RetornoREDS):
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Retorno REDS.')
            elif isinstance(retorno, RetornoPoliticaPSR):
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Retorno PoliticaPSR.')
            else:
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 1,
                                  'Indefinido.')

            aba_retorno.write(
                index_retorno_global - limite_quantidade_retorno * LIMIT_ROW,
                2, encaminhamento.historico.denuncia_id)
            aba_retorno.write(
                index_retorno_global - limite_quantidade_retorno * LIMIT_ROW,
                3, retorno.descricao)
            if retorno.dtretorno:
                aba_retorno.write_datetime(
                    index_retorno_global -
                    limite_quantidade_retorno * LIMIT_ROW, 4,
                    retorno.dtretorno, date_format)
            else:
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 4,
                                  retorno.dtretorno)
            if retorno.dtcriacao:
                aba_retorno.write_datetime(
                    index_retorno_global -
                    limite_quantidade_retorno * LIMIT_ROW, 5,
                    retorno.dtcriacao, date_format)
            else:
                aba_retorno.write(index_retorno_global -
                                  limite_quantidade_retorno * LIMIT_ROW, 5,
                                  retorno.dtcriacao)
            aba_retorno.write(
                index_retorno_global - limite_quantidade_retorno * LIMIT_ROW,
                6, retorno.tiporetorno.nome)

            index_retorno_global += 1


def _criar_planilha(encaminhamento, query, qr_vitima, qr_suspeitos,
                    qr_violacoes, qr_homicidios, formatos):
    try:

        output = StringIO.StringIO()
        date_now = datetime.now().strftime("_%Y_%m_%d_%H_%M_%S")
        workbook = xlsxwriter.Workbook(output)

        # Format
        negrito = workbook.add_format({'bold': 1})
        date_format = workbook.add_format({'num_format': formatos['data']})
        # Format

        _criar_aba_denuncias(workbook, negrito, date_format, query)
        _criar_aba_violacoes(workbook, negrito, date_format, qr_violacoes)
        _criar_aba_vitimas(workbook, negrito, date_format, qr_vitima)
        _criar_aba_suspeitos(workbook, negrito, date_format, qr_suspeitos)
        _criar_aba_homicidios(workbook, negrito, date_format, qr_homicidios)
        if encaminhamento:
            _criar_aba_encaminhamento(workbook, [], negrito, date_format)

        workbook.close()
        output.seek(0)
        return send_file(
            output,
            attachment_filename='planilha_de_dados' + date_now + '.xlsx',
            as_attachment=True)
        return "Gerada."
    except TemplateNotFound:
        abort(404)


@export_app.route('/obter-cidades/<string:estado>')
@login_required
def obter_cidade(estado):
    dict_estados = {estado: abrv for abrv, estado in estados_choices}
    estados = map(lambda x: dict_estados.get(x, ''),
                  filter(lambda x: len(x) > 0,
                         estado.replace("_", " ").split("-")))
    cidades = db.session.query(Cidade).filter(Cidade.estado.in_(estados))
    return render_template('_form_cidades.html', cidades=cidades)


@export_app.route('/obter-violacoes/<string:violacoes>')
@login_required
def obter_violacoes(violacoes):
    violacoes = violacoes.replace("_", " ").replace("@", "/").split("-")
    violacoes = db.session.query(TipoViolacao).filter(
        TipoViolacao.macrocategoria.in_(violacoes))
    return render_template('_form_violacoes.html', violacoes=violacoes)


@export_app.route('/obter-tipo-de-suspeitos/<string:suspeitos>')
@login_required
def obter_tipo_suspeitos(suspeitos):
    suspeitos = suspeitos.replace("_", " ").split("-")
    suspeitos = db.session.query(TipoSuspeito.instituicao).filter(
        TipoSuspeito.tipo.in_(suspeitos)).distinct()
    return render_template('_form_suspeitos.html', suspeitos=suspeitos)


def _add_filter_to_queries(querys, filter_):
    # querys -> list
    # filter -> sqlalchemy filter
    def add_filter(query):
        query = query.filter(filter_)
        return query

    return list(map(add_filter, querys))


@export_app.route('/', methods=['GET', 'POST'])
@login_required
@checa_permissao('exporta-dados')
def criar_planilha():
    form = ExportToExcelFiltroForm(request.form)

    if request.method == 'POST' and form.validate():
        filtro_suspeito_tipo_adicionado = False

        query = db.session.\
            query(Denuncia).\
            order_by(Denuncia.id)

        query_vitima = db.session.\
            query(Vitima).\
            join(Denuncia)

        query_suspeitos = db.session.\
            query(Suspeito).\
            join(Denuncia)

        query_violacoes = db.session.\
            query(Violacao, Homicidio).\
            join(Denuncia)

        query_homicidios = db.session.\
            query(Homicidio, TipoMeioUtilizado).\
            join(Violacao, Homicidio.id == Violacao.id).\
            join(Denuncia, Denuncia.id == Violacao.denuncia_id).\
            outerjoin(HomicidioMeioUtilizado, Homicidio.id == HomicidioMeioUtilizado.homicidio_id).\
            outerjoin(TipoMeioUtilizado, HomicidioMeioUtilizado.tipomeioutilizado_id == TipoMeioUtilizado.id )

        # _add_filter_to_queries(querys, )
        if form.data['suspeito_idade_inicio'] or\
            form.data['suspeito_idade_fim'] or\
            len(form.data['cor_suspeito']) > 0 or\
            len(form.data['sexo_suspeito']) > 0 or \
            len(form.data['tipo_de_suspeitos_tipo']) > 0 or\
            form.data['quantidade_de_suspeitos_inicio'] or\
            form.data['quantidade_de_suspeitos_fim'] or\
            len(form.data['tipo_de_suspeitos_instituicao']) > 0:

            query = query.join(Suspeito, Suspeito.denuncia_id == Denuncia.id)
            query_vitima = query_vitima.join(
                Suspeito, Suspeito.denuncia_id == Denuncia.id)
            query_violacoes = query_violacoes.join(
                Suspeito, Suspeito.denuncia_id == Denuncia.id)
            query_homicidios = query_homicidios.join(
                Suspeito, Suspeito.denuncia_id == Denuncia.id)

        if len(form.data['tipo_de_vitimas']) > 0 or\
            form.data['quantidade_de_vitimas_inicio'] or\
            form.data['quantidade_de_vitimas_fim'] or\
            form.data['vitima_idade_inicio'] or\
            form.data['vitima_idade_fim'] or\
            len(form.data['sexo_vitima']) > 0 or\
            form.data['cor_vitima']:

            query = query.join(Vitima, Vitima.denuncia_id == Denuncia.id)
            query_suspeitos = query_suspeitos.join(
                Vitima, Vitima.denuncia_id == Denuncia.id)
            query_violacoes = query_violacoes.join(
                Vitima, Vitima.denuncia_id == Denuncia.id)
            query_homicidios = query_homicidios.join(
                Vitima, Vitima.denuncia_id == Denuncia.id)

        if len(form.data['violacoes_macrocategoria']) > 0 or\
           len(form.data['violacoes_microcategoria']) > 0:
            query = query.\
                join(Violacao, Denuncia.id == Violacao.denuncia_id).\
                join(TipoViolacao, Violacao.tipoviolacoes_id == TipoViolacao.id)
            query_vitima = query_vitima.\
                join(Violacao, Denuncia.id == Violacao.denuncia_id).\
                join(TipoViolacao, Violacao.tipoviolacoes_id == TipoViolacao.id)
            query_suspeitos = query_suspeitos.\
                join(Violacao, Denuncia.id == Violacao.denuncia_id).\
                join(TipoViolacao, Violacao.tipoviolacoes_id == TipoViolacao.id)

        if len(form.data['homicidio_periodo']) > 0 or len(form.data['meio_utilizado']) > 0:
            query = query.\
                join(Violacao, Denuncia.id == Violacao.denuncia_id)
            query_vitima = query_vitima.\
                join(Violacao, Denuncia.id == Violacao.denuncia_id)
            query_suspeitos = query_suspeitos.\
                join(Violacao, Denuncia.id == Violacao.denuncia_id)
        if len(form.data['meio_utilizado']) > 0:
            query = query.\
                outerjoin(HomicidioMeioUtilizado, Homicidio.id == HomicidioMeioUtilizado.homicidio_id)

            query_vitima = query_vitima.\
                outerjoin(HomicidioMeioUtilizado, Homicidio.id == HomicidioMeioUtilizado.homicidio_id)
            query_suspeitos = query_suspeitos.\
                outerjoin(HomicidioMeioUtilizado, Homicidio.id == HomicidioMeioUtilizado.homicidio_id)

            query_violacoes = query_violacoes.\
                outerjoin(HomicidioMeioUtilizado, Homicidio.id == HomicidioMeioUtilizado.homicidio_id)

        querys = [
            query, query_vitima, query_suspeitos, query_violacoes,
            query_homicidios
        ]
        # Denuncias

        if len(form.data['cidades']) > 0:
            querys = _add_filter_to_queries(
                querys, Denuncia.cidade.in_(form.data['cidades']))

        if len(form.data['estados']) > 0:
            querys = _add_filter_to_queries(
                querys, Denuncia.estado.in_(form.data['estados']))

        if len(form.data['status_denuncia']) > 0:
            querys = _add_filter_to_queries(
                querys, Denuncia.status_id.in_(form.data['status_denuncia']))

        if len(form.data['tipo_de_locais']) > 0:
            querys = _add_filter_to_queries(
                querys, Denuncia.tipolocal.in_(form.data['tipo_de_locais']))

        if form.data['data_criacao_inicio'] and form.data['data_criacao_fim']:
            querys = _add_filter_to_queries(
                querys,
                Denuncia.dtcriacao.between(form.data['data_criacao_inicio'],
                                           form.data['data_criacao_fim']))
        elif form.data['data_criacao_inicio']:
            querys = _add_filter_to_queries(
                querys, Denuncia.dtcriacao >= form.data['data_criacao_inicio'])
        elif form.data['data_criacao_fim']:
            querys = _add_filter_to_queries(
                querys, Denuncia.dtcriacao <= form.data['data_criacao_fim'])

        if form.data['data_denuncia_inicio'] and form.data['data_denuncia_fim']:
            querys = _add_filter_to_queries(
                querys,
                Denuncia.dtcriacao.between(form.data['data_denuncia_inicio'],
                                           form.data['data_denuncia_fim']))
        elif form.data['data_denuncia_inicio']:
            querys = _add_filter_to_queries(
                querys,
                Denuncia.dtcriacao >= form.data['data_denuncia_inicio'])
        elif form.data['data_denuncia_fim']:
            querys = _add_filter_to_queries(
                querys, Denuncia.dtcriacao <= form.data['data_denuncia_fim'])

        if len(form.data['tipo_de_fontes']) > 0:
            querys = _add_filter_to_queries(
                querys, Denuncia.tipofonte_id.in_(form.data['tipo_de_fontes']))
        # FIM Denuncias
        # Violacoes
        if len(form.data['violacoes_macrocategoria']) > 0:
            querys = _add_filter_to_queries(
                querys,
                TipoViolacao.macrocategoria.in_(
                    form.data['violacoes_macrocategoria']))

        if len(form.data['violacoes_microcategoria']) > 0:
            querys = _add_filter_to_queries(
                querys,
                TipoViolacao.microcategoria.in_(
                    form.data['violacoes_microcategoria']))
        # Fim Violacoes

        # Vitimas
        if len(form.data['tipo_de_vitimas']) > 0:
            querys = _add_filter_to_queries(
                querys, Vitima.tipovitima_id.in_(form.data['tipo_de_vitimas']))

        if form.data['quantidade_de_vitimas_inicio'] and form.data['quantidade_de_vitimas_fim']:
            querys = _add_filter_to_queries(
                querys,
                Vitima.qtdevitimas.between(
                    form.data['quantidade_de_vitimas_inicio'],
                    form.data['quantidade_de_vitimas_fim']))
        elif form.data['quantidade_de_vitimas_inicio']:
            querys = _add_filter_to_queries(
                querys, Vitima.qtdevitimas >=
                form.data['quantidade_de_vitimas_inicio'])
        elif form.data['quantidade_de_vitimas_fim']:
            querys = _add_filter_to_queries(
                querys,
                Vitima.qtdevitimas <= form.data['quantidade_de_vitimas_fim'])

        if form.data['vitima_idade_inicio'] and form.data['vitima_idade_fim']:
            querys = _add_filter_to_queries(
                querys,
                Vitima.idade.between(form.data['vitima_idade_inicio'],
                                     form.data['vitima_idade_fim']))
        elif form.data['vitima_idade_inicio']:
            querys = _add_filter_to_queries(
                querys, Vitima.idade >= form.data['vitima_idade_inicio'])
        elif form.data['vitima_idade_fim']:
            querys = _add_filter_to_queries(
                querys, Vitima.idade <= form.data['vitima_idade_fim'])

        if len(form.data['sexo_vitima']) > 0:
            querys = _add_filter_to_queries(
                querys, Vitima.sexo.in_(form.data['sexo_vitima']))

        if len(form.data['cor_vitima']) > 0:
            querys = _add_filter_to_queries(
                querys, Vitima.cor.in_(form.data['cor_vitima']))
        # Fim Vitimas

        # Suspeitos

        if form.data['quantidade_de_suspeitos_inicio'] and form.data['quantidade_de_suspeitos_fim']:
            querys = _add_filter_to_queries(
                querys,
                Suspeito.qtdesuspeitos.between(
                    form.data['quantidade_de_suspeitos_inicio'],
                    form.data['quantidade_de_suspeitos_fim']))
        elif form.data['quantidade_de_suspeitos_inicio']:
            querys = _add_filter_to_queries(
                querys, Suspeito.qtdesuspeitos >=
                form.data['quantidade_de_suspeitos_inicio'])
        elif form.data['quantidade_de_suspeitos_fim']:
            querys = _add_filter_to_queries(
                querys, Suspeito.qtdesuspeitos <=
                form.data['quantidade_de_suspeitos_fim'])

        if len(form.data['tipo_de_suspeitos_tipo']) > 0:
            if not filtro_suspeito_tipo_adicionado:
                filtro_suspeito_tipo_adicionado = True

                def _do_join(query_):
                    return query_.join(
                        TipoSuspeito,
                        Suspeito.tiposuspeito_id == TipoSuspeito.id)

                querys = list(map(_do_join, querys))
                querys = _add_filter_to_queries(
                    querys,
                    TipoSuspeito.tipo.in_(form.data['tipo_de_suspeitos_tipo']))
            else:
                querys = _add_filter_to_queries(
                    querys,
                    TipoSuspeito.tipo.in_(form.data['tipo_de_suspeitos_tipo']))

        if len(form.data['tipo_de_suspeitos_instituicao']) > 0:
            if not filtro_suspeito_tipo_adicionado:
                filtro_suspeito_tipo_adicionado = True

                def _do_join(query_):
                    return query_.join(
                        TipoSuspeito,
                        Suspeito.tiposuspeito_id == TipoSuspeito.id)

                querys = list(map(_do_join, querys))
                querys = _add_filter_to_queries(
                    querys,
                    TipoSuspeito.instituicao.in_(
                        form.data['tipo_de_suspeitos_instituicao']))
            else:
                querys = _add_filter_to_queries(
                    querys,
                    TipoSuspeito.instituicao.in_(
                        form.data['tipo_de_suspeitos_instituicao']))

        if len(form.data['sexo_suspeito']) > 0:
            querys = _add_filter_to_queries(
                querys, Suspeito.sexo.in_(form.data['sexo_suspeito']))

        if len(form.data['cor_suspeito']) > 0:
            querys = _add_filter_to_queries(
                querys, Suspeito.cor.in_(form.data['cor_suspeito']))

        if form.data['suspeito_idade_inicio'] and form.data['suspeito_idade_fim']:
            querys = _add_filter_to_queries(
                querys,
                Suspeito.idade.between(form.data['suspeito_idade_inicio'],
                                       form.data['suspeito_idade_fim']))
        elif form.data['suspeito_idade_inicio']:
            querys = _add_filter_to_queries(
                querys, Suspeito.idade >= form.data['suspeito_idade_inicio'])
        elif form.data['suspeito_idade_fim']:
            querys = _add_filter_to_queries(
                querys, Suspeito.idade <= form.data['suspeito_idade_fim'])

        # FIM Suspeitos

        if len(form.data['homicidio_periodo']) > 0:
            querys = _add_filter_to_queries(
                querys, Homicidio.prfato.in_(form.data['homicidio_periodo']))

        if len(form.data['meio_utilizado']) > 0:
            querys = _add_filter_to_queries(
                querys, HomicidioMeioUtilizado.tipomeioutilizado_id.in_(form.data['meio_utilizado']))            

        # encaminhamento = form.data['recuperar_encaminhamentos']
        encaminhamento = False
        query, query_vitima, query_suspeitos, query_violacoes, query_homicidios = querys
        formatos = {}
        formatos['data'] = form.data['data_formato']
        return _criar_planilha(encaminhamento, query, query_vitima,
                               query_suspeitos, query_violacoes,
                               query_homicidios, formatos)

    return render_template('index.html', form=form)

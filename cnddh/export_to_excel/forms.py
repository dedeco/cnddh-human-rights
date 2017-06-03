# -*- coding: utf-8 -*-

from wtforms import Form
from wtforms import validators
from wtforms_components import DateRange
from wtforms import  SelectMultipleField#, DateField
from wtforms.fields.html5 import DateField
from wtforms.fields import IntegerField, BooleanField
from cnddh.database import db
from cnddh.models import Denuncia, Violacao, Vitima, Suspeito, Encaminhamento
from cnddh.models import Oficio, Telefonema, Reuniao, Email, Generico
from cnddh.models import RetornoGenerico, RetornoPessoasassistidas, RetornoInquerito
from cnddh.models import RetornoProcesso, RetornoBO, RetornoRCO, RetornoREDS, RetornoPoliticaPSR
from cnddh.models import Cidade, Status, TipoLocal, TipoViolacao
from cnddh.models import TipoVitima, TipoSuspeito

from cnddh.mapeamentos import estados_choices, sexo_choices, cor_choices, situacao_choices, periodo_choices, tipoassistencia_choices, politicas_choices

from datetime import date

class ExportToExcelFiltroForm(Form):
    class Meta:
        locales = ['pt_BR', 'pt']
    def __init__(self,  *args, **kwargs):
        super(ExportToExcelFiltroForm, self).__init__( *args, **kwargs)
      
        status = db.session.query(Status).order_by(Status.status).distinct()

        self.status_denuncia.choices = map(lambda item: (str(item.id), item.status), status)

        tipo_de_locais = db.session.query(TipoLocal).order_by(TipoLocal.local).distinct()
        self.tipo_de_locais.choices = map(lambda item: (str(item.id), item.local), tipo_de_locais)

        violacoes_macrocategoria = db.session.query(TipoViolacao.macrocategoria).order_by(TipoViolacao.macrocategoria).distinct(TipoViolacao.macrocategoria)
        self.violacoes_macrocategoria.choices = map(lambda item: (item.macrocategoria, item.macrocategoria), violacoes_macrocategoria)

        tipo_de_vitimas = db.session.query(TipoVitima).order_by(TipoVitima.tipo).distinct()
        self.tipo_de_vitimas.choices = tipo_de_vitimas = map(lambda item: (str(item.id), item.tipo), tipo_de_vitimas)

        tipo_suspeito_tipo = db.session.query(TipoSuspeito.tipo).order_by(TipoSuspeito.tipo).distinct()
        tipo_suspeito_instituicao = db.session.query(TipoSuspeito.instituicao).order_by(TipoSuspeito.instituicao).distinct()
        #TOdo One Query for both
        self.tipo_de_suspeitos_tipo.choices = map(lambda item: (item.tipo, item.tipo), tipo_suspeito_tipo)
        self.tipo_de_suspeitos_instituicao.choices = map(lambda item: (item.instituicao, item.instituicao), tipo_suspeito_instituicao)

    cidades = SelectMultipleField(u"Cidades",[], choices=[])
    estados = SelectMultipleField(u"Estados",[], choices=estados_choices)
    status_denuncia = SelectMultipleField(u"Status Denúncia",[], choices=[])
    tipo_de_locais = SelectMultipleField(u"Tipo de locais",[], choices=[])

    violacoes_macrocategoria = SelectMultipleField(u"Violações Macro Categoria",[], choices=[])
    violacoes_microcategoria = SelectMultipleField(u"Violações Macro Categoria",[], choices=[])
    tipo_de_vitimas = SelectMultipleField(u"Tipo de Vítimas",[], choices=[])
    quantidade_de_vitimas_inicio = IntegerField(u"Quantidade de vítimas", [validators.optional(), validators.NumberRange(0, 50)])
    quantidade_de_vitimas_fim = IntegerField(u"Quantidade de vítimas", [validators.optional(), validators.NumberRange(0, 50)])
    data_criacao_inicio = DateField(u'Data criação inicio', [validators.optional()])
    data_criacao_fim = DateField(u'Data criação fim', [validators.optional()])
    data_denuncia_inicio = DateField(u'Data denúncia', [validators.optional()])
    data_denuncia_fim = DateField(u'Data denúncia', [validators.optional()])
    sexo_vitima = SelectMultipleField(u"Sexo", [], choices=sexo_choices)
    cor_vitima = SelectMultipleField(u"Cor", [], choices=cor_choices)
    
    vitima_idade_inicio = IntegerField(u"Idade", [validators.optional()])
    vitima_idade_fim = IntegerField(u"Idade", [validators.optional()])

    tipo_de_suspeitos_tipo = SelectMultipleField(u"Tipo de Suspeitos",[], choices=[])
    tipo_de_suspeitos_instituicao = SelectMultipleField(u"Tipo de Suspeitos",[], choices=[])
    quantidade_de_suspeitos_inicio = IntegerField(u"Quantidade de suspeitos", [validators.optional(), validators.NumberRange(0, 50)])
    quantidade_de_suspeitos_fim = IntegerField(u"Quantidade de suspeitos", [validators.optional(), validators.NumberRange(0, 50)])
    sexo_suspeito = SelectMultipleField(u"Sexo", [], choices=sexo_choices)
    cor_suspeito = SelectMultipleField(u"Cor", [], choices=cor_choices)
    

    suspeito_idade_inicio = IntegerField(u"Idade", [validators.optional()])
    suspeito_idade_fim = IntegerField(u"Idade", [validators.optional()])

    recuperar_encaminhamentos = BooleanField(u"Recuperar Encaminhamentos", [])
    #TODO FIltro encaminhamento e retorno?


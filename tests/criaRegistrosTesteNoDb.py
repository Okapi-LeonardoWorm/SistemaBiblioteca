from multiprocessing import Pool
from time import strftime
from random import randint
from datetime import date, timedelta, datetime
import unicodedata

from flask import json
from app import createApp, db
from app.models import User, Book, KeyWord
from .criaUserAdmin import criaAdminUser


"""
Execute com: python -m tests.criaRegistrosTesteNoDb
"""


"""
$terms = @(
 'Literatura de Ficção Científica', 'Literatura Noir', 'Literatura Erótica', 'Literatura Policial', 'Literatura Juvenil', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura de Aventura', 'Realismo Mágico', 'Literatura de Cordel', 'Literatura Oral', 'Literatura Indígena', 'Literatura Afro-Brasileira', 'Literatura Feminista', 'Literatura LGBTQIA+', 'Auto-Retrato', 'Cronista', 'Poeta', 'Dramaturgista', 'Romancista', 'Contista', 'Poeta', 'Narrador', 'Personagem', 'Protagonista', 'Antagonista', 'Narrador', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Narrativa em Primeira Pessoa', 'Narrativa em Terceira Pessoa', 'Narrativa Onisciente', 'Narrativa Onipresente', 'Monólogo Interior', 'Fragmento', 'Epícope', 'Metáfora', 'Metonímia', 'Hipérbole', 'Ironia', 'Sátira', 'Paródia', 'Eufemismo', 'Hipérbato', 'Anáfora', 'Assíndeto', 'Polissíndeto', 'Anáfora', 'Assíndeto', 'Polissíndeto'
)
python .\tests\find_books.py --query $terms --max-per-query 10 --out res.json
"""


KEYWORDS = ['Realismo', 'Naturalismo', 'Romantismo', 'Modernismo', 'Simbolismo', 'Decadentismo', 'Futurismo', 'Cubismo', 'Surrealismo', 'Existencialismo', 'Psicanálise', 'Expressionismo', 'Dadaísmo', 'Abstracionismo', 'Marinismo', 'Fluxus', 'Minimalismo', 'Postmodernismo', 'Neorrealismo', 'Neoexpressionismo', 'Metafísica', 'Neoclassicismo', 'Barroco', 'Classicismo', 'Epicurismo', 'Estoicismo', 'Pré-Romantismo', 'Romantismo Gótico', 'Parnasianismo', 'Simbolismo', 'Estridentismo', 'Surrealismo', 'Modernismo Brasileiro', 'Neo-Realismo Italiano', 'Literatura Fantástica', 'Literatura de Terror', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura Infantil', 'Literatura de Ficção Científica', 'Literatura Noir', 'Literatura Erótica', 'Literatura Policial', 'Literatura Juvenil', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura de Aventura', 'Literatura de Contos', 'Literatura Juvenil', 'Literatura de Aventura', 'Realismo Mágico', 'Literatura de Cordel', 'Literatura Oral', 'Literatura Indígena', 'Literatura Afro-Brasileira', 'Literatura Feminista', 'Literatura LGBTQIA+', 'Auto-Retrato', 'Cronista', 'Poeta', 'Dramaturgista', 'Romancista', 'Contista', 'Poeta', 'Narrador', 'Personagem', 'Protagonista', 'Antagonista', 'Narrador', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Narrativa em Primeira Pessoa', 'Narrativa em Terceira Pessoa', 'Narrativa Onisciente', 'Narrativa Onipresente', 'Monólogo Interior', 'Fragmento', 'Epícope', 'Metáfora', 'Metonímia', 'Hipérbole', 'Ironia', 'Sátira', 'Paródia', 'Eufemismo', 'Hipérbato', 'Anáfora', 'Assíndeto', 'Polissíndeto', 'Anáfora', 'Assíndeto', 'Polissíndeto', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Personificação', 'Hipérbole', 'Anáfora', 'Assíndeto', 'Polissíndeto', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa Não Linear', 'Monólogo Interior', 'Estilo Literário', 'Linguagem Literária', 'Vocabulário', 'Estilo', 'Tema', 'Motivo', 'Estilo Narrativo', 'Narrativa Linear', 'Narrativa']

"""
USERS = [
  { "userId": 1, "identificationCode": "admin.teste123", "password": "admin123", "userCompleteName": "João da Silva", "userType": "admin", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 1, "userPhone": "(11) 99999-9999", "birthDate": "1980-05-10", "cpf": "123.456.789-01", "rg": "1234567", "gradeNumber": "", "className": "", "guardianName1": "Maria da Silva", "guardianPhone1": "(11) 98888-8888", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 2, "identificationCode": "lib.teste456", "password": "bibliotecario123", "userCompleteName": "Ana Paula Souza", "userType": "bibliotecario", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 2, "userPhone": "(21) 97777-7777", "birthDate": "1992-11-20", "cpf": "987.654.321-02", "rg": "6789012", "gradeNumber": "", "className": "6º Ano", "guardianName1": "Carlos Souza", "guardianPhone1": "(21) 96666-6666", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 3, "identificationCode": "col.teste789", "password": "colaborador123", "userCompleteName": "Ricardo Oliveira", "userType": "colaborador", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 3, "userPhone": "(31) 95555-5555", "birthDate": "1985-03-15", "cpf": "111.222.333-444", "rg": "3334445", "gradeNumber": 1, "className": "1º Ano", "guardianName1": "Patrícia Oliveira", "guardianPhone1": "(31) 94444-4444", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 4, "identificationCode": "alu.teste012", "password": "aluno123", "userCompleteName": "Laura Santos", "userType": "aluno", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 4, "userPhone": "(44) 93333-3333", "birthDate": "2012-07-22", "cpf": "555.666.777-888", "rg": "7778889", "gradeNumber": 2, "className": "7º Ano", "guardianName1": "José Santos", "guardianPhone1": "(44) 92111-1111", "guardianName2": "Maria Silva", "guardianPhone2": "(44) 91111-1111", "notes": "Precisa de acompanhamento pedagógico." },
  { "userId": 5, "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Pedro Almeida", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 5, "userPhone": "(61) 94444-4444", "birthDate": "1978-09-03", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "", "guardianPhone1": "", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 6, "identificationCode": "alu.teste678", "password": "aluno123", "userCompleteName": "Gabriel Rodrigues", "userType": "aluno", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 6, "userPhone": "(55) 94321-1234", "birthDate": "2010-12-05", "cpf": "999.888.777-666", "rg": "5556667", "gradeNumber": 3, "className": "2º Ano", "guardianName1": "Ana Souza", "guardianPhone1": "(55) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 7, "identificationCode": "alu.teste901", "password": "aluno123", "userCompleteName": "Isabela Ferreira", "userType": "aluno", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 7, "userPhone": "(77) 92111-1234", "birthDate": "2011-04-18", "cpf": "444.555.666-777", "rg": "8889990", "gradeNumber": 4, "className": "3º Ano", "guardianName1": "Ricardo Costa", "guardianPhone1": "(77) 91111-2222", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 8, "identificationCode": "alu.teste234", "password": "aluno123", "userCompleteName": "Lucas Pereira", "userType": "aluno", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 8, "userPhone": "(88) 94321-2345", "birthDate": "2013-08-29", "cpf": "777.888.999-000", "rg": "9991111", "gradeNumber": 5, "className": "4º Ano", "guardianName1": "Fernanda Lima", "guardianPhone1": "(88) 93333-4444", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 9, "identificationCode": "alu.teste567", "password": "aluno123", "userCompleteName": "Matheus Carvalho", "userType": "aluno", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 9, "userPhone": "(99) 94321-3456", "birthDate": "2014-06-14", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": 6, "className": "5º Ano", "guardianName1": "Carlos Santos", "guardianPhone1": "(99) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 10, "identificationCode": "alu.teste890", "password": "aluno123", "userCompleteName": "Sofia Almeida", "userType": "aluno", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 10, "userPhone": "(101) 94321-4567", "birthDate": "2015-03-01", "cpf": "999.888.999-000", "rg": "8889990", "gradeNumber": 7, "className": "6º Ano", "guardianName1": "Maria Rodrigues", "guardianPhone1": "(101) 93333-6666", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 11, "identificationCode": "vis.teste123", "password": "visitante123", "userCompleteName": "Vinícius Costa", "userType": "visitante", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 11, "userPhone": "(22) 94321-5678", "birthDate": "1982-12-20", "cpf": "777.888.777-888", "rg": "9991111", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(22) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 12, "identificationCode": "vis.teste456", "password": "visitante123", "userCompleteName": "Isabela Souza", "userType": "visitante", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 12, "userPhone": "(33) 94321-6789", "birthDate": "1990-04-10", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Pedro Santos", "guardianPhone1": "(33) 93333-8888", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 13, "identificationCode": "vis.teste789", "password": "visitante123", "userCompleteName": "Ricardo Pereira", "userType": "visitante", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 13, "userPhone": "(44) 94321-7890", "birthDate": "1975-09-25", "cpf": "777.888.999-000", "rg": "9991111", "gradeNumber": "", "className": "", "guardianName1": "Ana Costa", "guardianPhone1": "(44) 93333-9999", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 14, "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Silva", "userType": "visitante", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 14, "userPhone": "(55) 94321-8901", "birthDate": "1988-06-12", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Sofia Lima", "guardianPhone1": "(55) 93333-1111", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 15, "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Matheus Ferreira", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 15, "userPhone": "(66) 94321-9012", "birthDate": "1970-03-05", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(66) 93333-2222", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 16, "identificationCode": "vis.teste678", "password": "visitante123", "userCompleteName": "Sofia Almeida", "userType": "visitante", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 16, "userPhone": "(77) 94321-0123", "birthDate": "1999-11-08", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(77) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 17, "identificationCode": "vis.teste890", "password": "visitante123", "userCompleteName": "Matheus Pereira", "userType": "visitante", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 17, "userPhone": "(88) 94321-1234", "birthDate": "1982-04-19", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Costa", "guardianPhone1": "(88) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 18, "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Souza", "userType": "visitante", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 18, "userPhone": "(99) 94321-2345", "birthDate": "1980-01-26", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Santos", "guardianPhone1": "(99) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 19, "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Matheus Ferreira", "userType": "visitante", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 19, "userPhone": "(101) 94321-3456", "birthDate": "1985-10-12", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(101) 93333-9999", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 20, "identificationCode": "vis.teste678", "password": "visitante123", "userCompleteName": "Sofia Almeida", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 20, "userPhone": "(22) 94321-0123", "birthDate": "1990-02-14", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(22) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 21, "identificationCode": "vis.teste890", "password": "visitante123", "userCompleteName": "Matheus Pereira", "userType": "visitante", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 21, "userPhone": "(33) 94321-1234", "birthDate": "1999-05-27", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(33) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 22, "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Souza", "userType": "visitante", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 22, "userPhone": "(44) 94321-2345", "birthDate": "1982-08-15", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Santos", "guardianPhone1": "(44) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 23, "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Matheus Ferreira", "userType": "visitante", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 23, "userPhone": "(55) 94321-1234", "birthDate": "1980-04-17", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(55) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 24, "identificationCode": "vis.teste678", "password": "visitante123", "userCompleteName": "Sofia Almeida", "userType": "visitante", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 24, "userPhone": "(66) 94321-0123", "birthDate": "1985-11-22", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(66) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 25, "identificationCode": "vis.teste890", "password": "visitante123", "userCompleteName": "Matheus Pereira", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 25, "userPhone": "(77) 94321-1234", "birthDate": "1991-06-09", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Santos", "guardianPhone1": "(77) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 26, "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Souza", "userType": "visitante", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 26, "userPhone": "(88) 94321-2345", "birthDate": "1983-03-11", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Santos", "guardianPhone1": "(88) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 27, "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Matheus Ferreira", "userType": "visitante", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 27, "userPhone": "(99) 94321-1234", "birthDate": "1984-07-18", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(99) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 28, "identificationCode": "vis.teste678", "password": "visitante123", "userCompleteName": "Sofia Almeida", "userType": "visitante", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 28, "userPhone": "(101) 94321-0123", "birthDate": "1992-02-03", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(101) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 29, "identificationCode": "vis.teste890", "password": "visitante123", "userCompleteName": "Matheus Pereira", "userType": "visitante", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 29, "userPhone": "(22) 94321-1234", "birthDate": "1986-08-19", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(22) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "userId": 30, "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Souza", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 30, "userPhone": "(33) 94321-1234", "birthDate": "1987-01-24", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(33) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" }
]
"""

USERS = [
  { "identificationCode": "admin.teste123", "password": "admin123", "userCompleteName": "João da Silva", "userType": "admin", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 1, "userPhone": "(11) 99999-9999", "birthDate": "1980-05-10", "cpf": "123.456.789-01", "rg": "1234567", "gradeNumber": "", "className": "", "guardianName1": "Maria da Silva", "guardianPhone1": "(11) 98888-8888", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "lib.teste456", "password": "bibliotecario123", "userCompleteName": "Ana Paula Souza", "userType": "bibliotecario", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 2, "userPhone": "(21) 97777-7777", "birthDate": "1992-11-20", "cpf": "987.654.321-02", "rg": "6789012", "gradeNumber": "", "className": "6º Ano", "guardianName1": "Carlos Souza", "guardianPhone1": "(21) 96666-6666", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "col.teste789", "password": "colaborador123", "userCompleteName": "Ricardo Oliveira", "userType": "colaborador", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 3, "userPhone": "(31) 95555-5555", "birthDate": "1985-03-15", "cpf": "111.222.333-444", "rg": "3334445", "gradeNumber": 1, "className": "1º Ano", "guardianName1": "Patrícia Oliveira", "guardianPhone1": "(31) 94444-4444", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "alu.teste012", "password": "aluno123", "userCompleteName": "Laura Santos", "userType": "aluno", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 4, "userPhone": "(44) 93333-3333", "birthDate": "2012-07-22", "cpf": "555.666.777-888", "rg": "7778889", "gradeNumber": 2, "className": "7º Ano", "guardianName1": "José Santos", "guardianPhone1": "(44) 92111-1111", "guardianName2": "Maria Silva", "guardianPhone2": "(44) 91111-1111", "notes": "Precisa de acompanhamento pedagógico." },
  { "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Pedro Almeida", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 5, "userPhone": "(61) 94444-4444", "birthDate": "1978-09-03", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "", "guardianPhone1": "", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "alu.teste678", "password": "aluno123", "userCompleteName": "Gabriel Rodrigues", "userType": "aluno", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 6, "userPhone": "(55) 94321-1234", "birthDate": "2010-12-05", "cpf": "999.888.777-666", "rg": "5556667", "gradeNumber": 3, "className": "2º Ano", "guardianName1": "Ana Souza", "guardianPhone1": "(55) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "alu.teste901", "password": "aluno123", "userCompleteName": "Isabela Ferreira", "userType": "aluno", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 7, "userPhone": "(77) 92111-1234", "birthDate": "2011-04-18", "cpf": "444.555.666-777", "rg": "8889990", "gradeNumber": 4, "className": "3º Ano", "guardianName1": "Ricardo Costa", "guardianPhone1": "(77) 91111-2222", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "alu.teste234", "password": "aluno123", "userCompleteName": "Lucas Pereira", "userType": "aluno", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 8, "userPhone": "(88) 94321-2345", "birthDate": "2013-08-29", "cpf": "777.888.999-000", "rg": "9991111", "gradeNumber": 5, "className": "4º Ano", "guardianName1": "Fernanda Lima", "guardianPhone1": "(88) 93333-4444", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "alu.teste567", "password": "aluno123", "userCompleteName": "Matheus Carvalho", "userType": "aluno", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 9, "userPhone": "(99) 94321-3456", "birthDate": "2014-06-14", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": 6, "className": "5º Ano", "guardianName1": "Carlos Santos", "guardianPhone1": "(99) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "alu.teste890", "password": "aluno123", "userCompleteName": "Sofia Almeida", "userType": "aluno", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 10, "userPhone": "(101) 94321-4567", "birthDate": "2015-03-01", "cpf": "999.888.999-000", "rg": "8889990", "gradeNumber": 7, "className": "6º Ano", "guardianName1": "Maria Rodrigues", "guardianPhone1": "(101) 93333-6666", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste123", "password": "visitante123", "userCompleteName": "Vinícius Costa", "userType": "visitante", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 11, "userPhone": "(22) 94321-5678", "birthDate": "1982-12-20", "cpf": "777.888.777-888", "rg": "9991111", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(22) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste456", "password": "visitante123", "userCompleteName": "Isabela Souza", "userType": "visitante", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 12, "userPhone": "(33) 94321-6789", "birthDate": "1990-04-10", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Pedro Santos", "guardianPhone1": "(33) 93333-8888", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste789", "password": "visitante123", "userCompleteName": "Ricardo Pereira", "userType": "visitante", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 13, "userPhone": "(44) 94321-7890", "birthDate": "1975-09-25", "cpf": "777.888.999-000", "rg": "9991111", "gradeNumber": "", "className": "", "guardianName1": "Ana Costa", "guardianPhone1": "(44) 93333-9999", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Silva", "userType": "visitante", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 14, "userPhone": "(55) 94321-8901", "birthDate": "1988-06-12", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Sofia Lima", "guardianPhone1": "(55) 93333-1111", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Matheus Ferreira", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 15, "userPhone": "(66) 94321-9012", "birthDate": "1970-03-05", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(66) 93333-2222", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste678", "password": "visitante123", "userCompleteName": "Sofia Almeida", "userType": "visitante", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 16, "userPhone": "(77) 94321-0123", "birthDate": "1999-11-08", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(77) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste890", "password": "visitante123", "userCompleteName": "Matheus Pereira", "userType": "visitante", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 17, "userPhone": "(88) 94321-1234", "birthDate": "1982-04-19", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Costa", "guardianPhone1": "(88) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Souza", "userType": "visitante", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 18, "userPhone": "(99) 94321-2345", "birthDate": "1980-01-26", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Santos", "guardianPhone1": "(99) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Matheus Ferreira", "userType": "visitante", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 19, "userPhone": "(101) 94321-3456", "birthDate": "1985-10-12", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(101) 93333-9999", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste678", "password": "visitante123", "userCompleteName": "Sofia Almeida", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 20, "userPhone": "(22) 94321-0123", "birthDate": "1990-02-14", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(22) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste890", "password": "visitante123", "userCompleteName": "Matheus Pereira", "userType": "visitante", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 21, "userPhone": "(33) 94321-1234", "birthDate": "1999-05-27", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(33) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Souza", "userType": "visitante", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 22, "userPhone": "(44) 94321-2345", "birthDate": "1982-08-15", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Santos", "guardianPhone1": "(44) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Matheus Ferreira", "userType": "visitante", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 23, "userPhone": "(55) 94321-1234", "birthDate": "1980-04-17", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(55) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste678", "password": "visitante123", "userCompleteName": "Sofia Almeida", "userType": "visitante", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 24, "userPhone": "(66) 94321-0123", "birthDate": "1985-11-22", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(66) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste890", "password": "visitante123", "userCompleteName": "Matheus Pereira", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 25, "userPhone": "(77) 94321-1234", "birthDate": "1991-06-09", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Santos", "guardianPhone1": "(77) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Souza", "userType": "visitante", "creationDate": "2024-10-26", "lastUpdate": "2024-10-26", "createdBy": 1, "updatedBy": 26, "userPhone": "(88) 94321-2345", "birthDate": "1983-03-11", "cpf": "777.888.999-000", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Ana Santos", "guardianPhone1": "(88) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste345", "password": "visitante123", "userCompleteName": "Matheus Ferreira", "userType": "visitante", "creationDate": "2024-10-27", "lastUpdate": "2024-10-27", "createdBy": 1, "updatedBy": 27, "userPhone": "(99) 94321-1234", "birthDate": "1984-07-18", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(99) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste678", "password": "visitante123", "userCompleteName": "Sofia Almeida", "userType": "visitante", "creationDate": "2024-10-28", "lastUpdate": "2024-10-28", "createdBy": 1, "updatedBy": 28, "userPhone": "(101) 94321-0123", "birthDate": "1992-02-03", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(101) 93333-3333", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste890", "password": "visitante123", "userCompleteName": "Matheus Pereira", "userType": "visitante", "creationDate": "2024-10-29", "lastUpdate": "2024-10-29", "createdBy": 1, "updatedBy": 29, "userPhone": "(22) 94321-1234", "birthDate": "1986-08-19", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Oliveira", "guardianPhone1": "(22) 93333-5555", "guardianName2": "", "guardianPhone2": "", "notes": "" },
  { "identificationCode": "vis.teste012", "password": "visitante123", "userCompleteName": "Lucas Souza", "userType": "visitante", "creationDate": "2024-10-30", "lastUpdate": "2024-10-30", "createdBy": 1, "updatedBy": 30, "userPhone": "(33) 94321-1234", "birthDate": "1987-01-24", "cpf": "888.999.000-111", "rg": "9991112", "gradeNumber": "", "className": "", "guardianName1": "Luís Santos", "guardianPhone1": "(33) 93333-7777", "guardianName2": "", "guardianPhone2": "", "notes": "" }
]


def hash_password(pw: str) -> str:
    try:
        from flask_bcrypt import Bcrypt  # type: ignore
        return Bcrypt().generate_password_hash(pw).decode('utf-8')
    except Exception:
        try:
            import bcrypt as _bcrypt  # type: ignore
            return _bcrypt.hashpw(pw.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')
        except Exception:
            return pw  # fallback: texto puro


def _normalize_tag(token: str) -> str:
    if not token:
        return ''
    token = token.strip()
    nfkd = unicodedata.normalize('NFKD', token)
    ascii_only = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    up = ascii_only.upper()
    return ' '.join(up.split())


def insert_users(start, end):
    app = createApp()
    with app.app_context():
        users = []
        for i in range(start, end):
            username = f"user_{i}"
            password = f"passWord_{i}"
            hashed_password = hash_password(password)

            # birthDate obrigatório no modelo
            birth = date(2000, 1, 1) + timedelta(days=i % 365)

            # pular se já existe
            if db.session.query(User.userId).filter_by(identificationCode=username).first():
                continue

            new_user = User(
                username=username,  # synonym para identificationCode
                password=hashed_password,
                userType="visitor",
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
                createdBy=1,
                updatedBy=1,
                birthDate=birth,
                userCompleteName=f"User {i}",
            )
            users.append(new_user)

            if len(users) % 1000 == 0:
                db.session.bulk_save_objects(users)
                print(f"Users - {strftime('%H:%M:%S')}: {i}")
                db.session.commit()
                users = []

        if users:
            db.session.bulk_save_objects(users)
            print(f"Users - {strftime('%H:%M:%S')}: {i}")
            db.session.commit()


def insert_users_from_list(user_list):
    app = createApp()
    with app.app_context():
        for user in user_list:
            username = user.get("identificationCode")
            password = user.get("password", "defaultPassword")
            hashed_password = hash_password(password)

            # birthDate obrigatório no modelo
            birth_str = user.get("birthDate")
            if birth_str:
                try:
                    birth = datetime.strptime(birth_str, "%Y-%m-%d").date()
                except ValueError:
                    birth = date(2000, 1, 1)
            else:
                birth = date(2000, 1, 1)

            # Tratamento de datas de criação e atualização
            creationDate_str = user.get("creationDate")
            lastUpdate_str = user.get("lastUpdate")
            
            try:
                creationDate = datetime.strptime(creationDate_str, "%Y-%m-%d %H:%M:%S") if creationDate_str else datetime.now()
            except ValueError:
                try:
                    creationDate = datetime.strptime(creationDate_str, "%Y-%m-%d") if creationDate_str else datetime.now()
                except ValueError:
                    creationDate = datetime.now()

            try:
                lastUpdate = datetime.strptime(lastUpdate_str, "%Y-%m-%d %H:%M:%S") if lastUpdate_str else datetime.now()
            except ValueError:
                try:
                    lastUpdate = datetime.strptime(lastUpdate_str, "%Y-%m-%d") if lastUpdate_str else datetime.now()
                except ValueError:
                    lastUpdate = datetime.now()

            # pular se já existe
            if db.session.query(User.userId).filter_by(identificationCode=username).first():
                continue

            new_user = User(
                username=username,  # synonym para identificationCode
                password=hashed_password,
                userType=user.get("userType", "visitor"),
                creationDate=creationDate,
                lastUpdate=lastUpdate,
                createdBy=1,
                updatedBy=1,
                birthDate=birth,
                userCompleteName=user.get("userCompleteName"),
                userPhone=user.get("userPhone"),
                cpf=user.get("cpf"),
                rg=user.get("rg"),
                gradeNumber=user.get("gradeNumber"),
                className=user.get("className"),
                guardianName1=user.get("guardianName1"),
                guardianPhone1=user.get("guardianPhone1"),
                guardianName2=user.get("guardianName2"),
                guardianPhone2=user.get("guardianPhone2"),
                notes=user.get("notes"),
            )
            try:
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                print(f"Erro ao inserir usuário '{username}': {e}")
                db.session.rollback()


def insert_books(start, end):
    app = createApp()
    with app.app_context():
        books = []
        for i in range(start, end):
            bookName = f"book_{i}"
            amount = randint(1, 100)
            authorName = f"author_{i}"
            publisherName = f"publisher_{i}"
            publishedDate = date.today()
            acquisitionDate = datetime.now()
            description = f"description_{i}"

            new_book = Book(
                bookName=bookName,
                amount=amount,
                authorName=authorName,
                publisherName=publisherName,
                publishedDate=publishedDate,
                acquisitionDate=acquisitionDate,
                description=description,
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
                createdBy=1,
                updatedBy=1,
            )
            books.append(new_book)

            if len(books) % 100 == 0:
                db.session.bulk_save_objects(books)
                print(f"Books - {strftime('%H:%M:%S')}: {i}")
                db.session.commit()
                books = []

        if books:
            db.session.bulk_save_objects(books)
            print(f"Books - {strftime('%H:%M:%S')}: {i}")
            db.session.commit()


def get_books_from_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
            if isinstance(data, list):
                return data
            else:
                print("O conteúdo do arquivo JSON não é uma lista.")
                return []
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar o arquivo JSON: {e}")
            return []


def insert_books_from_list(book_list):
    app = createApp()
    with app.app_context():
        for book in book_list:
            bookName = book.get("bookName")
            amount = book.get("amount", 1)
            authorName = book.get("authorName", "Unknown Author")
            publisherName = book.get("publisherName", "Unknown Publisher")
            publishedDate_str = book.get("publishedDate")
            acquisitionDate_str = book.get("acquisitionDate")
            description = book.get("description", "")

            try:
                publishedDate = datetime.strptime(publishedDate_str, "%Y-%m-%d").date() if publishedDate_str else date.today()
            except ValueError:
                publishedDate = date.today()

            try:
                acquisitionDate = datetime.strptime(acquisitionDate_str, "%Y-%m-%d %H:%M:%S") if acquisitionDate_str else datetime.now()
            except ValueError:
                try:
                    acquisitionDate = datetime.strptime(acquisitionDate_str, "%Y-%m-%d") if acquisitionDate_str else datetime.now()
                except ValueError:
                    acquisitionDate = datetime.now()

            new_book = Book(
                bookName=bookName,
                amount=amount,
                authorName=authorName,
                publisherName=publisherName,
                publishedDate=publishedDate,
                acquisitionDate=acquisitionDate,
                description=description,
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
                createdBy=1,
                updatedBy=1,
            )
            try:
                db.session.add(new_book)
                db.session.commit()
            except Exception as e:
                print(f"Erro ao inserir livro '{bookName}': {e}")
                db.session.rollback()


def insert_keyWord(start, end):
    app = createApp()
    with app.app_context():
        words = []
        for i in range(start, end):
            word = _normalize_tag(f"word_{i}")

            # pular se já existe
            if db.session.query(KeyWord.wordId).filter_by(word=word).first():
                continue

            new_keyWord = KeyWord(
                word=word,
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
                createdBy=1,
                updatedBy=1,
            )
            words.append(new_keyWord)

            if len(words) % 1000 == 0:
                db.session.bulk_save_objects(words)
                print(f"KeyWords - {strftime('%H:%M:%S')}: {i}")
                db.session.commit()
                words = []

        if words:
            db.session.bulk_save_objects(words)
            print(f"KeyWords - {strftime('%H:%M:%S')}: {i}")
            db.session.commit()


def insert_keyword_from_list(list):
    app = createApp()
    with app.app_context():
        for i in list:
            word = _normalize_tag(i)

            # pular se já existe
            if db.session.query(KeyWord.wordId).filter_by(word=word).first():
                continue

            new_keyWord = KeyWord(
                word=word,
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
                createdBy=1,
                updatedBy=1,
            )
            try:
                db.session.add(new_keyWord)
                db.session.commit()
            except Exception as e:
                print(f"Erro ao inserir keyword '{word}': {e}")
                db.session.rollback()
    

if __name__ == "__main__":
    # Cria um usuário admin para poder inserir registros no banco de dados
    a = criaAdminUser()
    
    num_processes = 4  # Number of parallel processes
    BATCH_SIZE = 10
    # TOTAL_USERS = 20
    # TOTAL_KEYWORDS = 20
    # TOTAL_BOOKS = 20

    def build_batches(total):
        batches = []
        start = 1
        while start <= total:
            end = min(start + BATCH_SIZE, total + 1)
            batches.append((start, end))
            start = end
        return batches

    # user_batches = build_batches(TOTAL_USERS)
    # book_batches = build_batches(TOTAL_BOOKS)
    # keyWord_batches = build_batches(TOTAL_KEYWORDS)

    # with Pool(num_processes) as pool:
        # try:
        #     pool.starmap(insert_users, user_batches)
        # except Exception as e:
        #     print(f"Erro ao inserir usuários: {e}")
        # try:
        #     pool.starmap(insert_books, book_batches)
        # except:
        #     pass
        # try:
        #     pool.starmap(insert_keyWord, keyWord_batches)
        # except Exception as e:
        #     print(f"Erro ao inserir keywords: {e}")
    
    # insert_users_from_list(USERS)
    
    # insert_keyword_from_list(KEYWORDS)
    
    books_list = get_books_from_json_file('tests/livros_teste.json')
    insert_books_from_list(books_list)

    print("Done!")

# run me with -> python -m tests.criaRegistrosTesteNoDb

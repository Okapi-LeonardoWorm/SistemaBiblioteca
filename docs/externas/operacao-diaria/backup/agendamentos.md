# Agendamentos de Backup

## Objetivo

Orientar criacao e manutencao de agendamentos de backup.

## Onde fazer

Tela: Gestao de Backup > secao Novo Agendamento.

## Campos

- Nome: identificacao do agendamento.
- Frequencia: daily ou weekly.
- Horario: formato HH:MM.
- Dias semana: usado no modo weekly (0-6).
  - 0 = segunda, 6 = domingo (seguindo padrao interno).
- Timezone: ex. America/Sao_Paulo.
- Ativo: define se o agendamento entra em execucao.

## Como criar

1. Preencha os campos.
2. Clique em Salvar Agendamento.
3. Verifique a coluna Proxima Execucao na lista.

## Como editar

1. Ajuste os campos na linha do agendamento.
2. Clique em Salvar.

## Como pausar e reativar

- Botao Pausar desativa execucao.
- Botao Ativar reabilita e recalcula proxima execucao.

## Como excluir

- Clique em Excluir na linha desejada e confirme.

## Erros comuns

- Horario invalido: usar HH:MM.
- Sem dias no semanal: preencher ao menos um dia (0-6).
- Frequencia invalida: usar daily ou weekly.

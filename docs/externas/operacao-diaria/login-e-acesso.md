# Atualizacao de Login e Acesso

## O que mudou

1. O login agora aceita **codigo ou email** no mesmo campo.
2. O sistema nao diferencia maiusculas e minusculas no login.
3. O campo aceita identificadores maiores (ate 150 caracteres).
4. Se o usuario ja estiver logado e abrir `/login`, ele sera redirecionado automaticamente:
   - Admin -> Dashboard
   - Demais perfis -> Menu
5. **[NOVO]** O que você vê no sistema (botões, menus e funcionalidades) após o login é gerado dinamicamente com base nas **permissões** do seu perfil e pode ser configurado pelo Administrador. Saiba mais sobre os [Níveis de Permissão](./permissoes-e-acessos.md).

## Como preencher o login

- Digite seu codigo de acesso **ou** email cadastrado.
- A senha continua obrigatoria.
- Espacos extras nas extremidades sao ignorados.

## Possiveis impactos para usuarios antigos

Em casos raros de conflito legado (mesmo login com diferenca apenas de maiusculas/minusculas), um dos logins pode ter sido ajustado para manter unicidade.

Se um usuario nao conseguir entrar com o login antigo:

1. Conferir o cadastro atualizado no modulo de usuarios.
2. Tentar o login em minusculas.
3. Acionar administrador do sistema para confirmar identificador final.

## Perguntas rapidas

- Nao consigo abrir a tela de login quando ja estou no sistema:
  - Isso e esperado; o sistema redireciona automaticamente para a tela inicial do perfil.
- Posso continuar usando codigo ao inves de email?
  - Sim.
- Posso usar email com letras maiusculas?
  - Sim; o sistema normaliza para comparacao interna.

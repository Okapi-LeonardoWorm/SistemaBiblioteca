# Permissões e Acessos Dinâmicos

O Sistema de Biblioteca opera com um modelo de acesso baseado em diferentes **Níveis de Permissão**, garantindo que as operações mais críticas sejam restritas.

O sistema divide os usuários nos seguintes papéis principais, em ordem de acesso (do mais restrito ao mais amplo):
1. **Aluno** (Leitura básica e acesso pessoal)
2. **Colaborador** (Gerenciamento moderado)
3. **Bibliotecário** (Gestão avançada)
4. **Administrador** (Controle total do sistema)

## Telas Visíveis vs Acesso Negado

Um aspecto fundamental deste novo sistema é o comportamento das telas e botões. **O sistema ocultará automaticamente** qualquer botão, menu ou tela para a qual a sua conta atual não tenha nível suficiente de permissão. 

Por exemplo, se um usuário tiver permissão para ver os livros, mas não tiver o nível mínimo exigido para apagá-los, o botão **"Excluir"** sequer aparecerá em sua interface.

**Caso você tente forçar o acesso** (ex: colando uma URL de uma tela para a qual você não possui permissões), o sistema bloqueará a página exibindo um alerta ("Você não tem permissão para acessar essa área") e te redirecionará para uma página segura (geralmente o Menu de Operação).

## O Administrador tem o controle

As permissões atreladas a cada funcionalidade do sistema não são rígidas. O **Administrador** pode alterar o nível exigido para acessar as funcionalidades através do menu **Configurações**.

Desta forma, se o seu ambiente permitir, o Administrador pode, por exemplo:
- Liberar a "Importação em Lote de Usuários" para Bibliotecários (Nível 3).
- Exigir que apenas o Administrador (Nível 4) consiga apagar um Livro do acervo.
- Liberar acesso às telas de Backup para todos os colaboradores.

Caso sinta falta de uma funcionalidade que anteriormente estava disponível, contate o Administrador de sua unidade para que ele revise as permissões concedidas.

# Sistema de Permissões e Autorização

A partir da versão mais recente, o sistema de permissões foi completamente reformulado. Antigamente baseado em verificações estáticas de papel (ex: `current_user.userType == 'admin'`), o sistema agora é dinâmico e suportado pelo banco de dados.

O núcleo desta lógica encontra-se em `app/utils/auth_utils.py`.

## Arquitetura de Permissões

### Níveis de Acesso
O sistema converte os papéis de usuários textuais em um nível numérico hierárquico (`USER_TYPE_LEVELS`):
- `aluno` = Nível 1
- `colaborador` = Nível 2
- `bibliotecario` = Nível 3
- `admin` = Nível 4

As rotas e recursos já não verificam a "string" do tipo de usuário, mas validam se o *nível numérico do usuário logado é maior ou igual ao nível configurado para o recurso*.

### Armazenamento e Configuração
As permissões são controladas pelas tabelas `Configuration` e `ConfigSpec`. 
No `auth_utils.py`, a variável `PERMISSION_LEVEL_CONFIG_SPECS` detalha quais chaves de configuração existem, seus valores padrão e limites permitidos (1 a 4).

O método `ensure_permission_level_configs()` é chamado durante o boot da aplicação para garantir que o banco possua todas essas configurações registradas. Assim, um Administrador pode mudar os níveis requeridos pelo painel de *Configurações* do próprio sistema.

## Helpers de Acesso (Backend)

Sempre utilize os métodos em `app/utils/auth_utils.py` para verificar acessos, seja em rotas ou serviços.

- **`can_access_feature(feature_name)`**: Retorna `True` ou `False`. Baseado em `FEATURE_CONFIG_MAP`, verifica o nível do usuário logado contra a configuração.
- **`enforce_feature_access(feature_name, message)`**: Ideal para rotas comuns (`@login_required`). Retorna um `redirect` (com um `flash` alertando sobre a falta de permissão) caso o usuário não tenha acesso. Caso contrário, retorna `None`.
- **`enforce_api_feature_access(feature_name, message)`**: Ideal para rotas JSON. Retorna uma tupla `(jsonify, 403)` se não autorizado.

Exemplo de uso:
```python
from app.utils.auth_utils import enforce_feature_access

@bp.route('/excluir_livro/<int:id>', methods=['POST'])
@login_required
def delete_book(id):
    # Trava a rota de imediato se o nivel for incompatível
    error_response = enforce_feature_access('books_delete', 'Você não tem permissão para excluir livros.')
    if error_response:
        return error_response
    
    # Restante da lógica de exclusão...
```

## Permissões no Frontend (Templates)

Para não poluir o Jinja com consultas de banco repetitivas, todas as permissões são exportadas para os templates via contexto global no `app/__init__.py`. 

A função `build_permission_capabilities()` em `auth_utils.py` gera um dicionário contendo flags booleanas (`can_view_books`, `can_delete_users`, etc.). No Jinja, esse dicionário está disponível como a variável `permissions`.

Exemplo no HTML:
```html
{% if permissions.can_delete_books %}
    <button type="submit" class="btn btn-danger">Excluir Livro</button>
{% endif %}
```

## Como registrar uma nova permissão

Se você precisar de um novo controle (exemplo: `relatorios_gerais`):
1. **Adicione a especificação** em `PERMISSION_LEVEL_CONFIG_SPECS` dentro do `auth_utils.py` (defina o nome da chave, default, max/min level e description).
2. **Adicione o mapeamento** em `FEATURE_CONFIG_MAP`, vinculando um nome curto (ex: `reports_general`) à chave criada.
3. **Exporte a capacidade** para os templates adicionando uma linha em `build_permission_capabilities()` (ex: `'can_view_reports': can_access_feature('reports_general')`).
4. Utilize `permissions.can_view_reports` nos templates e `enforce_feature_access('reports_general', ...)` na rota Backend.

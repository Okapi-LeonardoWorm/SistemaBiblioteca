from flask import Flask

from .admin_sessions import bp as admin_sessions_bp
from .apis import bp as apis_bp
from .audit_logs import bp as audit_logs_bp
from .auth import bp as auth_bp
from .backups import bp as backups_bp
from .books import bp as books_bp
from .configs import bp as configs_bp
from .keywords import bp as keywords_bp
from .loans import bp as loans_bp
from .navigation import bp as navigation_bp
from .users import bp as users_bp

BLUEPRINTS = [
    auth_bp,
    navigation_bp,
    backups_bp,
    books_bp,
    loans_bp,
    keywords_bp,
    users_bp,
    configs_bp,
    apis_bp,
    audit_logs_bp,
    admin_sessions_bp,
]

LEGACY_ENDPOINT_ALIASES = {
    'main.index': 'auth.index',
    'main.login': 'auth.login',
    'main.logout': 'auth.logout',
    'main.register': 'auth.register',
    'main.dashboard': 'navigation.dashboard',
    'main.menu': 'navigation.menu',
    'main.livros': 'books.livros',
    'main.get_book_form': 'books.get_book_form',
    'main.novo_livro': 'books.novo_livro',
    'main.editar_livro': 'books.editar_livro',
    'main.excluir_livro': 'books.excluir_livro',
    'main.emprestimos': 'loans.emprestimos',
    'main.cancelar_emprestimo': 'loans.cancelar_emprestimo',
    'main.get_loan_form': 'loans.get_loan_form',
    'main.novo_emprestimo': 'loans.novo_emprestimo',
    'main.editar_emprestimo': 'loans.editar_emprestimo',
    'main.informar_retorno_emprestimo': 'loans.informar_retorno_emprestimo',
    'main.excluir_emprestimo': 'loans.excluir_emprestimo',
    'main.palavras_chave': 'keywords.palavras_chave',
    'main.get_keyword_form': 'keywords.get_keyword_form',
    'main.nova_palavra_chave': 'keywords.nova_palavra_chave',
    'main.editar_palavra_chave': 'keywords.editar_palavra_chave',
    'main.excluir_palavra_chave': 'keywords.excluir_palavra_chave',
    'main.list_users': 'users.list_users',
    'main.get_user_form': 'users.get_user_form',
    'main.new_user': 'users.new_user',
    'main.edit_user': 'users.edit_user',
    'main.check_identification_code': 'users.check_identification_code',
    'main.delete_user': 'users.delete_user',
    'main.configuracoes': 'configs.configuracoes',
    'main.get_config_form': 'configs.get_config_form',
    'main.nova_configuracao': 'configs.nova_configuracao',
    'main.editar_configuracao': 'configs.editar_configuracao',
    'main.api_search_users': 'apis.api_search_users',
    'main.api_search_books': 'apis.api_search_books',
    'main.audit_logs': 'audit_logs.audit_logs',
    'main.manage_sessions': 'admin_sessions.manage_sessions',
    'main.revoke_session': 'admin_sessions.revoke_session',
}


def _register_legacy_aliases(app: Flask):
    for legacy_endpoint, target_endpoint in LEGACY_ENDPOINT_ALIASES.items():
        if target_endpoint not in app.view_functions:
            continue

        target_view = app.view_functions[target_endpoint]
        target_rules = [rule for rule in app.url_map.iter_rules() if rule.endpoint == target_endpoint]

        for rule in target_rules:
            methods = sorted([m for m in rule.methods if m not in {'HEAD', 'OPTIONS'}])
            app.add_url_rule(rule.rule, endpoint=legacy_endpoint, view_func=target_view, methods=methods)


def register_blueprints(app: Flask):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    _register_legacy_aliases(app)

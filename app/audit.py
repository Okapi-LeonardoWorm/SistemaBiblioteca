from sqlalchemy import event, inspect
from flask_login import current_user
from app import db
from app.models import AuditLog
import json
from datetime import datetime, date


def get_current_user_id():
    try:
        if current_user and current_user.is_authenticated:
            return current_user.userId
    except Exception:
        pass
    return None


def json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def get_changes_insert(target):
    changes = {}
    
    # Também filtrar campos técnicos em CREATE para ficar consistente
    ignored_fields = {'lastUpdate', 'updatedBy', 'creationDate', 'createdBy'}

    try:
        mapper = inspect(target).mapper
        for prop in mapper.column_attrs:
            key = prop.key
            if key in ignored_fields:
                continue

            # Ignora colunas privadas ou relacionais/complexas
            if not key.startswith('_'):
                 value = getattr(target, key)
                 changes[key] = value
    except Exception:
        pass
    return changes


def get_changes_update(target):
    changes = {}
    
    # Campos técnicos que não devem gerar log se forem a única alteração
    # Mas se houver OUTRAS alterações, talvez seja interessante?
    # O usuário pediu para não registrar "nada à toa".
    # Se eu mudar o nome, e o lastUpdate muda, o log deve conter nome e lastUpdate?
    # Geralmente Audit Log foca no que o usuário mudou explicitamente.
    # Vamos manter simples: ignorar esses campos completamente no output do 'changes'.
    ignored_fields = {'lastUpdate', 'updatedBy', 'creationDate', 'createdBy'}

    try:
        attrs = inspect(target).attrs
        for attr in attrs:
            if attr.key in ignored_fields:
                continue
            
            history = attr.history
            if history.has_changes():
                new_value = history.added[0] if history.added else None
                old_value = history.deleted[0] if history.deleted else None
                
                # Se valores forem iguais (ex: setou mesma string), ignora
                if new_value == old_value:
                    continue

                changes[attr.key] = new_value
    except Exception:
        pass
    return changes


def create_audit_log(connection, action, target_type, target_id, changes=None, user_id=None):
    # Se action for UPDATE/DELETE, 'changes' deve ser um dicionário não vazio
    if changes is not None and isinstance(changes, dict) and not changes:
         return
    
    if user_id is None:
        user_id = get_current_user_id()

    changes_json = None
    if changes:

        try:
            changes_json = json.dumps(changes, default=json_serializer)
        except Exception:
            changes_json = str(changes)

    audit_table = AuditLog.__table__
    try:
        connection.execute(
            audit_table.insert().values(
                timestamp=datetime.now(),
                user_id=user_id,
                action=action,
                target_type=target_type,
                target_id=str(target_id) if target_id is not None else None,
                changes=changes_json
            )
        )
    except Exception as e:
        print(f"Erro ao salvar log de auditoria: {e}")


def after_insert_listener(mapper, connection, target):
    if isinstance(target, AuditLog): return
    changes = get_changes_insert(target)
    pk = _get_pk(target)
    create_audit_log(connection, 'CREATE', target.__class__.__name__, pk, changes)


def after_update_listener(mapper, connection, target):
    if isinstance(target, AuditLog): return
    changes = get_changes_update(target)
    if changes:
        pk = _get_pk(target)
        create_audit_log(connection, 'UPDATE', target.__class__.__name__, pk, changes)


def after_delete_listener(mapper, connection, target):
    if isinstance(target, AuditLog): return
    changes = get_changes_insert(target) # Salva estado antes de deletar
    pk = _get_pk(target)
    create_audit_log(connection, 'DELETE', target.__class__.__name__, pk, changes)


def _get_pk(target):
    try:
        mapper = inspect(target).mapper
        pk_props = mapper.primary_key
        if pk_props:
             pks = [str(getattr(target, prop.key)) for prop in pk_props]
             return "-".join(pks)
    except:
        return None


def register_listeners(app):
    from app import models
    import inspect as py_inspect

    # Registra listeners para todas as classes que herdam de db.Model exceto AuditLog
    # Precisamos iterar sobre as classes definidas no models que são Models do SQLAlchemy
    for name, obj in py_inspect.getmembers(models):
        if py_inspect.isclass(obj) and issubclass(obj, db.Model):
             if obj != AuditLog:
                 if hasattr(obj, '__tablename__'):
                     event.listen(obj, 'after_insert', after_insert_listener)
                     event.listen(obj, 'after_update', after_update_listener)
                     event.listen(obj, 'after_delete', after_delete_listener)


def log_manual_event(action, target_type='System', target_id=None, changes=None):
    try:
        # Usamos ORM para logs manuais
        user_id = get_current_user_id()
        if user_id is None and action == 'LOGIN':
             if target_type == 'User' and target_id:
                 try:
                     user_id = int(target_id)
                 except:
                     pass

        changes_json = None
        if changes:
             import json
             try:
                 changes_json = json.dumps(changes, default=json_serializer)
             except:
                 changes_json = str(changes)

        log_entry = AuditLog(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            changes=changes_json
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
    except Exception as e:
        print(f"Erro ao salvar log manual: {e}")
        db.session.rollback()




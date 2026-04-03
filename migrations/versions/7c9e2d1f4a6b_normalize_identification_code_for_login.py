"""normalize identificationCode for code or email login

Revision ID: 7c9e2d1f4a6b
Revises: 5d3a2f1b9c4e
Create Date: 2026-04-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c9e2d1f4a6b'
down_revision = '5d3a2f1b9c4e'
branch_labels = None
depends_on = None


def _normalize_and_resolve_conflicts(bind):
    rows = bind.execute(
        sa.text('SELECT "userId", "identificationCode" FROM users ORDER BY "userId"')
    ).mappings().all()

    used = set()
    planned_updates = []

    for row in rows:
        user_id = row['userId']
        current_code = row['identificationCode'] or ''
        base_code = current_code.lower()
        target_code = base_code

        if target_code in used:
            suffix_index = 1
            while True:
                suffix = f'__{user_id}' if suffix_index == 1 else f'__{user_id}_{suffix_index}'
                max_base_len = 150 - len(suffix)
                candidate = f'{base_code[:max_base_len]}{suffix}'
                if candidate not in used:
                    target_code = candidate
                    break
                suffix_index += 1

        used.add(target_code)

        if target_code != current_code:
            planned_updates.append({'user_id': user_id, 'current': current_code, 'target': target_code})

    if not planned_updates:
        return

    occupied = set((row['identificationCode'] or '').lower() for row in rows)
    target_values = set(item['target'] for item in planned_updates)

    # Fase 1: move para valores temporários únicos para evitar colisão no índice unique existente.
    for item in planned_updates:
        user_id = item['user_id']
        tmp_code = f'__tmp_norm_{user_id}__'
        suffix_index = 1
        while tmp_code in occupied or tmp_code in target_values:
            tmp_code = f'__tmp_norm_{user_id}_{suffix_index}__'
            suffix_index += 1

        occupied.add(tmp_code)
        item['tmp'] = tmp_code
        bind.execute(
            sa.text('UPDATE users SET "identificationCode" = :code WHERE "userId" = :user_id'),
            {'code': tmp_code, 'user_id': user_id},
        )

    # Fase 2: aplica o valor final normalizado/resolvido.
    for item in planned_updates:
        bind.execute(
            sa.text('UPDATE users SET "identificationCode" = :code WHERE "userId" = :user_id'),
            {'code': item['target'], 'user_id': item['user_id']},
        )


def upgrade():
    bind = op.get_bind()

    # Padroniza identificadores para minúsculas e resolve colisões legacy sem diferenciar caixa.
    _normalize_and_resolve_conflicts(bind)

    # Garante tamanho compatível com identificadores longos e emails completos.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'identificationCode',
            existing_type=sa.String(length=150),
            type_=sa.String(length=150),
            existing_nullable=False,
        )


def downgrade():
    # A normalização para minúsculas não é reversível sem histórico.
    pass

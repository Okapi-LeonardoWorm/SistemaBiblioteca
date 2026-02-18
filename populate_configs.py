from app import createApp, db
from app.models import Configuration, ConfigSpec, User
from datetime import datetime

def populate_configs():
    app = createApp()
    with app.app_context():
        print("Iniciando verificação e população de configurações iniciais...")

        # Tenta encontrar um usuário admin para atribuir a criação (ou usa ID 1 se não achar)
        admin_user = User.query.filter_by(userType='admin').first()
        admin_id = admin_user.userId if admin_user else 1

        # Definição das configurações padrões
        default_configs = [
            {
                "key": "TEMPO_MAXIMO_PARA_CANCELAMENTO_DE_EMPRESTIMO",
                "value": "15",
                "description": "Tempo em minutos que o usuário tem para cancelar um empréstimo realizado por engano.",
                "spec": {
                    "valueType": "integer",
                    "minValue": 0,
                    "maxValue": 1440, # 24 horas
                    "required": True,
                    "defaultValue": "15",
                    "description": "Defina 0 para desativar o cancelamento."
                }
            },
            {
                "key": "PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_ATIVO",
                "value": "1",
                "description": "Permite que a observação inicial seja editada enquanto o empréstimo estiver Ativo.",
                "spec": {
                    "valueType": "boolean",
                    "required": True,
                    "defaultValue": "1",
                    "description": "1 = Sim, 0 = Não"
                }
            },
            {
                "key": "PERMITE_ALTERAR_OBSERVACAO_INICIAL_EMPRESTIMO_FINALIZADO",
                "value": "0",
                "description": "Permite editar a observação inicial após o empréstimo ser finalizado (Devolvido/Perdido).",
                "spec": {
                    "valueType": "boolean",
                    "required": True,
                    "defaultValue": "0",
                    "description": "1 = Sim, 0 = Não"
                }
            },
            {
                "key": "PERMITE_ALTERAR_OBSERVACAO_FINAL_EMPRESTIMO_FINALIZADO",
                "value": "1",
                "description": "Permite editar a observação de devolução após o empréstimo ser finalizado.",
                "spec": {
                    "valueType": "boolean",
                    "required": True,
                    "defaultValue": "1",
                    "description": "1 = Sim, 0 = Não"
                }
            }
        ]

        for item in default_configs:
            key = item['key']
            
            # 1. Verifica/Cria a Especificação (ConfigSpec)
            spec = ConfigSpec.query.filter_by(key=key).first()
            if not spec:
                print(f"Criando especificação para: {key}")
                spec_data = item['spec']
                new_spec = ConfigSpec(
                    key=key,
                    valueType=spec_data['valueType'],
                    minValue=spec_data.get('minValue'),
                    maxValue=spec_data.get('maxValue'),
                    required=spec_data.get('required', False),
                    defaultValue=spec_data.get('defaultValue'),
                    description=spec_data.get('description'),
                    creationDate=datetime.now(),
                    lastUpdate=datetime.now(),
                    createdBy=admin_id,
                    updatedBy=admin_id
                )
                db.session.add(new_spec)
            
            # 2. Verifica/Cria o Valor (Configuration)
            config = Configuration.query.filter_by(key=key).first()
            if not config:
                print(f"Criando valor padrão para: {key}")
                new_config = Configuration(
                    key=key,
                    value=item['value'],
                    description=item['description'],
                    creationDate=datetime.now(),
                    lastUpdate=datetime.now(),
                    createdBy=admin_id,
                    updatedBy=admin_id
                )
                db.session.add(new_config)
            else:
                print(f"Configuração {key} já existe. Pulando.")

        try:
            db.session.commit()
            print("Processo concluído com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar configurações: {e}")

if __name__ == "__main__":
    populate_configs()

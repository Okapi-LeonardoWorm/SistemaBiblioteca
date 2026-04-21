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
                "key": "DASHBOARD_LOST_THRESHOLD_DAYS",
                "value": "30",
                "description": "Dias de atraso para considerar extravio no painel de saúde do acervo.",
                "spec": {
                    "valueType": "integer",
                    "minValue": 1,
                    "maxValue": 365,
                    "required": True,
                    "defaultValue": "30",
                    "description": "Usado no dashboard para classificar itens perdidos por atraso prolongado."
                }
            },
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
            },
            {
                "key": "SESSION_LIFETIME_HOURS",
                "value": "12",
                "description": "Tempo máximo de duração da sessão do usuário em horas.",
                "spec": {
                    "valueType": "integer",
                    "minValue": 1,
                    "maxValue": 168, # 1 semana
                    "required": True,
                    "defaultValue": "12",
                    "description": "Número de horas antes da sessão expirar."
                }
            },
            {
                "key": "SESSION_INACTIVITY_MINUTES",
                "value": "60",
                "description": "Tempo máximo de inatividade em minutos antes da sessão expirar.",
                "spec": {
                    "valueType": "integer",
                    "minValue": 5,
                    "maxValue": 720,
                    "required": True,
                    "defaultValue": "60",
                    "description": "Minutos de inatividade permitidos."
                }
            },
            {
                "key": "BULK_IMPORT_USER_REQUIRED_COLUMNS_ALUNO",
                "value": "identificationCode,password,userCompleteName,birthDate",
                "description": "Colunas obrigatórias para importação em massa de criação de usuários do tipo aluno.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "identificationCode,password,userCompleteName,birthDate",
                    "description": "Lista de campos separados por vírgula."
                }
            },
            {
                "key": "BULK_IMPORT_USER_REQUIRED_COLUMNS_COLABORADOR",
                "value": "identificationCode,password,userCompleteName,birthDate",
                "description": "Cópia da configuração de colunas obrigatórias para importação em massa de colaboradores.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "identificationCode,password,userCompleteName,birthDate",
                    "description": "Lista de campos separados por vírgula."
                }
            },
            {
                "key": "BULK_IMPORT_USER_REQUIRED_COLUMNS_BIBLIOTECARIO",
                "value": "identificationCode,password,userCompleteName,birthDate",
                "description": "Cópia da configuração de colunas obrigatórias para importação em massa de bibliotecários.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "identificationCode,password,userCompleteName,birthDate",
                    "description": "Lista de campos separados por vírgula."
                }
            },
            {
                "key": "BULK_IMPORT_USER_REQUIRED_COLUMNS_ADMIN",
                "value": "identificationCode,password,userCompleteName,birthDate",
                "description": "Cópia da configuração de colunas obrigatórias para importação em massa de administradores.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "identificationCode,password,userCompleteName,birthDate",
                    "description": "Lista de campos separados por vírgula."
                }
            },
            {
                "key": "BACKUP_LOCAL_DIRECTORY",
                "value": "",
                "description": "Diretório local do Windows para armazenamento dos arquivos de backup. Em branco usa instance/backups.",
                "spec": {
                    "valueType": "string",
                    "required": False,
                    "defaultValue": "",
                    "description": "Caminho absoluto no servidor Windows que executa o sistema."
                }
            },
            {
                "key": "BACKUP_RETENTION_DAYS",
                "value": "30",
                "description": "Quantidade de dias para retenção dos backups locais.",
                "spec": {
                    "valueType": "integer",
                    "minValue": 1,
                    "maxValue": 3650,
                    "required": True,
                    "defaultValue": "30",
                    "description": "Arquivos locais mais antigos que este prazo podem ser removidos."
                }
            },
            {
                "key": "BACKUP_SCREEN_MIN_VIEW_LEVEL",
                "value": "3",
                "description": "Nível mínimo para visualizar a tela de backup (1=aluno, 2=colaborador, 3=bibliotecario, 4=admin).",
                "spec": {
                    "valueType": "enum",
                    "allowedValues": "1,2,3,4",
                    "required": True,
                    "defaultValue": "3",
                    "description": "Controle de acesso por nível mínimo para visualização da tela de backup."
                }
            },
            {
                "key": "BACKUP_SCREEN_MIN_EDIT_LEVEL",
                "value": "4",
                "description": "Nível mínimo para editar dados na tela de backup (1=aluno, 2=colaborador, 3=bibliotecario, 4=admin).",
                "spec": {
                    "valueType": "enum",
                    "allowedValues": "1,2,3,4",
                    "required": True,
                    "defaultValue": "4",
                    "description": "Controle de acesso por nível mínimo para ações de edição/executar backup."
                }
            },
            {
                "key": "BACKUP_GOOGLE_DRIVE_FOLDER_ID",
                "value": "",
                "description": "ID da pasta do Google Drive que receberá os backups.",
                "spec": {
                    "valueType": "string",
                    "required": False,
                    "defaultValue": "",
                    "description": "Pasta de destino no Drive para upload automático de backups."
                }
            },
            {
                "key": "BACKUP_GOOGLE_DRIVE_FOLDER_NAME",
                "value": "Backups_Sistema_Biblioteca",
                "description": "Nome da pasta gerenciada automaticamente no Google Drive para armazenamento dos backups.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "Backups_Sistema_Biblioteca",
                    "description": "Se o folder_id estiver vazio ou inválido, o sistema busca/cria pasta com este nome."
                }
            },
            {
                "key": "BACKUP_GOOGLE_DRIVE_AUTO_CREATE_FOLDER",
                "value": "1",
                "description": "Habilita criação automática da pasta de backup no Google Drive quando necessário.",
                "spec": {
                    "valueType": "boolean",
                    "required": True,
                    "defaultValue": "1",
                    "description": "Quando ativo, o sistema provisiona a pasta automaticamente no connect/upload."
                }
            },
            {
                "key": "BACKUP_GOOGLE_DRIVE_FOLDER_RECOVERY_MODE",
                "value": "auto_replace_invalid",
                "description": "Comportamento quando folder_id salvo estiver inválido: auto_replace_invalid ou strict.",
                "spec": {
                    "valueType": "enum",
                    "allowedValues": "auto_replace_invalid,strict",
                    "required": True,
                    "defaultValue": "auto_replace_invalid",
                    "description": "auto_replace_invalid busca/cria nova pasta e atualiza folder_id automaticamente."
                }
            },
            {
                "key": "BACKUP_PG_DUMP_COMMAND",
                "value": "pg_dump",
                "description": "Comando executável de dump do PostgreSQL no servidor (ex.: pg_dump ou caminho completo).",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "pg_dump",
                    "description": "Permite ajustar o executável usado na geração de backup local."
                }
            },
            {
                "key": "BACKUP_DUMP_STRATEGY",
                "value": "auto",
                "description": "Estratégia de dump: auto, local_cli ou docker_exec.",
                "spec": {
                    "valueType": "enum",
                    "allowedValues": "auto,local_cli,docker_exec",
                    "required": True,
                    "defaultValue": "auto",
                    "description": "auto tenta pg_dump local e cai para docker_exec quando necessário."
                }
            },
            {
                "key": "BACKUP_DOCKER_BINARY",
                "value": "docker",
                "description": "Executável Docker usado para comandos de backup via container.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "docker",
                    "description": "Normalmente 'docker'."
                }
            },
            {
                "key": "BACKUP_DOCKER_CONTAINER_NAME",
                "value": "sistema_biblioteca_postgres",
                "description": "Nome do container PostgreSQL para executar pg_dump internamente.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "sistema_biblioteca_postgres",
                    "description": "Container do banco definido no docker-compose."
                }
            },
            {
                "key": "BACKUP_DOCKER_TEMP_DIR",
                "value": "/tmp",
                "description": "Diretório temporário dentro do container para gerar o arquivo dump.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "/tmp",
                    "description": "Pasta interna do container usada antes do docker cp."
                }
            },
            {
                "key": "BACKUP_RETRY_BASE_MINUTES",
                "value": "10",
                "description": "Intervalo base (minutos) para retentativas de upload ao Drive.",
                "spec": {
                    "valueType": "integer",
                    "minValue": 1,
                    "maxValue": 1440,
                    "required": True,
                    "defaultValue": "10",
                    "description": "Base do backoff exponencial para nova tentativa de envio."
                }
            },
            {
                "key": "BACKUP_RETRY_MAX_MINUTES",
                "value": "1440",
                "description": "Teto (minutos) para retentativas de upload ao Drive.",
                "spec": {
                    "valueType": "integer",
                    "minValue": 1,
                    "maxValue": 10080,
                    "required": True,
                    "defaultValue": "1440",
                    "description": "Intervalo máximo entre tentativas de envio pendente ao Drive."
                }
            },
            {
                "key": "BACKUP_GOOGLE_OAUTH_CLIENT_ID",
                "value": "",
                "description": "Client ID OAuth2 da aplicação Google para envio de backups ao Drive.",
                "spec": {
                    "valueType": "string",
                    "required": False,
                    "defaultValue": "",
                    "description": "Credencial OAuth2 fornecida no Google Cloud Console."
                }
            },
            {
                "key": "BACKUP_GOOGLE_OAUTH_CLIENT_SECRET",
                "value": "",
                "description": "Client Secret OAuth2 da aplicação Google para envio de backups ao Drive.",
                "spec": {
                    "valueType": "string",
                    "required": False,
                    "defaultValue": "",
                    "description": "Segredo OAuth2 fornecido no Google Cloud Console."
                }
            },
            {
                "key": "BACKUP_GOOGLE_OAUTH_REDIRECT_URI",
                "value": "",
                "description": "URL de callback OAuth2 da aplicação para retorno da autorização Google.",
                "spec": {
                    "valueType": "string",
                    "required": False,
                    "defaultValue": "",
                    "description": "Deixe em branco para usar automaticamente a rota /backups/google/callback do servidor atual."
                }
            },
            {
                "key": "BACKUP_GOOGLE_OAUTH_SCOPES",
                "value": "https://www.googleapis.com/auth/drive.file",
                "description": "Escopos OAuth2 utilizados na integração de backup com Google Drive.",
                "spec": {
                    "valueType": "string",
                    "required": True,
                    "defaultValue": "https://www.googleapis.com/auth/drive.file",
                    "description": "Escopos separados por espaço conforme padrão OAuth2."
                }
            },
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
                    allowedValues=spec_data.get('allowedValues'),
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

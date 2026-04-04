import os
import tempfile
from datetime import datetime, timedelta
from subprocess import CompletedProcess
from unittest.mock import patch

from app import db
from app.models import BackupRun, BackupSchedule, BackupUpload, Configuration, OAuthCredential, User
from app.services.backup_service import (
    _run_pg_dump_custom,
    build_google_oauth_authorize_url,
    calculate_next_run_at,
    create_local_backup_now,
    process_pending_drive_uploads_once,
)
from tests.unit.base import BaseTestCase


class BackupModuleTestCase(BaseTestCase):
    def _login_as_admin(self):
        admin = self._create_admin_user()
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(admin.userId)
            sess['_fresh'] = True
            sess['logged_in'] = True
            sess['userType'] = 'admin'
            sess['userId'] = admin.userId
        return admin

    def _set_config(self, key, value):
        existing_admin = User.query.filter_by(identificationCode='admin').first()
        owner = existing_admin or self._create_admin_user()
        entry = Configuration(
            key=key,
            value=str(value),
            description='test',
            creationDate=datetime.now(),
            lastUpdate=datetime.now(),
            createdBy=owner.userId,
            updatedBy=owner.userId,
        )
        db.session.add(entry)
        db.session.commit()

    def test_calculate_next_run_daily_and_weekly(self):
        owner = self._create_admin_user()
        now_ref = datetime(2026, 4, 3, 10, 15, 0)

        daily = BackupSchedule(
            name='Diario',
            frequency='daily',
            runTime='11:00',
            weekDays=None,
            timezone='America/Sao_Paulo',
            enabled=True,
            createdBy=owner.userId,
            updatedBy=owner.userId,
            creationDate=datetime.now(),
            lastUpdate=datetime.now(),
        )
        next_daily = calculate_next_run_at(daily, reference_dt=now_ref)
        self.assertEqual(next_daily.hour, 11)
        self.assertEqual(next_daily.minute, 0)

        weekly = BackupSchedule(
            name='Semanal',
            frequency='weekly',
            runTime='09:00',
            weekDays='4',
            timezone='America/Sao_Paulo',
            enabled=True,
            createdBy=owner.userId,
            updatedBy=owner.userId,
            creationDate=datetime.now(),
            lastUpdate=datetime.now(),
        )
        next_weekly = calculate_next_run_at(weekly, reference_dt=now_ref)
        self.assertIsNotNone(next_weekly)

    def test_backup_route_schedule_crud(self):
        self._login_as_admin()
        self._set_config('BACKUP_SCREEN_MIN_VIEW_LEVEL', 1)
        self._set_config('BACKUP_SCREEN_MIN_EDIT_LEVEL', 1)

        response = self.client.post(
            '/backups/schedules/new',
            data={
                'name': 'Agendamento Teste',
                'frequency': 'daily',
                'runTime': '08:30',
                'timezone': 'America/Sao_Paulo',
                'enabled': '1',
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        schedule = BackupSchedule.query.filter_by(name='Agendamento Teste').first()
        self.assertIsNotNone(schedule)

        response = self.client.post(
            f'/backups/schedules/{schedule.scheduleId}/update',
            data={
                'name': 'Agendamento Editado',
                'frequency': 'weekly',
                'runTime': '10:00',
                'weekDays': '1,3',
                'timezone': 'America/Sao_Paulo',
                'enabled': '1',
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        schedule = db.session.get(BackupSchedule, schedule.scheduleId)
        self.assertEqual(schedule.name, 'Agendamento Editado')
        self.assertEqual(schedule.frequency, 'weekly')

        response = self.client.post(f'/backups/schedules/{schedule.scheduleId}/toggle', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        schedule = db.session.get(BackupSchedule, schedule.scheduleId)
        self.assertFalse(schedule.enabled)

        response = self.client.post(f'/backups/schedules/{schedule.scheduleId}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(db.session.get(BackupSchedule, schedule.scheduleId))

    def test_create_local_backup_offline_first_enqueues_upload(self):
        owner = self._create_admin_user()

        with tempfile.TemporaryDirectory() as tmp_dir:
            self._set_config('BACKUP_LOCAL_DIRECTORY', tmp_dir)
            self._set_config('BACKUP_PG_DUMP_COMMAND', 'pg_dump')

            def fake_pg_dump(path):
                with open(path, 'wb') as file_obj:
                    file_obj.write(b'dummy dump data')

            with patch('app.services.backup_service._run_pg_dump_custom', side_effect=fake_pg_dump):
                run = create_local_backup_now(requested_by=owner.userId)

            stored_run = db.session.get(BackupRun, run.runId)
            self.assertEqual(stored_run.status, 'success')
            self.assertTrue(stored_run.fileName.startswith('BkpBiblioteca_'))
            self.assertTrue(os.path.isfile(stored_run.localPath))

            upload = BackupUpload.query.filter_by(runId=run.runId).first()
            self.assertIsNotNone(upload)
            self.assertEqual(upload.status, 'pending')

    def test_process_pending_uploads_with_retry(self):
        owner = self._create_admin_user()

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, 'BkpBiblioteca_03-04-2026_10-00-00.zip')
            with open(zip_path, 'wb') as file_obj:
                file_obj.write(b'zip-data')

            run = BackupRun(
                scheduleId=None,
                status='success',
                fileName=os.path.basename(zip_path),
                localPath=zip_path,
                fileHash='abc',
                fileSizeBytes=7,
                startedAt=datetime.now(),
                finishedAt=datetime.now(),
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
                createdBy=owner.userId,
                updatedBy=owner.userId,
            )
            db.session.add(run)
            db.session.commit()

            upload = BackupUpload(
                runId=run.runId,
                provider='google_drive',
                status='pending',
                retryCount=0,
                nextRetryAt=datetime.now() - timedelta(minutes=1),
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
            )
            db.session.add(upload)

            credential = OAuthCredential(
                provider='google_drive',
                accessToken='enc-token',
                refreshToken='enc-refresh',
                tokenType='Bearer',
                scope='drive.file',
                expiresAt=datetime.now() + timedelta(hours=1),
                isEncrypted=True,
                creationDate=datetime.now(),
                lastUpdate=datetime.now(),
                createdBy=owner.userId,
                updatedBy=owner.userId,
            )
            db.session.add(credential)
            db.session.commit()

            with patch('app.services.backup_service.decrypt_secret', return_value='token'):
                with patch('app.services.backup_service._upload_file_to_google_drive', return_value='drive-file-id'):
                    uploaded_count = process_pending_drive_uploads_once(limit=5)

            self.assertEqual(uploaded_count, 1)
            updated = db.session.get(BackupUpload, upload.uploadId)
            self.assertEqual(updated.status, 'uploaded')
            self.assertEqual(updated.remoteFileId, 'drive-file-id')

    def test_google_connect_redirects_to_authorize_url(self):
        self._login_as_admin()
        self._set_config('BACKUP_SCREEN_MIN_VIEW_LEVEL', 1)
        self._set_config('BACKUP_SCREEN_MIN_EDIT_LEVEL', 1)

        with patch('app.routes.backups.build_google_oauth_authorize_url', return_value='https://accounts.google.com/o/oauth2/v2/auth?x=1'):
            response = self.client.post('/backups/google/connect', follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn('accounts.google.com', response.location)

    def test_google_connect_without_client_id_redirects_back(self):
        self._login_as_admin()
        self._set_config('BACKUP_SCREEN_MIN_VIEW_LEVEL', 1)
        self._set_config('BACKUP_SCREEN_MIN_EDIT_LEVEL', 1)

        response = self.client.post('/backups/google/connect', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/backups', response.location)

    def test_authorize_url_uses_callback_when_redirect_config_is_blank(self):
        self._set_config('BACKUP_GOOGLE_OAUTH_CLIENT_ID', 'client-123')
        self._set_config('BACKUP_GOOGLE_OAUTH_REDIRECT_URI', '')

        url = build_google_oauth_authorize_url(
            state_value='state-123',
            redirect_uri='http://localhost:5000/backups/google/callback',
        )
        self.assertIn('redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fbackups%2Fgoogle%2Fcallback', url)

    def test_google_callback_exchanges_code(self):
        self._login_as_admin()
        self._set_config('BACKUP_SCREEN_MIN_VIEW_LEVEL', 1)
        self._set_config('BACKUP_SCREEN_MIN_EDIT_LEVEL', 1)

        with self.client.session_transaction() as sess:
            sess['backup_google_oauth_state'] = 'state-123'

        with patch('app.routes.backups.exchange_google_oauth_code') as mocked_exchange:
            response = self.client.get('/backups/google/callback?state=state-123&code=abc123', follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/backups', response.location)
        self.assertTrue(mocked_exchange.called)

    def test_google_callback_alias_route_exchanges_code(self):
        self._login_as_admin()
        self._set_config('BACKUP_SCREEN_MIN_VIEW_LEVEL', 1)
        self._set_config('BACKUP_SCREEN_MIN_EDIT_LEVEL', 1)

        with self.client.session_transaction() as sess:
            sess['backup_google_oauth_state'] = 'state-alias'

        with patch('app.routes.backups.exchange_google_oauth_code') as mocked_exchange:
            response = self.client.get('/callback?state=state-alias&code=code123', follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/backups', response.location)
        self.assertTrue(mocked_exchange.called)

    def test_save_google_credentials_from_backup_screen(self):
        self._login_as_admin()
        self._set_config('BACKUP_SCREEN_MIN_VIEW_LEVEL', 1)
        self._set_config('BACKUP_SCREEN_MIN_EDIT_LEVEL', 1)

        response = self.client.post(
            '/backups/google/credentials',
            data={
                'client_id': 'client-id-xyz',
                'client_secret': 'client-secret-xyz',
                'redirect_uri': 'http://localhost:5000/backups/google/callback',
                'folder_id': 'folder-123',
                'scopes': 'https://www.googleapis.com/auth/drive.file',
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/backups', response.location)

        saved_client_id = Configuration.query.filter_by(key='BACKUP_GOOGLE_OAUTH_CLIENT_ID').first()
        saved_client_secret = Configuration.query.filter_by(key='BACKUP_GOOGLE_OAUTH_CLIENT_SECRET').first()
        saved_redirect = Configuration.query.filter_by(key='BACKUP_GOOGLE_OAUTH_REDIRECT_URI').first()

        self.assertIsNotNone(saved_client_id)
        self.assertIsNotNone(saved_client_secret)
        self.assertIsNotNone(saved_redirect)
        self.assertEqual(saved_client_id.value, 'client-id-xyz')
        self.assertEqual(saved_client_secret.value, 'client-secret-xyz')

    def test_pg_dump_uses_docker_exec_strategy(self):
        self._set_config('BACKUP_DUMP_STRATEGY', 'docker_exec')
        self._set_config('BACKUP_DOCKER_BINARY', 'docker')
        self._set_config('BACKUP_DOCKER_CONTAINER_NAME', 'sistema_biblioteca_postgres')
        self._set_config('BACKUP_DOCKER_TEMP_DIR', '/tmp')

        commands = []

        def fake_run(cmd, **kwargs):
            commands.append(cmd)
            return CompletedProcess(cmd, 0, stdout='', stderr='')

        with patch('app.services.backup_service.subprocess.run', side_effect=fake_run):
            _run_pg_dump_custom('C:/tmp/test.dump')

        self.assertTrue(any(cmd[:2] == ['docker', 'exec'] for cmd in commands))
        self.assertTrue(any(cmd[:2] == ['docker', 'cp'] for cmd in commands))

    def test_pg_dump_auto_fallbacks_to_docker_when_local_missing(self):
        self._set_config('BACKUP_DUMP_STRATEGY', 'auto')
        self._set_config('BACKUP_DOCKER_BINARY', 'docker')
        self._set_config('BACKUP_DOCKER_CONTAINER_NAME', 'sistema_biblioteca_postgres')

        with patch('app.services.backup_service._run_pg_dump_custom_local', side_effect=Exception('sentinel')):
            with patch('app.services.backup_service._run_pg_dump_custom_docker') as docker_runner:
                # Não deve cair para docker em erro genérico; só quando comando local não existe.
                with self.assertRaises(Exception):
                    _run_pg_dump_custom('C:/tmp/test.dump')
                self.assertFalse(docker_runner.called)

        from app.services.backup_service import PgDumpCommandNotFoundError
        with patch('app.services.backup_service._run_pg_dump_custom_local', side_effect=PgDumpCommandNotFoundError('not found')):
            with patch('app.services.backup_service._run_pg_dump_custom_docker') as docker_runner:
                _run_pg_dump_custom('C:/tmp/test.dump')
                self.assertTrue(docker_runner.called)

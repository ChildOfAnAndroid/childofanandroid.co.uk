"""Real Flask test-client coverage, skipped explicitly when Flask is unavailable."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

FLASK_AVAILABLE = bool(importlib.util.find_spec('flask') and importlib.util.find_spec('flask_cors'))
SERVER = Path(__file__).resolve().parents[1] / 'PYTHON' / 'bbyServer.py'


@unittest.skipUnless(FLASK_AVAILABLE, 'Flask and flask-cors are required for HTTP integration tests')
class SiteHTTP(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        target = Path(self.tmp.name) / 'bbyServer.py'
        shutil.copyfile(SERVER, target)
        spec = importlib.util.spec_from_file_location('site_test_server', target)
        self.server = importlib.util.module_from_spec(spec)
        # Importing this legacy server normally starts worker threads. Tests must
        # not start those workers or contact a live BabyLLM instance.
        with patch('threading.Thread.start'), patch.dict('os.environ', {
            'LLM_SERVER_URL': '', 'GALLERY_ADMIN_TOKEN': 'unit-test-only-secret',
            'BBY_ALLOWED_ORIGINS': 'https://site.example',
        }):
            spec.loader.exec_module(self.server)
        self.server.app.config['TESTING'] = True
        self.client = self.server.app.test_client()

    def test_gallery_owner_boundary(self):
        self.server.gallery_index[:] = [{'id': 'fixture', 'title': 'before'}]
        response = self.client.post('/api/gallery/update_meta', json={'id': 'fixture', 'title': 'after'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.server.gallery_index[0]['title'], 'before')
        response = self.client.post('/api/gallery/update_meta',
            headers={'Authorization': 'Bearer unit-test-only-secret'},
            json={'id': 'fixture', 'title': 'after'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.server.gallery_index[0]['title'], 'after')

    def test_browser_origin_boundary(self):
        response = self.client.post('/api/state', headers={'Origin': 'https://other.example'}, json={'R': 12})
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_internal_state_is_not_a_public_control(self):
        response = self.client.post('/api/state', json={'speechText': 'fixture'})
        self.assertEqual(response.status_code, 400)

    def test_public_read_and_security_header(self):
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')


if __name__ == '__main__':
    unittest.main()

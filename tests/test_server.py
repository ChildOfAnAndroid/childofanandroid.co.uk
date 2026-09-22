"""Offline regressions against the real handler functions, without booting workers.

The AST loader removes Flask decorators but executes each real function body.
It avoids touching live storage/network. The optional Flask smoke test below
checks actual route registration when Flask and Flask-Cors are installed.
"""
import ast
import base64
import hashlib
import hmac
import importlib.util
import io
import json
import os
import re
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import uuid

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'PYTHON' / 'bbyServer.py'


def functions(**extra):
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    for node in nodes:
        node.decorator_list = []
    ns = dict(os=os, re=re, json=json, uuid=uuid, time=time, hmac=hmac, hashlib=hashlib,
              base64=base64, io=io, Image=Image, tempfile=tempfile,
              requests=SimpleNamespace(post=Mock(), exceptions=requests.exceptions),
              jsonify=lambda *args, **kwargs: args[0] if args else kwargs,
              state_lock=threading.Lock(), chat_lock=threading.Lock(),
              snapshot_lock=threading.RLock(), babyState={}, chat_history=[],
              snapshot_index=[], gallery_index=[], LLM_SERVER_URL='http://brain.invalid',
              CHAT_FILE='unused', MAX_UPLOAD_MB=8,
              ALLOWED_ORIGINS=('https://site.example',))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), ns)
    ns.update(extra)
    return ns


def request(body=None, *, headers=None, method='POST'):
    return SimpleNamespace(headers=headers or {}, method=method,
                           get_json=lambda **kwargs: body, json=body)


def png(colour=(0, 0, 0, 0)):
    out = io.BytesIO()
    Image.new('RGBA', (2, 3), colour).save(out, 'PNG')
    return out.getvalue()


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'BBY_ADMIN_TOKEN': 'a' * 40,
                                         'BBY_INTERNAL_TOKEN': 'i' * 40})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.ns = functions(request=request({}))

    def test_missing_or_short_secret_fails_closed(self):
        for token in ('', 'short'):
            with self.subTest(token=token), patch.dict(os.environ, {'BBY_ADMIN_TOKEN': token}):
                self.assertEqual(self.ns['_require_token']('BBY_ADMIN_TOKEN')[1], 503)

    def test_invalid_auth_never_uses_proxy_ip_or_origin(self):
        for auth in ('', 'Bearer nope', 'Bearer ' + 'i' * 40, 'Bearer ☃'):
            with self.subTest(auth=auth):
                self.ns['request'] = request(headers={'Authorization': auth,
                    'Origin': 'https://site.example', 'X-Forwarded-For': '127.0.0.1'})
                self.assertEqual(self.ns['_require_token']('BBY_ADMIN_TOKEN')[1], 401)

    def test_correct_secret_accepted(self):
        self.ns['request'] = request(headers={'Authorization': 'Bearer ' + 'a' * 40})
        self.assertIsNone(self.ns['_require_token']('BBY_ADMIN_TOKEN'))

    def test_internal_push_requires_internal_not_admin_secret(self):
        for token in ('', 'a' * 40):
            self.ns['request'] = request({'R': 10}, headers={'Authorization': 'Bearer ' + token})
            self.assertEqual(self.ns['brain_push']()[1], 401)
            self.assertEqual(self.ns['babyState'], {})
        self.ns['request'] = request({'R': 10}, headers={'Authorization': 'Bearer ' + 'i' * 40})
        self.assertEqual(self.ns['brain_push'](), {'ok': True})
        self.assertEqual(self.ns['babyState']['R'], 10)

    def test_gallery_admin_denied_before_body_is_read(self):
        self.ns['request'] = SimpleNamespace(headers={}, get_json=Mock(side_effect=AssertionError('body read')))
        self.assertEqual(self.ns['api_gallery_update_meta']()[1], 401)
        self.ns['request'].get_json.assert_not_called()

    def test_origin_filter_does_not_replace_authentication(self):
        for method, origin, denied in [('POST', 'https://other.example', True),
                                       ('POST', 'null', True),
                                       ('POST', 'https://site.example', False),
                                       ('GET', 'https://other.example', False),
                                       ('POST', '', False)]:
            with self.subTest(method=method, origin=origin):
                self.ns['request'] = request(headers={'Origin': origin}, method=method)
                result = self.ns['_check_write_origin']()
                self.assertEqual(result is not None, denied)

    def test_existing_public_controls_still_work(self):
        for body in ({'jumping': True}, {'cheeks_on': False}, {'stretch_up': True},
                     {'R': 0, 'G': 128, 'B': 255}):
            self.assertTrue(self.ns['_public_state_update'](body))

    def test_public_controls_have_strict_types(self):
        for body in ({'R': True}, {'R': 256}, {'G': -1}, {'B': 1.5}, {'jumping': 'yes'}):
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.ns['_public_state_update'](body)

    def test_arbitrary_state_change_is_not_public(self):
        self.ns['_reload_users_from_disk'] = lambda: None
        for body in ({'speechText': 'changed'}, {'R': 100, 'unrelated': 'value'}):
            self.ns['request'] = request(body)
            self.assertEqual(self.ns['api_set_state']()[1], 401)
        self.ns['requests'].post.assert_not_called()

    def test_public_state_is_forwarded_once(self):
        self.ns['_reload_users_from_disk'] = lambda: None
        self.ns['request'] = request({'jumping': True})
        self.ns['requests'].post.return_value = SimpleNamespace(text='{}', status_code=200, headers={})
        self.assertEqual(self.ns['api_set_state']()[1], 200)
        self.ns['requests'].post.assert_called_once()


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.ns = functions(_reload_users_from_disk=lambda: None,
                            _upsert_user=lambda **kw: 'web:unit-test',
                            _claim_alias_if_exists=lambda *a: None,
                            _save_json=lambda *a: None)
        self.ns['requests'].post.return_value = SimpleNamespace(ok=True, status_code=200,
                                                              json=lambda: {'reply': 'hello'})

    def test_each_speech_option_generates_only_once(self):
        for speak in (True, False, None):
            with self.subTest(speak=speak):
                self.ns['requests'].post.reset_mock()
                self.ns['request'] = request({'text': 'hello', 'author': 'tester', 'speak': speak})
                self.assertEqual(self.ns['api_say']()[1], 200)
                self.ns['requests'].post.assert_called_once()
                self.assertEqual(self.ns['requests'].post.call_args.kwargs['json']['speak'], speak is not False)

    def test_timeout_does_not_generate_again(self):
        self.ns['request'] = request({'text': 'hello', 'speak': True})
        self.ns['requests'].post.side_effect = requests.exceptions.Timeout('offline fixture')
        self.assertEqual(self.ns['api_say']()[1], 504)
        self.ns['requests'].post.assert_called_once()

    def test_offline_brain_is_not_called(self):
        self.ns['LLM_SERVER_URL'] = ''
        self.ns['request'] = request({'text': 'hello'})
        self.assertEqual(self.ns['api_say']()[1], 503)
        self.ns['requests'].post.assert_not_called()

    def test_invalid_json_or_speak_is_rejected_before_side_effects(self):
        self.ns['_upsert_user'] = Mock()
        for body in ([], None, {'text': 'hello', 'speak': 'true'}):
            self.ns['request'] = request(body)
            self.assertEqual(self.ns['api_say']()[1], 400)
        self.ns['_upsert_user'].assert_not_called()
        self.ns['requests'].post.assert_not_called()


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sid = str(uuid.uuid4())
        self.ns = functions(SNAP_DIR=self.temp.name, SNAP_IDX=str(Path(self.temp.name) / 'index.json'),
                            snapshot_index=[{'id': self.sid, 'has_png': False, 'label': 'auto-burst'}],
                            last_autosnap_id=self.sid, _save_json=lambda *a: None)
        # Compile the original base64 helper's required module without importing Flask.
        import re
        self.ns['re'] = re

    def test_transparent_result_is_an_actual_png(self):
        data = self.ns['_crop_transparent_to_square'](png())
        self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
        with Image.open(io.BytesIO(data)) as image:
            self.assertEqual(image.size, (1, 1))
            self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_opaque_image_still_crops_to_square(self):
        with Image.open(io.BytesIO(self.ns['_crop_transparent_to_square'](png((10, 20, 30, 255))))) as image:
            self.assertEqual(image.size, (3, 3))

    def test_invalid_image_is_not_saved_as_png(self):
        with self.assertRaises(ValueError):
            self.ns['_crop_transparent_to_square'](b'not an image')

    def test_snapshot_requires_a_known_id(self):
        for sid in (str(uuid.uuid4()), 'not-a-snapshot'):
            with self.subTest(sid=sid), self.assertRaises(ValueError):
                self.ns['_attach_png'](sid, png())
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_snapshot_requires_real_png(self):
        with self.assertRaises(OSError):
            self.ns['_attach_png'](self.sid, b'not a PNG')
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_snapshot_is_create_once_by_default(self):
        original = png()
        self.ns['_attach_png'](self.sid, original)
        with self.assertRaises(FileExistsError):
            self.ns['_attach_png'](self.sid, png((10, 20, 30, 255)))
        self.assertEqual((Path(self.temp.name) / f'{self.sid}.png').read_bytes(), original)

    def test_current_autosnap_can_be_completed_anonymously(self):
        self.ns['request'] = request({'composite_png_b64': base64.b64encode(png()).decode()})
        self.assertEqual(self.ns['api_snapshot_attach_png'](self.sid), {'status': 'ok'})
        self.assertEqual(self.ns['api_snapshot_attach_png'](self.sid), {'status': 'ok', 'already_attached': True})

    def test_other_snapshots_require_admin_even_when_blank(self):
        self.ns['last_autosnap_id'] = str(uuid.uuid4())
        self.ns['request'] = request({'composite_png_b64': base64.b64encode(png()).decode()})
        with patch.dict(os.environ, {'BBY_ADMIN_TOKEN': 'a' * 40}):
            self.assertEqual(self.ns['api_snapshot_attach_png'](self.sid)[1], 401)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_admin_can_replace_existing_snapshot(self):
        self.ns['_attach_png'](self.sid, png())
        replacement = png((10, 20, 30, 255))
        self.ns['request'] = request({'composite_png_b64': base64.b64encode(replacement).decode()},
                                     headers={'Authorization': 'Bearer ' + 'a' * 40})
        with patch.dict(os.environ, {'BBY_ADMIN_TOKEN': 'a' * 40}):
            self.assertEqual(self.ns['api_snapshot_attach_png'](self.sid), {'status': 'ok'})
        self.assertEqual((Path(self.temp.name) / f'{self.sid}.png').read_bytes(), replacement)


class GalleryBodyTests(unittest.TestCase):
    def test_json_upload_is_decoded_not_treated_as_image_bytes(self):
        import re
        data = png()
        ns = functions(re=re, unquote=lambda s: s, _get_base_url=lambda: 'https://site.example',
                       _add_to_gallery=Mock(return_value={'id': 'gallery-id', 'file': 'fixture.png'}))
        ns['request'] = SimpleNamespace(is_json=True, get_data=Mock(side_effect=AssertionError('raw read')),
                                       get_json=lambda **kw: {'png_b64': base64.b64encode(data).decode()}, headers={})
        self.assertTrue(ns['api_gallery_save']()['ok'])
        self.assertEqual(ns['_add_to_gallery'].call_args.args[0], data)


@unittest.skipUnless(importlib.util.find_spec('flask') and importlib.util.find_spec('flask_cors'),
                     'Flask integration requires Flask and Flask-Cors')
class FlaskIntegrationTests(unittest.TestCase):
    def test_real_routes_enforce_admin_and_keep_public_get(self):
        with tempfile.TemporaryDirectory() as storage, patch.dict(os.environ, {
            'BBY_STORAGE_DIR': storage, 'BBY_START_BACKGROUND_THREADS': '0',
            'BBY_ADMIN_TOKEN': 'a' * 40, 'BBY_INTERNAL_TOKEN': 'i' * 40,
            'LLM_SERVER_URL': '',
        }):
            spec = importlib.util.spec_from_file_location('coaa_test_server', SOURCE)
            server = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(server)
            client = server.app.test_client()
            self.assertEqual(client.get('/api/state').status_code, 200)
            self.assertEqual(client.post('/api/gallery/update_meta', json={}).status_code, 401)
            self.assertEqual(client.post('/api/brain_push', json={'R': 5}).status_code, 401)


if __name__ == '__main__':
    unittest.main()

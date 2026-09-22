"""Isolated tests of the actual server functions, without sockets or background jobs.

Extracting the function definitions lets these unit tests run without Flask.
Request/response transport is stubbed; storage and Pillow processing are real.
Optional Flask test-client coverage lives in test_site_http.py.
"""
import ast
import base64
import hmac
import io
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
import uuid

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'PYTHON' / 'bbyServer.py'


def load_functions():
    tree = ast.parse(SERVER.read_text(encoding='utf-8'))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    for node in functions:
        node.decorator_list = []
    namespace = dict(os=os, re=re, uuid=uuid, time=time, io=io, json=json,
                     base64=base64, hmac=hmac, tempfile=tempfile, Image=Image, MAX_UPLOAD_MB=8)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SERVER), 'exec'), namespace)
    return namespace


class SiteContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ns = load_functions()
        self.request = SimpleNamespace(
            headers={}, method='POST', path='/api/state',
            get_json=lambda **kwargs: {}, is_json=True,
        )
        self.payload = {}
        self.request.get_json = lambda **kwargs: self.payload
        self.ns.update(
            request=self.request,
            app=SimpleNamespace(config={'GALLERY_ADMIN_TOKEN': 'unit-test-only-secret'}),
            jsonify=lambda *args, **kwargs: args[0] if args else kwargs,
            ALLOWED_ORIGINS={'https://site.example', 'http://localhost:6969'},
            snapshot_index=[], gallery_index=[], users={},
            snapshot_lock=threading.RLock(), gallery_lock=threading.RLock(),
            activity_lock=threading.Lock(), state_lock=threading.Lock(), chat_lock=threading.Lock(),
            state_refresh_requested=threading.Event(),
            babyState={'R': 133}, LLM_SERVER_URL='http://brain.example',
            CHAT_FILE=str(Path(self.tmp.name)/'chat.json'), chat_history=[],
            SNAP_DIR=self.tmp.name, SNAP_IDX=str(Path(self.tmp.name)/'snap-index.json'),
            GALL_IDX=str(Path(self.tmp.name)/'gallery-index.json'),
            last_autosnap_id=None,
            _save_json=Mock(), _reload_users_from_disk=Mock(),
            _upsert_user=Mock(return_value='web:test'), _claim_alias_if_exists=Mock(),
        )
        self.network = SimpleNamespace(
            post=Mock(return_value=SimpleNamespace(status_code=200, ok=True,
                json=lambda: {'reply':'hello'}, text='{}', headers={'Content-Type':'application/json'})),
            get=Mock(), exceptions=requests.exceptions,
        )
        self.ns['requests'] = self.network

    def call(self, name, *args):
        return self.ns[name](*args)

    def png(self, colour=(20,30,40,255)):
        out=io.BytesIO(); Image.new('RGBA',(4,4),colour).save(out,format='PNG')
        return out.getvalue()

    def snapshot(self, *, auto=False):
        sid=str(uuid.uuid4())
        row={'id':sid,'has_png':False,'label':'auto-burst' if auto else 'manual'}
        self.ns['snapshot_index'].append(row)
        if auto: self.ns['last_autosnap_id']=sid
        return sid, row

    def test_admin_requires_a_configured_nonempty_secret(self):
        self.ns['app'].config['GALLERY_ADMIN_TOKEN']=''
        self.assertFalse(self.call('_admin_authorised'))
        self.assertEqual(self.call('_require_admin')[1],503)

    def test_admin_accepts_only_matching_bearer(self):
        for header, expected in [('',False),('Bearer wrong-test-value',False),
                ('Basic unit-test-only-secret',False),('Bearer unit-test-only-secret',True)]:
            with self.subTest(header_type=header.split(' ')[0]):
                self.request.headers={'Authorization':header}
                self.assertEqual(self.call('_admin_authorised'),expected)

    def test_gallery_rename_denied_before_any_storage_write(self):
        self.payload={'id':'test-item','title':'new'}
        self.ns['gallery_index']=[{'id':'test-item','title':'original'}]
        self.assertEqual(self.call('api_gallery_update_meta')[1],401)
        self.assertEqual(self.ns['gallery_index'][0]['title'],'original')
        self.ns['_save_json'].assert_not_called()

    def test_authorised_gallery_rename_works(self):
        self.request.headers={'Authorization':'Bearer unit-test-only-secret'}
        self.payload={'id':'test-item','title':'new'}
        self.ns['gallery_index']=[{'id':'test-item','title':'original'}]
        self.assertEqual(self.call('api_gallery_update_meta'),{'ok':True})
        self.assertEqual(self.ns['gallery_index'][0]['title'],'new')
        self.ns['_save_json'].assert_called_once()

    def test_private_user_record_needs_admin(self):
        self.assertEqual(self.call('api_get_user','web:test')[1],401)
        self.ns['_reload_users_from_disk'].assert_not_called()

    def test_disallowed_browser_write_origin_is_rejected(self):
        self.request.headers={'Origin':'https://other.example'}
        self.assertEqual(self.call('_check_write_origin')[1],403)
        self.request.headers={'Origin':'https://site.example'}
        self.assertIsNone(self.call('_check_write_origin'))
        self.request.headers={}
        self.assertIsNone(self.call('_check_write_origin'))

    def test_public_colour_and_movement_controls_remain_allowed(self):
        for data in ({'R':0,'G':255,'B':64},{'jumping':True},
                     {'cheeks_on':False,'stretch_up':True},{'eyes':5,'mouth':1}):
            with self.subTest(data=data):
                self.assertEqual(self.call('_public_state_update',data),data)

    def test_public_controls_refuse_internal_or_malformed_values(self):
        for data in ({'speechText':'not a public appearance control'}, {'R':256},
                     {'G':True},{'R':1.2},{'jumping':'true'},[],{}):
            with self.subTest(data=data):
                with self.assertRaises(ValueError): self.call('_public_state_update',data)

    def test_state_proxy_validates_before_contacting_brain(self):
        self.payload={'R':-1}
        self.assertEqual(self.call('api_set_state')[1],400)
        self.network.post.assert_not_called()
        self.payload={'R':0,'jumping':True}
        self.assertEqual(self.call('api_set_state')[1],200)
        self.network.post.assert_called_once()

    def test_brain_notification_is_only_a_coalesced_refresh_hint(self):
        self.payload={'R':5}
        for _ in range(5):
            self.assertEqual(self.call('brain_push')[1],202)
        self.assertTrue(self.ns['state_refresh_requested'].is_set())
        self.assertEqual(self.ns['babyState'],{'R':133})
        self.network.get.assert_not_called()
        self.network.post.assert_not_called()

    def test_refresh_hints_cannot_make_the_worker_poll_faster_than_once_a_second(self):
        response=SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'R':15})
        self.network.get=Mock(side_effect=[response,StopIteration()])
        clock=SimpleNamespace(monotonic=Mock(side_effect=[0,0.2,1.0]),sleep=Mock())
        event=Mock()
        self.ns.update(time=clock,STATE_SYNC_HZ=0.1,state_refresh_requested=event)
        with self.assertRaises(StopIteration): self.call('state_sync_loop')
        event.wait.assert_called_once_with(timeout=10.0)
        clock.sleep.assert_called_once_with(0.8)
        self.assertEqual(self.ns['babyState']['R'],15)

    def test_refresh_notifications_do_not_bypass_failure_backoff(self):
        self.network.get=Mock(side_effect=requests.exceptions.Timeout('unit test'))
        clock=SimpleNamespace(monotonic=lambda:0,sleep=Mock(side_effect=StopIteration()))
        event=Mock()
        self.ns.update(time=clock,STATE_SYNC_HZ=0.1,state_refresh_requested=event)
        with self.assertRaises(StopIteration): self.call('state_sync_loop')
        event.wait.assert_not_called()
        clock.sleep.assert_called_once_with(20.0)

    def test_brain_notification_reports_unconfigured_source(self):
        self.ns['LLM_SERVER_URL']=''
        self.assertEqual(self.call('brain_push')[1],503)
        self.assertFalse(self.ns['state_refresh_requested'].is_set())

    def test_speaking_web_chat_generates_exactly_once(self):
        self.payload={'text':'hello','author':'test','display_name':'Test User','speak':True}
        self.assertEqual(self.call('api_say')[1],200)
        self.network.post.assert_called_once()
        sent=self.network.post.call_args.kwargs['json']
        self.assertEqual(sent,{'text':'hello','author':'Test User','speak':True})
        self.assertEqual(len(self.ns['chat_history']),2)

    def test_non_speaking_chat_still_generates_only_once(self):
        self.payload={'text':'hello','speak':False}
        self.assertEqual(self.call('api_say')[1],200)
        self.network.post.assert_called_once()
        self.assertFalse(self.network.post.call_args.kwargs['json']['speak'])

    def test_chat_timeout_does_not_issue_an_ambiguous_retry(self):
        self.payload={'text':'hello','speak':True}
        self.network.post.side_effect=requests.exceptions.Timeout('unit test')
        self.assertEqual(self.call('api_say')[1],504)
        self.network.post.assert_called_once()

    def test_chat_rejects_invalid_input_before_network(self):
        for data in ([], {'text':7}, {'text':'hello','speak':'true'}):
            with self.subTest(data=data):
                self.payload=data
                self.assertEqual(self.call('api_say')[1],400)
        self.network.post.assert_not_called()

    def test_transparent_image_is_a_real_png(self):
        result=self.call('_crop_transparent_to_square',self.png((0,0,0,0)))
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.format,'PNG'); self.assertEqual(image.size,(1,1))
            self.assertEqual(image.getpixel((0,0)),(0,0,0,0))

    def test_png_validation_preserves_valid_image_and_refuses_invalid_data(self):
        result=self.call('_validated_png',self.png())
        with Image.open(io.BytesIO(result)) as image: self.assertEqual(image.size,(4,4))
        with self.assertRaises(ValueError): self.call('_validated_png',b'not an image')

    def test_snapshot_record_requires_canonical_existing_identity(self):
        sid,row=self.snapshot()
        self.assertIs(self.call('_snapshot_record',sid),row)
        self.assertIsNone(self.call('_snapshot_record','not-a-snapshot-id'))
        self.assertIsNone(self.call('_snapshot_record',str(uuid.uuid4())))

    def test_attachment_creation_is_one_shot(self):
        sid,row=self.snapshot()
        self.assertTrue(self.call('_attach_png',sid,self.png()))
        path=Path(self.tmp.name)/f'{sid}.png'; original=path.read_bytes()
        self.assertFalse(self.call('_attach_png',sid,self.png((200,100,50,255))))
        self.assertEqual(path.read_bytes(),original)
        self.assertTrue(row['has_png'])

    def test_current_autosnapshot_completes_without_admin(self):
        sid,row=self.snapshot(auto=True)
        self.payload={'composite_png_b64':base64.b64encode(self.png()).decode()}
        self.assertEqual(self.call('api_snapshot_attach_png',sid),
                         {'status':'ok','already_attached':False})
        self.assertTrue(row['has_png'])
        self.assertEqual(self.call('api_snapshot_attach_png',sid),
                         {'status':'ok','already_attached':True})

    def test_other_snapshot_requires_admin_and_is_not_modified(self):
        sid,row=self.snapshot()
        self.payload={'composite_png_b64':base64.b64encode(self.png()).decode()}
        self.assertEqual(self.call('api_snapshot_attach_png',sid)[1],403)
        self.assertFalse(row['has_png'])
        self.assertFalse((Path(self.tmp.name)/f'{sid}.png').exists())

    def test_gallery_json_is_decoded_instead_of_saved_as_png_bytes(self):
        self.request.is_json=True
        self.payload={'png_b64':base64.b64encode(self.png()).decode(),'label':'test'}
        self.ns['_add_to_gallery']=Mock(return_value={'id':'test','file':'test.png'})
        self.ns['_get_base_url']=lambda:'https://site.example'
        self.assertTrue(self.call('api_gallery_save')['ok'])
        self.assertEqual(self.ns['_add_to_gallery'].call_args.args[0],self.png())

    def test_gallery_binary_png_remains_supported(self):
        self.request.is_json=False; self.request.mimetype='image/png'
        self.request.get_data=lambda **kwargs:self.png()
        self.ns['unquote']=lambda value:value
        self.ns['_add_to_gallery']=Mock(return_value={'id':'test','file':'test.png'})
        self.ns['_get_base_url']=lambda:'https://site.example'
        self.assertTrue(self.call('api_gallery_save')['ok'])
        self.ns['_add_to_gallery'].assert_called_once()

    def test_security_decorators_are_registered(self):
        tree=ast.parse(SERVER.read_text())
        definitions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(ast.unparse(definitions['_check_write_origin'].decorator_list[0]),'app.before_request')
        self.assertEqual(ast.unparse(definitions['_api_response_headers'].decorator_list[0]),'app.after_request')


if __name__=='__main__': unittest.main()

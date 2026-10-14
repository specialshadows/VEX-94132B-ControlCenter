"""Public-release updater guards; installers are never executed by these tests."""
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import test_service
service=test_service.service


def installer():
    raw=bytearray(128);raw[:2]=b'MZ';struct.pack_into('<I',raw,60,80);raw[80:84]=b'PE\0\0'
    return bytes(raw)


def release(tag='control-center-v0.1.6'):
    raw=installer()
    return dict(tag_name=tag,draft=False,prerelease=False,assets=[dict(
        name=service.UPDATE_ASSET,size=len(raw),digest='sha256:'+hashlib.sha256(raw).hexdigest(),
        browser_download_url='https://github.com/'+service.UPDATE_REPO+'/releases/download/'+tag+'/'+service.UPDATE_ASSET)])


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.args=dict(_version='0.1.5',_target='windows-x64',_data=self.temp.name,
                       tag='control-center-v0.1.6',confirmed=True)
    def tearDown(self): self.temp.cleanup()
    def check(self,metadata=None,**args):
        with patch.object(service,'update_get',return_value=json.dumps(metadata or release()).encode()):
            return service.update_check(dict(self.args,**args))

    def test_newer_equal_and_older_versions(self):
        self.assertTrue(self.check()['available'])
        self.assertFalse(self.check(release('control-center-v0.1.5'))['available'])
        self.assertFalse(self.check(release('control-center-v0.1.3'))['available'])
        self.assertTrue(self.check(release('control-center-v0.1.10'))['available'])

    def test_mac_does_not_offer_windows_installation(self):
        info=self.check(_target='macos')
        self.assertFalse(info['supported']);self.assertNotIn('url',info)

    def test_wrong_origin_missing_digest_and_ambiguous_assets_are_rejected(self):
        for mutation in ('url','hash','duplicate','prerelease','traversal'):
            data=release()
            if mutation=='url': data['assets'][0]['browser_download_url']='https://attacker.example/setup.exe'
            if mutation=='hash': data['assets'][0]['digest']=None
            if mutation=='duplicate': data['assets']*=2
            if mutation=='prerelease': data['prerelease']=True
            if mutation=='traversal': data['tag_name']='../../elsewhere'
            with self.subTest(mutation=mutation),self.assertRaises(service.Failure): self.check(data)

    def test_redirects_cannot_leave_https_github_hosts(self):
        for url in ('http://github.com/file','https://github.com.attacker.test/file',
                    'https://attacker.test/file','https://name:secret@github.com/file','file:///tmp/setup.exe'):
            self.assertFalse(service.update_url_allowed(url))
            with self.assertRaises(service.Failure):
                service.UpdateRedirect().redirect_request(None,None,302,'',{},url)
        self.assertTrue(service.update_url_allowed('https://release-assets.githubusercontent.com/file'))

    def test_download_is_confirmed_checked_and_cached(self):
        info=self.check()
        with patch.object(service,'update_check',return_value=info),patch.object(service,'update_get',return_value=installer()) as get:
            result=service.update_download(self.args)
            self.assertTrue(result['downloaded']);self.assertFalse(result['cached'])
            self.assertTrue(service.update_download(self.args)['cached']);get.assert_called_once()
            with self.assertRaises(service.Failure): service.update_download(dict(self.args,confirmed=False))

    def test_bad_installer_never_reaches_installable_cache(self):
        info=self.check()
        with patch.object(service,'update_check',return_value=info),patch.object(service,'update_get',return_value=b'bad'):
            with self.assertRaises(service.Failure): service.update_download(self.args)
        self.assertFalse((Path(self.temp.name)/'updates'/self.args['tag']/service.UPDATE_ASSET).exists())
        bad=dict(info,sha256=hashlib.sha256(b'X'*128).hexdigest())
        self.assertFalse(service.update_installer_valid(b'X'*128,bad))

    def test_release_changes_need_a_fresh_review(self):
        with patch.object(service,'update_check',return_value=self.check()):
            with self.assertRaises(service.Failure): service.update_download(dict(self.args,tag='control-center-v0.1.4'))

    def test_symlinked_cache_is_not_written(self):
        folder=Path(self.temp.name)/'updates'
        try: folder.symlink_to(Path(self.temp.name),target_is_directory=True)
        except OSError: self.skipTest('This Windows account cannot create symbolic links')
        with self.assertRaises(service.Failure): service.update_destination(self.args,self.check())

    def test_install_rechecks_checksum_and_never_uses_shell_or_silent_flags(self):
        class WindowsOS: name='nt'
        info=self.check();target=service.update_destination(self.args,info);target.write_bytes(installer())
        with patch.object(service,'update_check',return_value=info),patch.object(service,'os',WindowsOS),\
             patch.object(service.subprocess,'Popen') as start:
            result=service.update_install(self.args)
            self.assertTrue(result['launched'])
            self.assertEqual(start.call_args.args[0],[str(target)])
            self.assertNotIn('shell',start.call_args.kwargs)
            target.write_bytes(b'tampered')
            with self.assertRaises(service.Failure): service.update_install(self.args)
            start.assert_called_once()


if __name__=='__main__': unittest.main()

import json
import threading
import urllib.error
import urllib.request
from claude_session.relay import Server
from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_http_requires_token_and_preserves_unicode(self):
            server = Server(('127.0.0.1', 0), self.state, 'test-token')
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f'http://127.0.0.1:{server.server_port}/client'
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                body = json.dumps(self.send(text='Unicode ✓')).encode()
                with self.assertRaises(urllib.error.HTTPError):
                    opener.open(urllib.request.Request(url, data=body), timeout=2)
                request = urllib.request.Request(url, data=body, headers={'Authorization': 'Bearer test-token'})
                with opener.open(request, timeout=2) as response:
                    self.assertTrue(json.loads(response.read())['ok'])
                self.assertEqual(self.state.tick(self.tick)['commands'][0]['text'], 'Unicode ✓')
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

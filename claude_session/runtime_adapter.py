"""Integration boundary for local orchestrators, separate from generated tool arguments."""
import json
import urllib.error
import urllib.parse
import urllib.request

from .identity import UNSUPPORTED


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def detect_runtime(base_url, get_json=None):
    """Probe an explicitly connected server, never scan ports or infer from a model name."""
    parsed = urllib.parse.urlsplit(base_url)
    if (parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'', '/', '/v1', '/v1/'}):
        raise ValueError('A server base URL without credentials or query parameters is required')
    origin = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, '', '', ''))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def read(path):
        if get_json is not None:
            return get_json(path)
        try:
            with opener.open(origin + path, timeout=3) as response:
                raw = response.read(1048577)
                if len(raw) > 1048576:
                    return {}
                return json.loads(raw)
        except (OSError, ValueError, urllib.error.HTTPError):
            return {}

    matches = []
    ollama_version, tags = read('/api/version'), read('/api/tags')
    if (isinstance(ollama_version, dict) and isinstance(ollama_version.get('version'), str)
            and isinstance(tags, dict) and isinstance(tags.get('models'), list)):
        matches.append('ollama')
    props = read('/props')
    if (isinstance(props, dict) and isinstance(props.get('default_generation_settings'), dict)
            and 'total_slots' in props and 'chat_template' in props):
        matches.append('llama.cpp')
    version, models = read('/version'), read('/v1/models')
    if (isinstance(version, dict) and isinstance(version.get('version'), str)
            and isinstance(models, dict) and isinstance(models.get('data'), list)
            and any(isinstance(m, dict) and m.get('owned_by') == 'vllm' for m in models['data'])):
        matches.append('vllm')
    if len(matches) != 1:
        raise ValueError(UNSUPPORTED + ' Runtime metadata is missing or ambiguous.')
    return {'kind': matches[0], 'method': 'runtime_adapter'}


class RuntimeConnection:
    """The local agent application owns this connection; the model cannot choose its sender."""
    def __init__(self, base_url, transport=None, get_json=None):
        self.source = detect_runtime(base_url, get_json)
        if transport is None:
            from .host import request
            transport = request
        self.transport = transport

    def request(self, body):
        if 'source' in body or 'prefix' in body or 'sender' in body:
            raise ValueError('Sender arguments are not exposed to models')
        return self.transport(body, source=self.source)

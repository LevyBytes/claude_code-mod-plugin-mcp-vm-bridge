"""Extract the container identity and grants used by setup and every host request."""


def inspect_binding(raw):
    if not raw['State']['Running'] or raw['Config'].get('User') not in ('1000', '1000:1000'):
        raise RuntimeError('The bound unprivileged container is unavailable')
    host = raw['HostConfig']
    if host.get('Privileged') or host.get('PidMode') == 'host':
        raise RuntimeError('Unsafe container configuration')
    mounts = [{k: m.get(k) for k in ('Type', 'Source', 'Destination', 'RW')} for m in raw['Mounts']]
    if any('podman.sock' in str(m) or 'docker.sock' in str(m) for m in mounts):
        raise RuntimeError('Management socket is exposed')
    return {'id': raw['Id'], 'image': raw['Image'], 'user': raw['Config']['User'], 'mounts': mounts,
            'privileged': False, 'security_opt': host.get('SecurityOpt'), 'cap_drop': host.get('CapDrop'),
            'memory': host.get('Memory'), 'pids_limit': host.get('PidsLimit')}

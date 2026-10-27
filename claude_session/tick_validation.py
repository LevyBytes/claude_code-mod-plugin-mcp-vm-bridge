"""Validate observation batches before changing registration or consuming commands."""
import hashlib
import json
try:
    from .protocol import fields, identifier
except ImportError:
    from protocol import fields, identifier


def validate(data):
    fields(data, ('session_id', 'instance_id', 'snapshot', 'events', 'acks'), ('batch',))
    identifier(data['session_id'])
    identifier(data['instance_id'])
    if 'batch' in data and (type(data['batch']) is not int or not 1 <= data['batch'] <= 9007199254740991):
        raise ValueError('Invalid observation batch number')
    if not isinstance(data['snapshot'], dict) or len(json.dumps(data['snapshot'], ensure_ascii=False)) > 24000:
        raise ValueError('Invalid snapshot')
    if not isinstance(data['events'], list) or len(data['events']) > 64:
        raise ValueError('Invalid event batch')
    if not isinstance(data['acks'], list) or len(data['acks']) > 16:
        raise ValueError('Invalid acknowledgement batch')
    for event in data['events']:
        if not isinstance(event, dict) or len(json.dumps(event, ensure_ascii=False)) > 12000:
            raise ValueError('Invalid event')
    for ack in data['acks']:
        fields(ack, ('request_id', 'state'), ('detail', 'result'))
        identifier(ack['request_id'])
        if len(json.dumps(ack, ensure_ascii=False).encode()) > 100000:
            raise ValueError('Acknowledgement exceeds result limit')
        if ack['state'] not in {'started', 'dropped', 'rejected', 'interrupt_requested', 'unknown', 'completed'}:
            raise ValueError('Invalid acknowledgement state')


def replay(session, data):
    if 'batch' not in data:
        if session['batch'] is not None:
            raise ValueError('Numbered observations cannot downgrade to legacy delivery')
        return None, None
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    old = session['batch']
    if old and data['batch'] <= old['number']:
        if data['batch'] != old['number'] or digest != old['digest']:
            raise ValueError('Stale or changed observation batch')
        return old['reply'], digest
    return None, digest

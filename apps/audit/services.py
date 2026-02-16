from .models import AuditEvent


def log_event(actor, action, entity=None, payload=None):
    entity_type = entity.__class__.__name__ if entity is not None else 'System'
    entity_id = str(entity.pk) if entity is not None else '-'
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload_json=payload or {},
    )

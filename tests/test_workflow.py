from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.content.models import DraftPost, DraftStatus, Topic
from apps.social.models import Platform, SocialAccount, SocialPost
from apps.social.services import build_social_post_idempotency_key
from apps.social.tasks import publish_scheduled_social_posts, recover_stuck_social_posts
from apps.users.models import ServiceToken, User, UserRole


@pytest.mark.django_db
def test_ai_agent_transition_rule():
    ai = User.objects.create(email='ai@example.com', role=UserRole.AI_AGENT)
    owner = User.objects.create(email='owner@example.com', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=owner)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=ai, updated_by=ai)

    draft.transition_status(DraftStatus.WAITING_APPROVAL, ai)
    with pytest.raises(ValidationError):
        draft.transition_status(DraftStatus.APPROVED, ai)


@pytest.mark.django_db
def test_schedule_creates_social_posts_with_idempotency():
    user = User.objects.create_user(email='owner@example.com', password='pass', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=user)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=user, updated_by=user, status=DraftStatus.APPROVED)
    account = SocialAccount(owner=user, platform=Platform.TELEGRAM, display_name='tg')
    account.set_credentials({'bot_token': 'x', 'chat_id': '@test'})
    account.save()

    client = APIClient()
    client.force_authenticate(user=user)
    payload = {
        'scheduled_at': timezone.now().isoformat(),
        'targets': [{'platform': Platform.TELEGRAM, 'social_account_id': str(account.id)}],
    }
    resp = client.post(f'/api/draft-posts/{draft.id}/schedule/', payload, format='json')
    assert resp.status_code == 201
    assert SocialPost.objects.count() == 1

    resp2 = client.post(f'/api/draft-posts/{draft.id}/schedule/', payload, format='json')
    assert resp2.status_code == 201
    assert SocialPost.objects.count() == 1


@pytest.mark.django_db
def test_schedule_rejects_invalid_target_payload():
    user = User.objects.create_user(email='owner@example.com', password='pass', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=user)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=user, updated_by=user, status=DraftStatus.APPROVED)

    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.post(f'/api/draft-posts/{draft.id}/schedule/', {
        'scheduled_at': timezone.now().isoformat(),
        'targets': [{'platform': Platform.TELEGRAM}],
    }, format='json')
    assert resp.status_code == 400


@pytest.mark.django_db
def test_publish_task_calls_connector():
    user = User.objects.create(email='owner@example.com', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=user)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=user, updated_by=user)
    account = SocialAccount(owner=user, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()
    sp = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.SCHEDULED,
        scheduled_at=timezone.now() - timezone.timedelta(minutes=1),
    )

    with patch('apps.social.connectors.vk.requests.post') as post, patch('apps.social.tasks.send_telegram_notification.delay'), patch('apps.social.tasks.social_post_lock') as lock:
        post.return_value.json.return_value = {'response': {'post_id': 12}}
        lock.return_value.__enter__.return_value = True
        publish_scheduled_social_posts()

    sp.refresh_from_db()
    assert sp.status == SocialPost.Status.PUBLISHED


@pytest.mark.django_db
def test_publish_task_skips_post_on_publish_version_mismatch():
    user = User.objects.create(email='owner@example.com', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=user)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=user, updated_by=user)
    account = SocialAccount(owner=user, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()
    sp = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.SCHEDULED,
        scheduled_at=timezone.now() - timezone.timedelta(minutes=1),
    )

    with patch('apps.social.connectors.vk.requests.post') as post, patch('apps.social.tasks.send_telegram_notification.delay'), patch('apps.social.tasks.social_post_lock') as lock:
        def _lock_enter():
            SocialPost.objects.filter(id=sp.id).update(publish_version=999)
            return True

        lock.return_value.__enter__.side_effect = _lock_enter
        publish_scheduled_social_posts()

    post.assert_not_called()
    sp.refresh_from_db()
    assert sp.status == SocialPost.Status.PENDING
    assert sp.publish_version == 999
    assert sp.publishing_token is None
    assert sp.publishing_started_at is None


@pytest.mark.django_db
def test_recover_stuck_social_posts():
    user = User.objects.create(email='owner@example.com', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=user)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=user, updated_by=user)
    account = SocialAccount(owner=user, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()
    old_time = timezone.now() - timezone.timedelta(minutes=30)
    sp = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, old_time),
        status=SocialPost.Status.PUBLISHING,
        scheduled_at=old_time,
        attempts=1,
    )
    SocialPost.objects.filter(id=sp.id).update(updated_at=old_time)

    recovered = recover_stuck_social_posts()
    sp.refresh_from_db()
    assert recovered >= 1
    assert sp.status == SocialPost.Status.PENDING
    assert sp.attempts == 2


@pytest.mark.django_db
def test_social_metrics_summary_endpoint():
    user = User.objects.create_user(email='owner@example.com', password='pass', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=user)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=user, updated_by=user)
    account = SocialAccount(owner=user, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()
    SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.FAILED,
        scheduled_at=timezone.now(),
    )

    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get('/api/social-posts/metrics/summary/')
    assert resp.status_code == 200
    assert 'by_status' in resp.data


@pytest.mark.django_db
def test_service_token_auth_for_draft_read():
    ai_user = User.objects.create(email='ai@example.com', role=UserRole.AI_AGENT)
    token_raw, token_hash = ServiceToken.generate_token()
    ServiceToken.objects.create(name='ai', service_user=ai_user, token_hash=token_hash, scopes=['ai:read_drafts'])
    owner = User.objects.create(email='owner@example.com', role=UserRole.OWNER)
    topic = Topic.objects.create(title='X', created_by=owner)
    DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=owner, updated_by=owner)
    client = APIClient()
    response = client.get('/api/draft-posts/', HTTP_X_SERVICE_TOKEN=token_raw)
    assert response.status_code == 200


@pytest.mark.django_db
def test_ai_cannot_patch_status_field():
    ai_user = User.objects.create(email='ai@example.com', role=UserRole.AI_AGENT)
    owner = User.objects.create(email='owner@example.com', role=UserRole.OWNER)
    topic = Topic.objects.create(title='X', created_by=owner)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=owner, updated_by=owner)
    token_raw, token_hash = ServiceToken.generate_token()
    ServiceToken.objects.create(name='ai', service_user=ai_user, token_hash=token_hash, scopes=['ai:write_drafts'])

    client = APIClient()
    response = client.patch(
        f'/api/draft-posts/{draft.id}/',
        {'status': DraftStatus.APPROVED, 'content': '<p>edited</p>'},
        format='json',
        HTTP_X_SERVICE_TOKEN=token_raw,
    )
    assert response.status_code == 200
    draft.refresh_from_db()
    assert draft.status == DraftStatus.DRAFT


@pytest.mark.django_db
def test_stale_inflight_marker_fails_to_avoid_duplicate_publish():
    user = User.objects.create(email='owner@example.com', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=user)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=user, updated_by=user)
    account = SocialAccount(owner=user, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()
    sp = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.PENDING,
        publishing_token='11111111-1111-1111-1111-111111111111',
        publishing_started_at=timezone.now() - timezone.timedelta(minutes=30),
        scheduled_at=timezone.now() - timezone.timedelta(minutes=1),
    )

    with patch('apps.social.connectors.vk.requests.post') as post:
        publish_scheduled_social_posts()

    post.assert_not_called()
    sp.refresh_from_db()
    assert sp.status == SocialPost.Status.FAILED

@pytest.mark.django_db
def test_metrics_summary_for_non_owner_forbidden():
    owner = User.objects.create_user(email='owner@example.com', password='pass', role=UserRole.OWNER)
    editor = User.objects.create_user(email='editor@example.com', password='pass', role=UserRole.EDITOR)
    topic = Topic.objects.create(title='Тест', created_by=owner)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=owner, updated_by=owner)
    account = SocialAccount(owner=owner, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()
    SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.FAILED,
        scheduled_at=timezone.now(),
    )

    client = APIClient()
    client.force_authenticate(user=editor)
    resp = client.get('/api/social-posts/metrics/summary/')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_social_posts_list_is_tenant_scoped():
    owner1 = User.objects.create_user(email='owner1@example.com', password='pass', role=UserRole.OWNER)
    owner2 = User.objects.create_user(email='owner2@example.com', password='pass', role=UserRole.OWNER)
    topic1 = Topic.objects.create(title='T1', created_by=owner1)
    topic2 = Topic.objects.create(title='T2', created_by=owner2)
    draft1 = DraftPost.objects.create(topic=topic1, content='<p>x</p>', created_by=owner1, updated_by=owner1)
    draft2 = DraftPost.objects.create(topic=topic2, content='<p>y</p>', created_by=owner2, updated_by=owner2)
    account1 = SocialAccount(owner=owner1, platform=Platform.VK, display_name='vk1')
    account1.set_credentials({'group_id': '1', 'access_token': 'token'})
    account1.save()
    account2 = SocialAccount(owner=owner2, platform=Platform.VK, display_name='vk2')
    account2.set_credentials({'group_id': '2', 'access_token': 'token'})
    account2.save()
    SocialPost.objects.create(
        draft_post=draft1, platform=Platform.VK, social_account=account1,
        idempotency_key=build_social_post_idempotency_key(draft1.id, account1.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.SCHEDULED, scheduled_at=timezone.now(),
    )
    SocialPost.objects.create(
        draft_post=draft2, platform=Platform.VK, social_account=account2,
        idempotency_key=build_social_post_idempotency_key(draft2.id, account2.id, Platform.VK, timezone.now()+timezone.timedelta(seconds=1)),
        status=SocialPost.Status.SCHEDULED, scheduled_at=timezone.now(),
    )

    client = APIClient()
    client.force_authenticate(user=owner1)
    resp = client.get('/api/social-posts/')
    assert resp.status_code == 200
    assert len(resp.data) == 1


@pytest.mark.django_db
def test_transient_error_resets_inflight_marker_and_keeps_pending():
    user = User.objects.create(email='owner@example.com', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=user)
    draft = DraftPost.objects.create(topic=topic, content='<p>x</p>', created_by=user, updated_by=user)
    account = SocialAccount(owner=user, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()
    sp = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.PENDING,
        scheduled_at=timezone.now() - timezone.timedelta(minutes=1),
    )

    with patch('apps.social.connectors.vk.requests.post') as post, patch('apps.social.tasks.social_post_lock') as lock:
        post.return_value.json.return_value = {'error': {'error_msg': 'Too many requests 429'}}
        lock.return_value.__enter__.return_value = True
        publish_scheduled_social_posts()

    sp.refresh_from_db()
    assert sp.status == SocialPost.Status.PENDING
    assert sp.publishing_token is None
    assert sp.publishing_started_at is None


@pytest.mark.django_db
def test_review_endpoint_updates_status_and_comment():
    owner = User.objects.create_user(email='owner@example.com', password='pass', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест', created_by=owner)
    draft = DraftPost.objects.create(topic=topic, content='<p>Контент</p>', created_by=owner, updated_by=owner)
    account = SocialAccount(owner=owner, platform=Platform.TELEGRAM, display_name='tg')
    account.set_credentials({'bot_token': 'x', 'chat_id': '@test'})
    account.save()
    post = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.TELEGRAM,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.TELEGRAM, timezone.now()),
        status=SocialPost.Status.READY_FOR_APPROVAL,
        scheduled_at=timezone.now(),
    )

    client = APIClient()
    client.force_authenticate(user=owner)
    resp = client.post(
        f'/api/social-posts/{post.id}/review/',
        {'status': SocialPost.Status.NEEDS_REVISION, 'comment': 'Добавьте CTA'},
        format='json',
    )

    assert resp.status_code == 200
    post.refresh_from_db()
    assert post.status == SocialPost.Status.NEEDS_REVISION
    assert post.review_comment == 'Добавьте CTA'


@pytest.mark.django_db
def test_review_endpoint_rejects_invalid_state_machine_transitions():
    owner = User.objects.create_user(email='owner2@example.com', password='pass', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест 2', created_by=owner)
    draft = DraftPost.objects.create(topic=topic, content='<p>Контент</p>', created_by=owner, updated_by=owner)
    account = SocialAccount(owner=owner, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()

    published_post = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.PUBLISHED,
        scheduled_at=timezone.now(),
    )
    failed_post = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now() + timezone.timedelta(seconds=1)),
        status=SocialPost.Status.FAILED,
        scheduled_at=timezone.now(),
    )

    client = APIClient()
    client.force_authenticate(user=owner)

    resp1 = client.post(
        f'/api/social-posts/{published_post.id}/review/',
        {'status': SocialPost.Status.REJECTED, 'comment': 'Поздно'},
        format='json',
    )
    assert resp1.status_code == 400
    assert 'Недопустимый переход статуса' in str(resp1.data)

    resp2 = client.post(
        f'/api/social-posts/{failed_post.id}/review/',
        {'status': SocialPost.Status.APPROVED, 'comment': ''},
        format='json',
    )
    assert resp2.status_code == 400
    assert 'Review доступен только из статуса ready_for_approval' in str(resp2.data)


@pytest.mark.django_db
def test_review_endpoint_is_only_allowed_from_ready_for_approval():
    owner = User.objects.create_user(email='owner3@example.com', password='pass', role=UserRole.OWNER)
    topic = Topic.objects.create(title='Тест 3', created_by=owner)
    draft = DraftPost.objects.create(topic=topic, content='<p>Контент</p>', created_by=owner, updated_by=owner)
    account = SocialAccount(owner=owner, platform=Platform.VK, display_name='vk')
    account.set_credentials({'group_id': '1', 'access_token': 'token'})
    account.save()
    post = SocialPost.objects.create(
        draft_post=draft,
        platform=Platform.VK,
        social_account=account,
        idempotency_key=build_social_post_idempotency_key(draft.id, account.id, Platform.VK, timezone.now()),
        status=SocialPost.Status.NEEDS_REVISION,
        scheduled_at=timezone.now(),
    )

    client = APIClient()
    client.force_authenticate(user=owner)
    resp = client.post(
        f'/api/social-posts/{post.id}/review/',
        {'status': SocialPost.Status.APPROVED, 'comment': ''},
        format='json',
    )

    assert resp.status_code == 400
    assert 'Review доступен только из статуса ready_for_approval' in str(resp.data)

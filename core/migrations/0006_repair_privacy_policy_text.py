from django.db import migrations


DEFAULT_POLICY_TEXT = (
    'CarShowroom обрабатывает персональные данные только для регистрации пользователей, '
    'оформления заказов, обратной связи и безопасной работы сайта. Обработка выполняется '
    'в соответствии с применимым законодательством Республики Беларусь.'
)


def repair_privacy_policy(apps, schema_editor):
    PrivacyPolicy = apps.get_model('core', 'PrivacyPolicy')
    policy = PrivacyPolicy.objects.order_by('-updated_at').first()

    if policy is None:
        PrivacyPolicy.objects.create(
            title='Политика конфиденциальности',
            text=DEFAULT_POLICY_TEXT,
        )
    elif not policy.text.strip() or '\ufffd' in policy.text:
        policy.title = 'Политика конфиденциальности'
        policy.text = DEFAULT_POLICY_TEXT
        policy.save(update_fields=['title', 'text', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_seed_company_history'),
    ]

    operations = [
        migrations.RunPython(repair_privacy_policy, migrations.RunPython.noop),
    ]

from django.db import migrations


def seed_company_history(apps, schema_editor):
    CompanyInfo = apps.get_model('core', 'CompanyInfo')
    CompanyHistoryEvent = apps.get_model('core', 'CompanyHistoryEvent')

    company = CompanyInfo.objects.order_by('-updated_at').first()
    if company is None:
        company = CompanyInfo.objects.create(
            title='CarShowroom',
            text='Автосалон помогает клиентам выбирать, проверять и приобретать автомобили.',
        )

    events = (
        (2022, 'Открыт первый демонстрационный зал CarShowroom в Минске.'),
        (2023, 'Запущена услуга предварительной записи на тест-драйв.'),
        (2024, 'Каталог автомобилей и оформление заявок стали доступны онлайн.'),
        (2025, 'Компания расширила партнерскую сеть и программу обслуживания клиентов.'),
    )
    for year, description in events:
        CompanyHistoryEvent.objects.get_or_create(
            company=company,
            year=year,
            defaults={'description': description},
        )


def remove_seeded_history(apps, schema_editor):
    CompanyHistoryEvent = apps.get_model('core', 'CompanyHistoryEvent')
    CompanyHistoryEvent.objects.filter(year__in=[2022, 2023, 2024, 2025]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_companyinfo_certificate_companyinfo_logo_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_company_history, remove_seeded_history),
    ]

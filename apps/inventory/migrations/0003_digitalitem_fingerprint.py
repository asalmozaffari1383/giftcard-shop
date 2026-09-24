import hashlib
import hmac

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.db import migrations, models


def populate_fingerprints(apps, schema_editor):
    DigitalItem = apps.get_model("inventory", "DigitalItem")
    cipher = MultiFernet([Fernet(key.encode()) for key in settings.INVENTORY_FERNET_KEYS])
    seen = set()
    for item in DigitalItem.objects.all().iterator(chunk_size=500):
        plaintext = cipher.decrypt(bytes(item.encrypted_payload)).decode("utf-8")
        fingerprint = hmac.new(settings.INVENTORY_FINGERPRINT_KEY.encode(), plaintext.encode("utf-8"),
                               hashlib.sha256).hexdigest()
        if fingerprint in seen:
            raise RuntimeError("Duplicate digital inventory secrets must be removed before migration")
        seen.add(fingerprint)
        item.fingerprint = fingerprint
        item.save(update_fields=["fingerprint"])


class Migration(migrations.Migration):
    dependencies = [("inventory", "0002_initial")]

    operations = [
        migrations.AddField(
            model_name="digitalitem",
            name="fingerprint",
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.RunPython(populate_fingerprints, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="digitalitem",
            name="fingerprint",
            field=models.CharField(editable=False, max_length=64, unique=True),
        ),
    ]

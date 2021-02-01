# Generated by Django 3.0.8 on 2020-11-04 12:25

import json
from pathlib import Path

from django.db import migrations, models
import django.db.models.deletion

from config import CONFIG
from index.json import to_json

try:
    JSONField = models.JSONField
except AttributeError:
    import jsonfield
    JSONField = jsonfield.JSONField


def forwards_func(apps, schema_editor):
    from core.models import EXTRACTORS

    Snapshot = apps.get_model("core", "Snapshot")
    ArchiveResult = apps.get_model("core", "ArchiveResult")

    snapshots = Snapshot.objects.all()
    for snapshot in snapshots:
        out_dir = Path(CONFIG['ARCHIVE_DIR']) / snapshot.timestamp

        try:
            with open(out_dir / "index.json", "r") as f:
                fs_index = json.load(f)
        except Exception as e:
            continue

        history = fs_index["history"]

        for extractor in history:
            for result in history[extractor]:
                ArchiveResult.objects.create(extractor=extractor, snapshot=snapshot, cmd=result["cmd"], cmd_version=result["cmd_version"] or 'unknown', 
                start_ts=result["start_ts"], end_ts=result["end_ts"], status=result["status"], pwd=result["pwd"], output=result["output"])


def verify_json_index_integrity(snapshot):
    results = snapshot.archiveresult_set.all()
    out_dir = Path(CONFIG['ARCHIVE_DIR']) / snapshot.timestamp
    with open(out_dir / "index.json", "r") as f:
        index = json.load(f)

    history = index["history"]
    index_results = [result for extractor in history for result in history[extractor]]
    flattened_results = [result["start_ts"] for result in index_results]
    
    missing_results = [result for result in results if result.start_ts.isoformat() not in flattened_results]

    for missing in missing_results:
        index["history"][missing.extractor].append({"cmd": missing.cmd, "cmd_version": missing.cmd_version, "end_ts": missing.end_ts.isoformat(),
                                                    "start_ts": missing.start_ts.isoformat(), "pwd": missing.pwd, "output": missing.output,
                                                    "schema": "ArchiveResult", "status": missing.status})

    json_index = to_json(index)
    with open(out_dir / "index.json", "w") as f:
        f.write(json_index)


def reverse_func(apps, schema_editor):
    Snapshot = apps.get_model("core", "Snapshot")
    ArchiveResult = apps.get_model("core", "ArchiveResult")
    for snapshot in Snapshot.objects.all():
        verify_json_index_integrity(snapshot)

    ArchiveResult.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20201012_1520'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchiveResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cmd', JSONField()),
                ('pwd', models.CharField(max_length=256)),
                ('cmd_version', models.CharField(max_length=32)),
                ('status', models.CharField(choices=[('succeeded', 'succeeded'), ('failed', 'failed'), ('skipped', 'skipped')], max_length=16)),
                ('output', models.CharField(max_length=512)),
                ('start_ts', models.DateTimeField()),
                ('end_ts', models.DateTimeField()),
                ('extractor', models.CharField(choices=[('title', 'title'), ('favicon', 'favicon'), ('wget', 'wget'), ('singlefile', 'singlefile'), ('pdf', 'pdf'), ('screenshot', 'screenshot'), ('dom', 'dom'), ('readability', 'readability'), ('mercury', 'mercury'), ('git', 'git'), ('media', 'media'), ('headers', 'headers'), ('archive_org', 'archive_org')], max_length=32)),
                ('snapshot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Snapshot')),
            ],
        ),
        migrations.RunPython(forwards_func, reverse_func),
    ]

# Generated manually to align Lecture model with playlist requirements.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0006_enrollment"),
    ]

    operations = [
        migrations.RenameField(
            model_name="lecture",
            old_name="video_file",
            new_name="video",
        ),
        migrations.AddField(
            model_name="lecture",
            name="description",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="lecture",
            name="title",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="lecture",
            name="order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="lecture",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.RemoveField(
            model_name="lecture",
            name="duration",
        ),
        migrations.RemoveField(
            model_name="lecture",
            name="is_preview",
        ),
        migrations.AlterUniqueTogether(
            name="lecture",
            unique_together=set(),
        ),
    ]

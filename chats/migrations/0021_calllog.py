# Generated by Django 4.1.4 on 2023-05-05 10:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chats', '0020_alter_conversation_archivedby_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='calls', to='chats.conversation')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_calls', to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='calls', to='chats.groupchat')),
                ('participants', models.ManyToManyField(blank=True, related_name='logs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
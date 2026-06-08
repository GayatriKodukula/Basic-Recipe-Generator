from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='recipehistory',
            name='difficulty_level',
            field=models.CharField(max_length=20, default='easy'),
        ),
        migrations.AddField(
            model_name='recipehistory',
            name='is_veg',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='UserRecipeInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe_title', models.CharField(max_length=200)),
                ('ingredients', models.TextField()),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-saved_at'],
            },
        ),
    ]

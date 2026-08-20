# 수동 작성: unmanaged 모델의 필드 변경은 makemigrations가 감지하지 않으므로
# (Django autodetector는 managed=False 모델의 필드 diff를 무시),
# 모델의 db_column="bond_id" 정의를 마이그레이션 상태에 반영한다.
# 이 상태가 없으면 portfolios 등 외부 앱의 FK가 존재하지 않는 bond("id")를 참조한다.
# managed=False이므로 실제 SQL은 실행되지 않는다(상태 전용).

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bonds", "0004_alter_bond_options_alter_bondcashflowrule_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bond",
            name="id",
            field=models.BigIntegerField(db_column="bond_id", primary_key=True, serialize=False),
        ),
    ]

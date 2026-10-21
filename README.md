# Brechó da Raia

Aplicação CRUD em Django para compra e venda de material de natação usado
(trajes, óculos, pés de pato e palmares). Cada anúncio é um `Post`, os
compradores deixam perguntas e propostas como `Comment` e os anúncios são
organizados por `Category`.

## Rodando localmente

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (no Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py popular_banco  # dados de exemplo (opcional)
python manage.py createsuperuser
python manage.py runserver
```

Os usuários que comentam são criados pelo superusuário em `/admin/`. Para
comentar, entre em `/contas/login/`.

## Implantação no Render

O arquivo `render.yaml` descreve o serviço (Blueprint). O `build.sh` instala
as dependências, coleta os arquivos estáticos, aplica as migrações, popula o
banco e cria o superusuário a partir das variáveis `DJANGO_SUPERUSER_*`.

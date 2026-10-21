import os
from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from blog.formatting import text_to_html
from blog.models import Category, Comment, Post

TZ = ZoneInfo('America/Sao_Paulo')


def data(dia, hora, minuto=0):
    return datetime(2026, 10, dia, hora, minuto, tzinfo=TZ)


USUARIOS = [
    ('ana', 'Ana', 'Souza'),
    ('carlos', 'Carlos', 'Lima'),
    ('julia', 'Júlia', 'Martins'),
    ('rafael', 'Rafael', 'Nakamura'),
]

CATEGORIAS = [
    ('Trajes', 'Maiôs, bermudas e macaquinhos de treino e de competição, incluindo trajes tecnológicos.'),
    ('Óculos', 'Óculos de treino e de prova: lentes espelhadas, fumê ou transparentes.'),
    ('Pé de pato', 'Nadadeiras curtas e longas para treino de pernada e golfinho.'),
    ('Palmar', 'Palmares de mão para treino de força e técnica de braçada.'),
]

POSTS = [
    {
        'title': 'Traje Speedo Fastskin LZR Pure Intent masculino – tam. 20',
        'posted_at': data(12, 19, 30),
        'author': 'ana',
        'categories': ['Trajes'],
        'text': """Traje de competição usado em apenas duas provas (estadual de inverno e um torneio universitário). Tecido ainda firme, costuras e silicone da cintura intactos, sem fios puxados.

- Marca/modelo: Speedo Fastskin LZR Pure Intent (bermuda de competição)
- Tamanho: 20 (equivale a P)
- Estado: muito bom — 2 usos, lavado só com água fria
- Retirada: CEPEUSP ou envio pelos Correios

Preço: R$ 850,00""",
        'comments': [
            ('carlos', 'Ainda está disponível? Serve para quem tem 1,78 m e 72 kg?', data(13, 8, 15)),
            ('julia', 'Aceita R$ 700 com retirada no CEPEUSP ainda esta semana?', data(13, 12, 40)),
            ('rafael', 'Tem nota fiscal ou alguma garantia de que é original?', data(14, 21, 5)),
        ],
    },
    {
        'title': 'Óculos Arena Cobra Ultra Swipe espelhado prata',
        'posted_at': data(14, 10, 0),
        'author': 'julia',
        'categories': ['Óculos'],
        'text': """Óculos de prova com lente espelhada e tecnologia antiembaçante Swipe (é só passar o dedo na lente molhada). Vem com estojo original e as quatro pontes nasais.

- Lente sem riscos; espelhamento perfeito
- Elástico duplo de silicone em bom estado
- Usado durante uma temporada de competições

Preço: R$ 210,00""",
        'comments': [
            ('ana', 'A vedação é boa para quem tem rosto mais fino?', data(14, 18, 20)),
            ('carlos', 'Faço por R$ 180 e busco hoje à noite na Raia Olímpica.', data(15, 9, 45)),
        ],
    },
    {
        'title': 'Kit treino: pé de pato Arena Powerfin Pro (40/41) + palmar Speedo Biofuse (M)',
        'posted_at': data(16, 15, 10),
        'author': 'carlos',
        'categories': ['Pé de pato', 'Palmar'],
        'text': """Kit completo para treino de força. Estou mudando de equipe e o técnico novo usa outro modelo de equipamento, então estou vendendo o que tenho.

- Pé de pato Arena Powerfin Pro, tamanho 40/41: bom estado, borracha sem rachaduras
- Palmar Speedo Biofuse, tamanho M: ótimo estado, tiras trocadas recentemente

Vendo também separado: pé de pato por R$ 220 e palmar por R$ 90.

Preço: R$ 280,00 o kit""",
        'comments': [
            ('julia', 'Vende só o palmar? Tenho interesse.', data(16, 19, 0)),
            ('rafael', 'O pé de pato serve para quem calça 42?', data(17, 7, 30)),
            ('ana', 'Fechado o kit por R$ 280! Posso buscar sábado de manhã?', data(17, 22, 10)),
        ],
    },
    {
        'title': 'Palmar Finis Agility (M) + óculos Speedo Vanquisher 2.0',
        'posted_at': data(18, 20, 45),
        'author': 'rafael',
        'categories': ['Palmar', 'Óculos'],
        'text': """Palmar sem tiras (o encaixe é só pelo polegar), ótimo para corrigir a pegada da braçada. Os óculos são de treino, lente fumê, perfeitos para piscina descoberta.

- Palmar Finis Agility: tamanho M, pouquíssimo uso
- Óculos Speedo Vanquisher 2.0: lente fumê, elástico novo

Preço: R$ 160,00 os dois""",
        'comments': [],
    },
]


class Command(BaseCommand):
    help = 'Popula o banco com usuários, categorias, anúncios e comentários de exemplo.'

    def handle(self, *args, **options):
        User = get_user_model()
        senha = os.environ.get('SEED_USER_PASSWORD')

        usuarios = {}
        for username, first_name, last_name in USUARIOS:
            user, criado = User.objects.get_or_create(
                username=username, defaults={'first_name': first_name, 'last_name': last_name},
            )
            if criado:
                # Sem SEED_USER_PASSWORD (p. ex. no Render) os usuários ficam sem senha utilizável
                if senha:
                    user.set_password(senha)
                else:
                    user.set_unusable_password()
                user.save()
            usuarios[username] = user

        categorias = {}
        for name, description in CATEGORIAS:
            categorias[name], _ = Category.objects.get_or_create(
                name=name, defaults={'description': description},
            )

        for dados in POSTS:
            autor = usuarios[dados['author']]
            post, criado = Post.objects.get_or_create(
                title=dados['title'],
                defaults={'content': text_to_html(dados['text']), 'posted_at': dados['posted_at'],
                          'author': autor},
            )
            if not criado:
                # bancos criados antes do campo autor existir
                if post.author is None:
                    post.author = autor
                    post.save(update_fields=['author'])
                continue
            post.categories.set(categorias[name] for name in dados['categories'])
            for username, text, posted_at in dados['comments']:
                Comment.objects.create(
                    post=post, author=usuarios[username], text=text, posted_at=posted_at,
                )

        self.stdout.write(self.style.SUCCESS(
            f'{Post.objects.count()} posts, {Comment.objects.count()} comentários, '
            f'{Category.objects.count()} categorias, {User.objects.count()} usuários.'
        ))

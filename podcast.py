import os
import openai
from elevenlabs.client import ElevenLabs
from datetime import datetime
from pathlib import Path
from pydub import AudioSegment

# Configurações a partir de variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_A = os.getenv("VOICE_A", "paulistano_masculino")
VOICE_B = os.getenv("VOICE_B", "paulistano_feminino")
MODEL_OPENAI = os.getenv("MODEL_OPENAI", "gpt-4o-mini")
ELEVEN_MODEL = os.getenv("ELEVEN_MODEL", "eleven_monolingual_v1")
SAIDA_DIR = Path(os.getenv("SAIDA_DIR", "./saida/public"))
TRILHA = os.getenv("TRILHA", "trilha.mp3")

PODCAST_TITLE = os.getenv("PODCAST_TITLE", "De Mala e Dog News — Espanha para Brasileiros")
PODCAST_AUTHOR = os.getenv("PODCAST_AUTHOR", "De Mala e Dog")
PODCAST_SUMMARY = os.getenv("PODCAST_SUMMARY", "Notícias, dicas e curiosidades da Espanha para brasileiros, em formato de bate-papo.")
PODCAST_FEED_PATH = Path(os.getenv("PODCAST_FEED_PATH", "./saida/public/feed.xml"))
PODCAST_AUDIO_BASE_URL = os.getenv("PODCAST_AUDIO_BASE_URL", "https://raw.githubusercontent.com/demalaedog/dmd_podcast/main/saida/public/")

# Inicializa clientes
openai.api_key = OPENAI_API_KEY
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# ---------------- FUNÇÕES ---------------- #

def gerar_roteiro():
    """Gera roteiro usando GPT."""
    prompt = """
    Crie um roteiro de podcast de notícias rápidas, em formato de bate-papo entre duas pessoas,
    focado em novidades, curiosidades e dicas da Espanha para brasileiros.
    O tom deve ser leve, divertido e informativo.
    """
    resposta = openai.chat.completions.create(
        model=MODEL_OPENAI,
        messages=[{"role": "user", "content": prompt}],
    )
    return resposta.choices[0].message.content.strip()


def gerar_audio(texto, arquivo_saida, voice=VOICE_A):
    """Gera áudio a partir do texto usando ElevenLabs."""
    print(f"🎤 Gerando áudio para {arquivo_saida} com voz {voice}...")

    audio = client.generate(
        text=texto,
        voice=voice,
        model=ELEVEN_MODEL
    )

    # Salvar áudio
    with open(arquivo_saida, "wb") as f:
        f.write(audio)

    # Também salvar texto correspondente
    txt_path = str(arquivo_saida).replace(".mp3", ".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(texto)


def mesclar_audios(lista_audios, trilha=None, arquivo_saida="podcast_final.mp3"):
    """Mescla áudios dos locutores e adiciona trilha."""
    final = AudioSegment.empty()

    for audio in lista_audios:
        final += AudioSegment.from_mp3(audio)

    if trilha and Path(trilha).exists():
        trilha_audio = AudioSegment.from_mp3(trilha) - 12  # volume mais baixo
        final = final.overlay(trilha_audio, loop=True)

    final.export(arquivo_saida, format="mp3")
    print(f"✅ Podcast final exportado: {arquivo_saida}")


def atualizar_feed(arquivo_mp3, titulo, descricao, feed_path=PODCAST_FEED_PATH):
    """Atualiza feed RSS simples para podcast."""
    url_audio = f"{PODCAST_AUDIO_BASE_URL}{Path(arquivo_mp3).name}"
    pub_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    item = f"""
    <item>
        <title>{titulo}</title>
        <description>{descricao}</description>
        <enclosure url="{url_audio}" type="audio/mpeg" />
        <guid>{url_audio}</guid>
        <pubDate>{pub_date}</pubDate>
    </item>
    """

    if feed_path.exists():
        with open(feed_path, "r", encoding="utf-8") as f:
            conteudo = f.read().replace("</channel>\n</rss>", "")
    else:
        conteudo = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>{PODCAST_TITLE}</title>
<description>{PODCAST_SUMMARY}</description>
<link>{PODCAST_AUDIO_BASE_URL}</link>
<language>pt-BR</language>
"""

    conteudo += item + "\n</channel>\n</rss>"

    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"📡 Feed atualizado em {feed_path}")


# ---------------- EXECUÇÃO ---------------- #

if __name__ == "__main__":
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)

    roteiro = gerar_roteiro()
    print("📜 Roteiro gerado:\n", roteiro)

    arquivo_a = SAIDA_DIR / "parte_a.mp3"
    arquivo_b = SAIDA_DIR / "parte_b.mp3"
    arquivo_final = SAIDA_DIR / f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"

    # Geração dos áudios (simples: um texto só, alternando vozes A e B)
    gerar_audio(roteiro, arquivo_a, VOICE_A)
    gerar_audio(roteiro, arquivo_b, VOICE_B)

    # Mesclar
    mesclar_audios([arquivo_a, arquivo_b], trilha=TRILHA, arquivo_saida=arquivo_final)

    # Atualizar feed
    atualizar_feed(arquivo_final, "Episódio Automático", "Podcast gerado automaticamente com IA")

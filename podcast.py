import os
import uuid
import time
from datetime import datetime
from pathlib import Path

# TTS e IA
try:
    import openai
    from elevenlabs import generate, save, set_api_key as eleven_set_api_key
except ImportError:
    openai = None
    generate = None
    save = None
    eleven_set_api_key = None

# RSS
import xml.etree.ElementTree as ET

# Configurações
SAIDA_DIR = Path(os.getenv('SAIDA_DIR', './saida/public'))
SAIDA_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
VOICE_A = os.getenv('VOICE_A', 'paulistano_masculino')
VOICE_B = os.getenv('VOICE_B', 'paulistano_feminino')
MODEL_OPENAI = os.getenv('MODEL_OPENAI', 'gpt-4o-mini')
ELEVEN_MODEL = os.getenv('ELEVEN_MODEL', 'eleven_monolingual_v1')

INTRO_APRESENTADORES = (
    'Fala viajante! Eu sou o Renan, e comigo está a Fernanda. '
    'Bem-vindo(a) ao De Mala e Dog News — Espanha para Brasileiros.'
)

# Inicializar APIs
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
if eleven_set_api_key and ELEVENLABS_API_KEY:
    eleven_set_api_key(ELEVENLABS_API_KEY)

# Função para gerar roteiro
def gerar_roteiro():
    prompt = f"""
Crie um roteiro de podcast em formato de DIÁLOGO entre dois apresentadores paulistanos.
Comece com: {INTRO_APRESENTADORES}

- Limite o texto a aproximadamente 800 palavras (até 5 minutos de áudio).
- Traga 4 blocos: Imigração/Documentação, Destinos/Viagens, Cultura/Gastronomia, Eventos/Agenda.
- Use linguagem clara e estilo de conversa.
"""
    if openai:
        resposta = openai.ChatCompletion.create(
            model=MODEL_OPENAI,
            messages=[{"role": "user", "content": prompt}]
        )
        return resposta.choices[0].message.content
    else:
        return f"{INTRO_APRESENTADORES} Aqui seria o roteiro de teste de até 5 minutos."

# Função para gerar áudio TTS
def gerar_audio(texto, arquivo_saida):
    if generate and save:
        audio = generate(texto, voice=VOICE_A, model=ELEVEN_MODEL)
        save(audio, arquivo_saida)
        return True
    else:
        with open(arquivo_saida.replace('.mp3', '.txt'), 'w') as f:
            f.write(texto)
        return False

# Criar RSS básico
def gerar_rss(arquivo_audio, titulo='Episódio', resumo='Resumo do episódio'):
    feed_path = SAIDA_DIR / 'feed.xml'
    item_guid = str(uuid.uuid4())

    if feed_path.exists():
        tree = ET.parse(feed_path)
        root = tree.getroot()
    else:
        root = ET.Element('rss', version='2.0')
        channel = ET.SubElement(root, 'channel')
        ET.SubElement(channel, 'title').text = 'De Mala e Dog News — Espanha para Brasileiros'
        ET.SubElement(channel, 'link').text = ''
        ET.SubElement(channel, 'description').text = 'Podcast sobre Espanha para brasileiros.'
        tree = ET.ElementTree(root)

    channel = root.find('channel')
    item = ET.SubElement(channel, 'item')
    ET.SubElement(item, 'title').text = titulo
    ET.SubElement(item, 'description').text = resumo
    ET.SubElement(item, 'guid').text = item_guid
    ET.SubElement(item, 'enclosure', url=f"{os.getenv('PODCAST_AUDIO_BASE_URL')}{arquivo_audio.name}", type='audio/mpeg')
    ET.SubElement(item, 'pubDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    tree.write(feed_path, encoding='utf-8', xml_declaration=True)

# ======== Execução ========
roteiro = gerar_roteiro()
arquivo_audio = SAIDA_DIR / f"episodio_{int(time.time())}.mp3"
gerar_audio(roteiro, arquivo_audio)
gerar_rss(arquivo_audio, titulo=f'Episódio {datetime.now().strftime("%d/%m/%Y")}', resumo='Resumo do episódio')
print(f'Episódio gerado: {arquivo_audio}')

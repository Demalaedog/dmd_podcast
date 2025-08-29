# podcast.py
import os
from pathlib import Path
from datetime import datetime
import openai
from elevenlabs import generate, set_api_key, save
import textwrap

# Configurações via ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_A = os.getenv("VOICE_A", "paulistano_masculino")
VOICE_B = os.getenv("VOICE_B", "paulistano_feminino")
SAIDA_DIR = Path(os.getenv("SAIDA_DIR", "./saida/public"))

set_api_key(ELEVENLABS_API_KEY)
openai.api_key = OPENAI_API_KEY

# Garantir que a pasta de saída existe
SAIDA_DIR.mkdir(parents=True, exist_ok=True)

def gerar_roteiro():
    """
    Gera um roteiro de até 5 minutos de notícias e curiosidades da Espanha para brasileiros
    """
    prompt = textwrap.dedent(f"""
    Você é um apresentador de podcast chamado "De Mala e Dog News — Espanha para Brasileiros".
    Crie um roteiro de conversa entre dois apresentadores: Renan (homem) e Fernanda (mulher), ambos com sotaque paulistano.
    O episódio deve ter aproximadamente 5 minutos.
    Inclua:
      - Notícias sobre imigração e documentações
      - Dicas de viagens e destinos na Espanha
      - Curiosidades culturais e gastronômicas
    Inicie com "Fala viajante!"
    Formate como diálogo, exemplo:
      Renan: ...
      Fernanda: ...
    """
    )
    
    response = openai.ChatCompletion.create(
        model=os.getenv("MODEL_OPENAI", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    
    roteiro = response.choices[0].message.content.strip()
    return roteiro

def gerar_audio(texto, arquivo_saida):
    """
    Gera o áudio a partir do texto usando ElevenLabs e salva roteiro em .txt
    """
    # Salvar roteiro em .txt
    arquivo_txt = Path(arquivo_saida).with_suffix('.txt')
    with open(arquivo_txt, 'w') as f:
        f.write(texto)
    
    # Dividir o roteiro para respeitar limite de tempo (~5 min)
    # Assumindo ~150 palavras por minuto, limitamos a 750 palavras
    palavras = texto.split()
    palavras = palavras[:750]
    texto_limitado = " ".join(palavras)

    # Criar áudio (simulação de conversa: alterna vozes)
    linhas = texto_limitado.splitlines()
    audio_final = None

    for linha in linhas:
        if linha.strip().startswith("Renan:"):
            voz = VOICE_A
            conteudo = linha.replace("Renan:", "").strip()
        elif linha.strip().startswith("Fernanda:"):
            voz = VOICE_B
            conteudo = linha.replace("Fernanda:", "").strip()
        else:
            # Linha neutra, usa voz A
            voz = VOICE_A
            conteudo = linha.strip()

        audio = generate(text=conteudo, voice=voz, model=os.getenv("ELEVEN_MODEL", "eleven_monolingual_v1"))
        if audio_final is None:
            audio_final = audio
        else:
            audio_final += audio

    # Salvar arquivo de áudio
    save(audio_final, str(arquivo_saida))

def main():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    arquivo_audio = SAIDA_DIR / f"episodio_{now}.mp3"
    
    print("Gerando roteiro...")
    roteiro = gerar_roteiro()
    
    print("Gerando áudio...")
    gerar_audio(roteiro, arquivo_audio)
    
    print(f"Episódio gerado: {arquivo_audio}")
    print("Roteiro salvo em .txt correspondente")

if __name__ == "__main__":
    main()

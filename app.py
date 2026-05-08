# 1. Importações das bibliotecas que vamos usar
 
import streamlit as st
from pytubefix import YouTube
from pytubefix.cli import on_progress
from pathlib import Path
import os
import re
 
# 2. Configuração da página
 
st.set_page_config(
    page_title="Baixador de Áudio do YouTube",
    page_icon="🎵",
    layout="centered"
)
 
# 3. Funções (a lógica que faz o download)
 
# Função para extrair o código do vídeo de QUALQUER link do YouTube
def extrair_codigo_video(url):
    """
    Pega qualquer link do YouTube e extrai só o código do vídeo.
    Funciona com:
    - youtu.be/ABC123
    - youtube.com/watch?v=ABC123
    - youtube.com/watch?v=ABC123&list=...
    - m.youtube.com/watch?v=ABC123
    - youtube.com/shorts/ABC123
    """
   
    # Lista de padrões de link do YouTube que vamos reconhecer
    padroes = [
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',  # Links de compartilhar: youtu.be/ABC123
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',  # Shorts: youtube.com/shorts/ABC123
        r'(?:v=)([a-zA-Z0-9_-]{11})',  # Links normais: watch?v=ABC123
        r'(?:embed/)([a-zA-Z0-9_-]{11})',  # Links embed: youtube.com/embed/ABC123
    ]
   
    # Tenta cada padrão até achar o código do vídeo
    for padrao in padroes:
        match = re.search(padrao, url)
        if match:
            codigo = match.group(1)
            return codigo
   
    # Se não achou nenhum padrão, devolve None
    return None
 
# Função para limpar o link do YouTube (tirar partes desnecessárias)
def limpar_link_youtube(url):
    """
    Transforma QUALQUER link do YouTube em um link limpo e funcionando.
    Exemplo: https://youtu.be/ABC123?si=XYZ -> https://youtube.com/watch?v=ABC123
    """
    # Extrai o código do vídeo
    codigo = extrair_codigo_video(url)
   
    if codigo:
        # Monta um link limpo (o formato mais confiável)
        link_limpo = f"https://www.youtube.com/watch?v={codigo}"
        return link_limpo
    else:
        # Se não conseguiu extrair, devolve o link original
        return url
 
# Função que tenta baixar, e se falhar, tenta com link limpo
def tentar_baixar(url, destino, tentativa_limpa=False):
    """
    Tenta baixar o áudio.
    Se falhar e ainda não tentou com link limpo, tenta de novo.
    """
    try:
        # Conecta ao vídeo do YouTube
        yt = YouTube(url, on_progress_callback=on_progress)
       
        # Pega apenas a melhor versão do áudio
        audio_stream = yt.streams.filter(only_audio=True).first()
       
        # Verifica se encontrou o áudio
        if audio_stream is None:
            return None, "Não foi possível encontrar áudio neste vídeo"
       
        # Baixa o áudio para a pasta escolhida
        arquivo_baixado = audio_stream.download(output_path=destino)
       
        # Muda a extensão do arquivo de .mp4 (ou outro) para .mp3
        arquivo_mp3 = os.path.splitext(arquivo_baixado)[0] + ".mp3"
        os.rename(arquivo_baixado, arquivo_mp3)
       
        return arquivo_mp3, None  # Sucesso!
       
    except Exception as erro:
        # Se deu erro e ainda NÃO tentamos com link limpo
        if not tentativa_limpa:
            return None, "precisa_limpar"  # Sinaliza que precisa tentar com link limpo
        else:
            # Já tentou com link limpo e falhou
            return None, str(erro)
 
# 4. Interface do Streamlit
 
# Título do app
st.title("🎵 Baixador de Áudio do YouTube")
 
# Subtítulo explicativo
st.caption("Funciona com qualquer link: normal, compartilhado, playlist ou Shorts")
 
# Separador
st.divider()
 
# Campo onde o usuário cola o link do vídeo
url = st.text_input(
    "📎 Link do YouTube:",
    placeholder="Cole o link aqui... (qualquer link do YouTube funciona)",
    key="url_input"
)
 
# Colunas para os botões de ação
col1, col2, col3 = st.columns([2, 1, 2])
 
with col1:
    if st.button("🗑️ Limpar", use_container_width=True):
        st.session_state.url_input = ""
        st.rerun()
 
with col2:
    # Botão vazio para espaçamento
    pass
 
with col3:
    # Botão vazio para espaçamento
    pass
 
# Campo para pasta de destino
st.subheader("📁 Configurações de Download")
 
# Opção de usar pasta padrão ou personalizada
opcao_pasta = st.radio(
    "Escolha onde salvar o arquivo:",
    ["📂 Downloads (padrão)", "📁 Escolher pasta personalizada"],
    index=0
)
 
destino = None
pasta_personalizada = None
 
if opcao_pasta == "📁 Escolher pasta personalizada":
    pasta_personalizada = st.text_input(
        "Caminho da pasta personalizada:",
        placeholder="Ex: C:/Users/SeuNome/Músicas ou /home/usuario/Musicas"
    )
    if pasta_personalizada:
        destino = Path(pasta_personalizada)
    else:
        destino = Path.home() / "Downloads"
else:
    destino = Path.home() / "Downloads"
 
# Botão principal que começa o download
if st.button("⬇️ BAIXAR ÁUDIO", type="primary", use_container_width=True):
    # Verifica se o usuário colocou um link
    if not url:
        st.error("❌ Cole um link do YouTube primeiro!")
    else:
        # Verifica se o link é do YouTube (tem "youtube" ou "youtu.be")
        if "youtube" not in url.lower() and "youtu.be" not in url.lower():
            st.error("❌ Isso não parece um link do YouTube! Verifique e tente novamente.")
        else:
            # Cria a pasta de destino se ela não existir
            destino.mkdir(exist_ok=True)
           
            # Mostra uma mensagem no status
            status_placeholder = st.empty()
            status_placeholder.info("📥 Baixando... aguarde")
           
            # PRIMEIRA TENTATIVA: com o link original do usuário
            arquivo, erro = tentar_baixar(url, destino, tentativa_limpa=False)
           
            # Se o erro for "precisa_limpar", tentamos com o link limpo
            if erro == "precisa_limpar":
                status_placeholder.warning("🔄 Corrigindo link automaticamente...")
               
                # Limpa o link (tira &list, &start_radio, etc)
                url_limpa = limpar_link_youtube(url)
               
                # SEGUNDA TENTATIVA: com o link já limpo
                arquivo, erro = tentar_baixar(url_limpa, destino, tentativa_limpa=True)
               
                if arquivo:
                    status_placeholder.success(
                        f"✅ Pronto! (Link foi corrigido automaticamente)\n\n📁 Arquivo salvo: {os.path.basename(arquivo)}"
                    )
                   
                    # Mostra o caminho completo do arquivo
                    st.code(str(arquivo), language="bash")
                else:
                    status_placeholder.error(f"❌ Erro: {erro}\n\n💡 Tente outro link ou verifique sua internet")
                   
            elif arquivo:
                # Deu certo na primeira tentativa
                status_placeholder.success(
                    f"✅ Pronto! Música salva com sucesso!\n\n📁 Arquivo: {os.path.basename(arquivo)}"
                )
               
                # Mostra o caminho completo do arquivo
                st.code(str(arquivo), language="bash")
            else:
                # Deu erro mesmo depois de tentar
                status_placeholder.error(f"❌ Erro: {erro}\n\n💡 Dica: Tente copiar o link direto do navegador")
 
# Separador
st.divider()
 
# Mensagem de status inicial
st.info("💡 Aguardando... Cole qualquer link do YouTube e clique em baixar")
 
# Informações adicionais na barra lateral
with st.sidebar:
    st.header("ℹ️ Informações")
    st.markdown("""
    ### Como usar:
    1. Cole qualquer link do YouTube
    2. Escolha onde salvar o arquivo
    3. Clique em "BAIXAR ÁUDIO"
   
    ### Links suportados:
    - ✅ Links normais (youtube.com/watch?v=...)
    - ✅ Links compartilhados (youtu.be/...)
    - ✅ Shorts (youtube.com/shorts/...)
    - ✅ Links com playlists
    - ✅ Links com parâmetros extras
   
    ### Observações:
    - O arquivo será salvo em MP3
    - Links com problemas são corrigidos automaticamente
    - Aguarde o processamento completo
    """)
   
    st.divider()
    st.caption("Desenvolvido com ❤️ usando Streamlit")

"""
Script pra você ajustar as logos de fundo (marca d'água) sozinho, sem
precisar pedir pra mim toda vez.

COMO USAR:
1. Mude os valores em "CONFIGURAÇÕES" abaixo (opacidade e largura de cada logo)
2. Salve o arquivo
3. Rode no terminal (com o ambiente virtual ativado):
       python gerar_marca_dagua.py
4. Atualize a página do app no navegador (F5) pra ver o resultado

A posição das logos (canto da tela) é ajustada num lugar diferente: dentro
do app.py, procure pelas classes CSS ".marca-dagua-cna" e ".marca-dagua-m7x"
(tem um comentário explicando cada valor bem ao lado).
"""
from pathlib import Path
from PIL import Image

ASSETS_DIR = Path(__file__).parent / "assets"

# --------------------------------------------------------------------------
# CONFIGURAÇÕES — mude os valores abaixo como quiser
# --------------------------------------------------------------------------

# Opacidade: 0.0 (invisível) até 1.0 (100% opaco, sem transparência nenhuma)
OPACIDADE_CNA = 0.45
OPACIDADE_M7X = 0.45

# Largura da logo em pixels (a altura ajusta sozinha, mantendo a proporção)
LARGURA_CNA = 170
LARGURA_M7X = 100

# --------------------------------------------------------------------------
# Não precisa mexer daqui pra baixo
# --------------------------------------------------------------------------


def gerar(nome_original: str, nome_saida: str, opacidade: float, largura: int):
    img = Image.open(ASSETS_DIR / nome_original).convert("RGBA")
    ratio = largura / img.width
    img = img.resize((largura, int(img.height * ratio)))
    r, g, b, a = img.split()
    a = a.point(lambda p: int(p * opacidade))
    resultado = Image.merge("RGBA", (r, g, b, a))
    resultado.save(ASSETS_DIR / nome_saida)
    print(f"✅ {nome_saida}: {resultado.size[0]}x{resultado.size[1]}px, "
          f"opacidade {int(opacidade*100)}%")


if __name__ == "__main__":
    gerar("logo_cna_original.png", "logo_cna_faded.png", OPACIDADE_CNA, LARGURA_CNA)
    gerar("logo_m7x_original.png", "logo_m7x_faded.png", OPACIDADE_M7X, LARGURA_M7X)
    print("\nPronto! Atualize a página do app (F5) pra ver a mudança.")

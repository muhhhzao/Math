"""
Quiz matemático - versão 1
Feito só com Python (Tkinter, que já vem instalado).

Regras:
- 10 perguntas fixas, cada uma é um nível.
- Cada acerto vale 50 pontos e passa para o próximo nível.
- Cada pergunta tem 10 segundos.
- Errou ou o tempo acabou: pontos zeram e volta para a tela de início.
- Ao acertar as 10, a partida termina e o resultado é salvo em historico.csv.
"""

import csv
import os
import random
import time
import tkinter as tk
from datetime import datetime

# ----------------------------------------------------------------------
# Configurações (troque aqui)
# ----------------------------------------------------------------------
NOME_AUTORA = "NOME DA ALUNA"
RA_AUTORA = "RA: 000000000"

# Por enquanto não existe campo de nome na tela: um nome fictício é sorteado.
NOMES_FICTICIOS = ["Ana", "Beatriz", "Carlos", "Daniela", "Eduardo", "Fernanda", "Gabriel", "Helena"]

PONTOS_POR_ACERTO = 50
SEGUNDOS_POR_PERGUNTA = 10
ARQUIVO_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico.csv")

# ----------------------------------------------------------------------
# Perguntas: (conta, resposta certa, alternativas)
# Níveis 1 a 4: + - x ÷   |   Níveis 5 a 10: mais difíceis
# ----------------------------------------------------------------------
PERGUNTAS = [
    ("23 + 19", 42, [41, 42, 43, 52]),
    ("85 − 37", 48, [48, 52, 58, 47]),
    ("7 × 8", 56, [54, 56, 63, 48]),
    ("72 ÷ 9", 8, [7, 8, 9, 6]),
    ("156 + 278", 434, [424, 434, 444, 334]),
    ("503 − 267", 236, [246, 226, 236, 336]),
    ("14 × 12", 168, [158, 178, 168, 148]),
    ("345 ÷ 5", 69, [59, 79, 69, 65]),
    ("(8 + 4) × 5", 60, [52, 60, 44, 40]),
    ("100 − 6 × 9 + 20", 66, [66, 76, 86, 56]),
]

# ----------------------------------------------------------------------
# Cores
# ----------------------------------------------------------------------
BRANCO = "#FFFFFF"
ROSA_BEBE = "#F8C8DC"
ROSA_CLARO = "#FDE9F0"
ROSA_FORTE = "#E87AA0"
ROSA_ESCURO = "#8E3358"
AMEIXA = "#5A3E4B"
VERDE = "#A8E6CF"
CORAL = "#FF9AA2"

LARGURA, ALTURA = 360, 640
FONTE = "Helvetica"


def salvar_resultado(nome, pontos, tempo_segundos):
    """Grava uma linha no historico.csv (cria o arquivo com cabeçalho se não existir)."""
    novo = not os.path.exists(ARQUIVO_DADOS)
    with open(ARQUIVO_DADOS, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f, delimiter=";")
        if novo:
            escritor.writerow(["data", "nome", "pontuacao", "tempo_segundos"])
        escritor.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            nome,
            pontos,
            round(tempo_segundos, 1),
        ])


class Jogo:
    def __init__(self, janela):
        self.janela = janela
        janela.title("Quiz matemático")
        janela.resizable(False, False)
        self.tela = tk.Canvas(janela, width=LARGURA, height=ALTURA, bg=BRANCO, highlightthickness=0)
        self.tela.pack()

        self.nivel = 0
        self.pontos = 0
        self.inicio = 0.0
        self.nome_jogador = ""
        self.limite = 0.0
        self.travado = False
        self.id_timer = None
        self.cartas = []

        self.mostrar_inicio()

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------
    def limpar(self):
        if self.id_timer is not None:
            self.janela.after_cancel(self.id_timer)
            self.id_timer = None
        self.tela.delete("all")

    def retangulo(self, x1, y1, x2, y2, raio, **opcoes):
        pontos = [
            x1 + raio, y1, x2 - raio, y1, x2, y1, x2, y1 + raio,
            x2, y2 - raio, x2, y2, x2 - raio, y2, x1 + raio, y2,
            x1, y2, x1, y2 - raio, x1, y1 + raio, x1, y1,
        ]
        return self.tela.create_polygon(pontos, smooth=True, **opcoes)

    def enfeites(self):
        self.tela.create_oval(-60, -60, 100, 100, fill=ROSA_BEBE, outline="")
        self.tela.create_oval(LARGURA - 100, ALTURA - 100, LARGURA + 60, ALTURA + 60, fill=ROSA_BEBE, outline="")

    def botao(self, x1, y1, x2, y2, texto, tag, cor=ROSA_FORTE, cor_texto=BRANCO, tamanho=20):
        self.retangulo(x1 + 2, y1 + 5, x2 + 2, y2 + 5, (y2 - y1) // 2, fill=ROSA_BEBE, outline="", tags=tag)
        self.retangulo(x1, y1, x2, y2, (y2 - y1) // 2, fill=cor, outline="", tags=tag)
        self.tela.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=texto, fill=cor_texto,
                              font=(FONTE, tamanho, "bold"), tags=tag)

    # ------------------------------------------------------------------
    # Tela de início
    # ------------------------------------------------------------------
    def mostrar_inicio(self):
        self.limpar()
        self.enfeites()
        self.retangulo(40, 110, 320, 250, 28, fill=ROSA_BEBE, outline="")
        self.tela.create_text(180, 160, text=NOME_AUTORA, fill=AMEIXA, font=(FONTE, 20, "bold"))
        self.tela.create_text(180, 205, text=RA_AUTORA, fill=ROSA_ESCURO, font=(FONTE, 15))
        self.botao(80, 470, 280, 535, "JOGAR", "jogar")
        self.tela.tag_bind("jogar", "<Button-1>", lambda e: self.iniciar_partida())

    def iniciar_partida(self):
        self.nome_jogador = random.choice(NOMES_FICTICIOS)
        self.nivel = 0
        self.pontos = 0
        self.inicio = time.time()
        self.mostrar_pergunta()

    # ------------------------------------------------------------------
    # Tela de pergunta
    # ------------------------------------------------------------------
    def mostrar_pergunta(self):
        self.limpar()
        self.travado = False
        conta, certa, alternativas = PERGUNTAS[self.nivel]
        alternativas = alternativas[:]
        random.shuffle(alternativas)

        self.enfeites()

        # topo: nível e pontos
        self.tela.create_text(24, 40, anchor="w", text=f"Pergunta {self.nivel + 1}/{len(PERGUNTAS)}",
                              fill=AMEIXA, font=(FONTE, 13))
        self.retangulo(236, 24, 336, 56, 16, fill=ROSA_BEBE, outline="")
        self.tela.create_text(286, 40, text=f"{self.pontos} pts", fill=AMEIXA, font=(FONTE, 13, "bold"))

        # barra de progresso
        self.retangulo(24, 74, 336, 84, 5, fill=ROSA_CLARO, outline="")
        if self.nivel > 0:
            largura = 24 + (336 - 24) * self.nivel / len(PERGUNTAS)
            self.retangulo(24, 74, largura, 84, 5, fill=ROSA_FORTE, outline="")

        # cartão da pergunta
        self.retangulo(32, 120, 328, 280, 28, fill=ROSA_BEBE, outline="")
        self.tela.create_text(180, 156, text="Quanto é", fill=ROSA_ESCURO, font=(FONTE, 13))
        tamanho = 40 if len(conta) <= 9 else 28
        self.tela.create_text(180, 215, text=f"{conta} = ?", fill=AMEIXA, font=(FONTE, tamanho, "bold"))

        # timer
        self.retangulo(32, 304, 328, 316, 6, fill=ROSA_CLARO, outline="")
        self.tela.create_text(180, 340, text="", fill=ROSA_ESCURO, font=(FONTE, 13), tags="timer_texto")

        # alternativas 2x2
        self.cartas = []
        posicoes = [(32, 380), (192, 380), (32, 480), (192, 480)]
        for i, (valor, (x, y)) in enumerate(zip(alternativas, posicoes)):
            tag = f"alt{i}"
            fundo = self.retangulo(x, y, x + 136, y + 80, 22, fill=BRANCO, outline=ROSA_BEBE, width=3, tags=tag)
            texto = self.tela.create_text(x + 68, y + 40, text=str(valor), fill=AMEIXA,
                                          font=(FONTE, 24, "bold"), tags=tag)
            self.cartas.append((valor, fundo, texto))
            self.tela.tag_bind(tag, "<Button-1>", lambda e, i=i: self.responder(i))
        self.limite = time.time() + SEGUNDOS_POR_PERGUNTA
        self.atualizar_timer()

    def atualizar_timer(self):
        restante = self.limite - time.time()
        if restante <= 0:
            self.tempo_esgotado()
            return
        self.tela.delete("timer_barra")
        fim = 32 + (328 - 32) * restante / SEGUNDOS_POR_PERGUNTA
        cor = ROSA_FORTE if restante > 3 else CORAL
        if fim - 32 > 12:
            self.retangulo(32, 304, fim, 316, 6, fill=cor, outline="", tags="timer_barra")
        self.tela.itemconfig("timer_texto", text=f"{restante:0.1f} s", fill=ROSA_ESCURO if restante > 3 else "#C0392B")
        self.id_timer = self.janela.after(100, self.atualizar_timer)

    # ------------------------------------------------------------------
    # Resposta
    # ------------------------------------------------------------------
    def indice_certo(self):
        certa = PERGUNTAS[self.nivel][1]
        for i, (valor, _, _) in enumerate(self.cartas):
            if valor == certa:
                return i
        return 0

    def colorir(self, i, cor):
        _, fundo, _ = self.cartas[i]
        self.tela.itemconfig(fundo, fill=cor, outline=cor)

    def responder(self, i):
        if self.travado:
            return
        self.travado = True
        if self.id_timer is not None:
            self.janela.after_cancel(self.id_timer)
            self.id_timer = None

        certa = PERGUNTAS[self.nivel][1]
        if self.cartas[i][0] == certa:
            self.colorir(i, VERDE)
            self.pontos += PONTOS_POR_ACERTO
            self.mensagem(f"Acertou! +{PONTOS_POR_ACERTO} pontos")
            self.janela.after(900, self.proximo_nivel)
        else:
            self.colorir(i, CORAL)
            self.colorir(self.indice_certo(), VERDE)
            self.errou("Errou! Tente Novamente")

    def tempo_esgotado(self):
        self.travado = True
        self.id_timer = None
        self.colorir(self.indice_certo(), VERDE)
        self.errou("Tempo esgotado!")

    def errou(self, texto):
        self.pontos = 0
        self.mensagem(texto, erro=True)
        self.janela.after(1500, self.mostrar_inicio)

    def mensagem(self, texto, erro=False):
        self.tela.delete("timer_texto")
        self.tela.create_text(180, 340, text=texto, fill="#C0392B" if erro else ROSA_ESCURO,
                              font=(FONTE, 13, "bold"))

    def proximo_nivel(self):
        self.nivel += 1
        if self.nivel >= len(PERGUNTAS):
            self.finalizar()
        else:
            self.mostrar_pergunta()

    # ------------------------------------------------------------------
    # Fim de jogo
    # ------------------------------------------------------------------
    def finalizar(self):
        duracao = time.time() - self.inicio
        salvar_resultado(self.nome_jogador, self.pontos, duracao)

        self.limpar()
        self.enfeites()
        self.retangulo(32, 120, 328, 340, 28, fill=ROSA_BEBE, outline="")
        self.tela.create_text(180, 160, text="Parabéns!", fill=AMEIXA, font=(FONTE, 26, "bold"))
        self.tela.create_text(180, 215, text=f"{self.pontos} pontos", fill=ROSA_ESCURO, font=(FONTE, 22, "bold"))
        self.tela.create_text(180, 255, text=f"Tempo: {duracao:0.1f} s", fill=AMEIXA, font=(FONTE, 13))
        self.tela.create_text(180, 295, text=f"Jogador: {self.nome_jogador}", fill=AMEIXA, font=(FONTE, 13))
        self.tela.create_text(180, 400, text="Resultado salvo em historico.csv", fill=ROSA_ESCURO, font=(FONTE, 11))
        self.botao(70, 450, 290, 515, "JOGAR DE NOVO", "denovo", tamanho=16)
        self.tela.tag_bind("denovo", "<Button-1>", lambda e: self.mostrar_inicio())


def main():
    janela = tk.Tk()
    Jogo(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()
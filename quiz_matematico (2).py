"""
Quiz matemático - versão 2
Feito só com Python (Tkinter, que já vem instalado).

Regras:
- 10 perguntas fixas, cada uma é um nível.
- Cada acerto vale 50 pontos e passa para o próximo nível.
- Cada pergunta tem 10 segundos.
- Antes de jogar, o jogador digita o nome.
- Errou ou o tempo acabou: a partida é salva, os pontos zeram e volta para a tela de início.
- Ao acertar as 10, a partida termina e também é salva.
- Cada partida vira uma linha do historico.csv (nome, pontuação e tempo de duração).
- A tela de ranking mostra o melhor resultado de cada jogador.
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
NOME_AUTORA = "Ana Carolina de Carvalho Xavier"
RA_AUTORA = "RA: 6023622"

MAX_NOME = 25  # tamanho máximo do nome digitado

PONTOS_POR_ACERTO = 50
SEGUNDOS_POR_PERGUNTA = 10
ARQUIVO_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico.csv")

# ----------------------------------------------------------------------
# Perguntas: (conta, resposta certa, alternativas)
# Só soma (+), subtração (−) e multiplicação (×), uma operação por pergunta
# ----------------------------------------------------------------------
PERGUNTAS = [
    ("12 + 8", 20, [18, 20, 22, 21]),
    ("15 − 7", 8, [6, 7, 8, 9]),
    ("6 × 4", 24, [20, 24, 28, 18]),
    ("9 + 14", 23, [13, 23, 24, 32]),
    ("25 + 17", 42, [32, 42, 43, 52]),
    ("30 − 12", 18, [28, 18, 17, 22]),
    ("8 × 5", 40, [35, 40, 45, 48]),
    ("20 − 9", 11, [10, 11, 12, 29]),
    ("7 × 6", 42, [36, 42, 48, 49]),
    ("9 × 7", 63, [56, 63, 54, 72]),
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


def salvar_resultado(nome, pontos, tempo_segundos, resultado):
    """Grava uma linha no historico.csv (cria o arquivo com cabeçalho se não existir).

    Uma linha por partida: data, nome, pontuação, tempo de duração e como a partida terminou.
    """
    novo = not os.path.exists(ARQUIVO_DADOS)
    with open(ARQUIVO_DADOS, "a", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        if novo:
            escritor.writerow(["data", "nome", "pontuacao", "tempo_segundos", "resultado"])
        escritor.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            nome,
            pontos,
            f"{tempo_segundos:.1f}".replace(".", ","),
            resultado,
        ])


def ler_historico():
    """Lê o historico.csv e devolve uma lista de (nome, pontos, tempo)."""
    if not os.path.exists(ARQUIVO_DADOS):
        return []
    partidas = []
    with open(ARQUIVO_DADOS, newline="", encoding="utf-8-sig") as f:
        for numero, linha in enumerate(csv.reader(f, delimiter=";")):
            if numero == 0 or len(linha) < 4:
                continue  # pula o cabeçalho e linhas incompletas
            try:
                partidas.append((linha[1], int(linha[2]), float(linha[3].replace(",", "."))))
            except ValueError:
                continue
    return partidas


def melhores_por_jogador(partidas):
    """Fica com o melhor resultado de cada jogador: mais pontos e, em empate, menos tempo."""
    melhores = {}
    for nome, pontos, tempo in partidas:
        chave = nome.casefold()
        atual = melhores.get(chave)
        if atual is None or (pontos, -tempo) > (atual[1], -atual[2]):
            melhores[chave] = (nome, pontos, tempo)
    return sorted(melhores.values(), key=lambda r: (-r[1], r[2]))


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
        self.campo_nome = None
        self.var_nome = None

        self.mostrar_inicio()

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------
    def limpar(self):
        if self.id_timer is not None:
            self.janela.after_cancel(self.id_timer)
            self.id_timer = None
        if self.campo_nome is not None:
            self.campo_nome.destroy()
            self.campo_nome = None
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
        self.tela.create_text(180, 157, text=NOME_AUTORA, fill=AMEIXA, font=(FONTE, 18, "bold"),
                              width=250, justify="center")
        self.tela.create_text(180, 218, text=RA_AUTORA, fill=ROSA_ESCURO, font=(FONTE, 15))

        # campo de nome do jogador (obrigatório para jogar)
        self.tela.create_text(180, 298, text="Digite seu nome", fill=ROSA_ESCURO, font=(FONTE, 13, "bold"))
        self.var_nome = tk.StringVar(value=self.nome_jogador)
        self.var_nome.trace_add("write", lambda *args: self.tela.delete("aviso"))
        self.campo_nome = tk.Entry(
            self.janela, textvariable=self.var_nome, font=(FONTE, 16), justify="center",
            bg=BRANCO, fg=AMEIXA, insertbackground=AMEIXA, relief="flat",
            highlightthickness=3, highlightbackground=ROSA_BEBE, highlightcolor=ROSA_FORTE,
            validate="key", validatecommand=(self.janela.register(lambda texto: len(texto) <= MAX_NOME), "%P"),
        )
        self.tela.create_window(180, 336, window=self.campo_nome, width=240, height=42)
        self.campo_nome.bind("<Return>", lambda e: self.iniciar_partida())
        self.campo_nome.focus_set()

        self.botao(80, 470, 280, 535, "JOGAR", "jogar")
        self.tela.tag_bind("jogar", "<Button-1>", lambda e: self.iniciar_partida())
        self.link_ranking(585)

    def iniciar_partida(self):
        nome = " ".join(self.var_nome.get().split())
        if not nome:
            self.tela.delete("aviso")
            self.tela.create_text(180, 380, text="Digite seu nome para jogar", fill="#C0392B",
                                  font=(FONTE, 12, "bold"), tags="aviso")
            self.campo_nome.focus_set()
            return
        self.nome_jogador = nome
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
            self.errou("Errou! Tente Novamente", "Errou")

    def tempo_esgotado(self):
        self.travado = True
        self.id_timer = None
        self.colorir(self.indice_certo(), VERDE)
        self.errou("Tempo esgotado!", "Tempo esgotado")

    def errou(self, texto, motivo):
        # a partida termina aqui: salva a pontuação alcançada e só depois zera os pontos
        duracao = time.time() - self.inicio
        salvar_resultado(self.nome_jogador, self.pontos, duracao, f"{motivo} na pergunta {self.nivel + 1}")
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
        salvar_resultado(self.nome_jogador, self.pontos, duracao, f"Concluiu as {len(PERGUNTAS)} perguntas")

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
        self.link_ranking(565)

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------
    def link_ranking(self, y):
        self.tela.create_rectangle(110, y - 14, 250, y + 14, fill=BRANCO, outline="", tags="ranking")
        self.tela.create_text(180, y, text="Ver ranking", fill=ROSA_ESCURO,
                              font=(FONTE, 13, "underline"), tags="ranking")
        self.tela.tag_bind("ranking", "<Button-1>", lambda e: self.mostrar_ranking())

    def mostrar_ranking(self):
        self.limpar()
        self.enfeites()
        ranking = melhores_por_jogador(ler_historico())

        self.tela.create_text(180, 52, text="Ranking", fill=AMEIXA, font=(FONTE, 26, "bold"))
        self.tela.create_text(180, 84, text="Melhor resultado de cada jogador", fill=ROSA_ESCURO,
                              font=(FONTE, 11))
        self.retangulo(24, 110, 336, 510, 24, fill=ROSA_BEBE, outline="")

        if not ranking:
            self.tela.create_text(180, 310, text="Ainda não há partidas salvas.", fill=AMEIXA,
                                  font=(FONTE, 13))
        for posicao, (nome, pontos, tempo) in enumerate(ranking[:8]):
            y = 140 + posicao * 46
            nome_curto = nome if len(nome) <= 14 else nome[:13] + "…"
            self.tela.create_text(44, y, anchor="w", text=f"{posicao + 1}º", fill=ROSA_ESCURO,
                                  font=(FONTE, 13, "bold"))
            self.tela.create_text(84, y, anchor="w", text=nome_curto, fill=AMEIXA, font=(FONTE, 13, "bold"))
            self.tela.create_text(262, y, anchor="e", text=f"{pontos} pts", fill=AMEIXA, font=(FONTE, 13))
            self.tela.create_text(324, y, anchor="e", text=f"{tempo:.1f} s".replace(".", ","),
                                  fill=ROSA_ESCURO, font=(FONTE, 12))

        self.botao(80, 545, 280, 605, "VOLTAR", "voltar", tamanho=18)
        self.tela.tag_bind("voltar", "<Button-1>", lambda e: self.mostrar_inicio())


def main():
    janela = tk.Tk()
    Jogo(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()

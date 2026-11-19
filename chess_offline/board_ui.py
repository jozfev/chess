"""Отрисовка шахматной доски, анимаций и правой панели."""
import pygame
import chess
from assets_loader import load_piece_images

BG = (18, 18, 18)
DARK = (36, 36, 36)
LIGHT = (56, 56, 56)
LIME = (182, 243, 106)
TEXT = (232, 235, 229)
MUTED = (142, 148, 140)
RED = (225, 86, 86)

class BoardUI:
    def __init__(self, screen, board, flipped=False):
        self.screen = screen
        self.board = board
        self.flipped = flipped
        self.board_x, self.board_y, self.square = 28, 38, 76
        self.board_size = self.square * 8
        self.panel_x = self.board_x + self.board_size + 30
        self.panel_w = screen.get_width() - self.panel_x - 24
        self.font = pygame.font.SysFont("arial", 17)
        self.small = pygame.font.SysFont("arial", 13)
        self.title = pygame.font.SysFont("arial", 22, bold=True)
        self.images = load_piece_images(self.square)
        self.last_move = None
        self.selected = None
        self.targets = []
        self.anim = None
        self.drag_square = None
        self.drag_pos = None
        self.move_scroll = 0
        self.status = ""
        self.mode = "Игрок vs Игрок"
        self.captured = {chess.WHITE: [], chess.BLACK: []}

    def square_rect(self, square):
        f, r = chess.square_file(square), chess.square_rank(square)
        if self.flipped:
            col, row = 7-f, r
        else:
            col, row = f, 7-r
        return pygame.Rect(self.board_x + col*self.square, self.board_y + row*self.square, self.square, self.square)

    def pixel_to_square(self, pos):
        x, y = pos
        col = (x-self.board_x)//self.square
        row = (y-self.board_y)//self.square
        if not (0 <= col < 8 and 0 <= row < 8):
            return None
        f, r = (7-col, row) if self.flipped else (col, 7-row)
        return chess.square(f, r)

    def begin_animation(self, move, duration=170):
        self.anim = {"move": move, "elapsed": 0, "duration": duration}

    def update(self, dt):
        if self.anim:
            self.anim["elapsed"] += dt
            if self.anim["elapsed"] >= self.anim["duration"]:
                self.anim = None

    def _draw_piece(self, piece, square, center_override=None):
        image = self.images[(piece.color, piece.piece_type)]
        rect = image.get_rect(center=center_override) if center_override else image.get_rect(center=self.square_rect(square).center)
        self.screen.blit(image, rect)

    def draw(self, board, selected=None, targets=None, last_move=None, status="", move_history=None):
        self.board = board
        self.selected, self.targets = selected, targets or []
        self.last_move, self.status = last_move, status
        self.screen.fill(BG)
        self._draw_board()
        self._draw_pieces(board)
        self._draw_panel(board, move_history or [])
        if self.anim:
            self._draw_animation(board)

    def _draw_board(self):
        for rank in range(8):
            for file in range(8):
                sq = chess.square(file, rank)
                rect = self.square_rect(sq)
                color = LIGHT if (file+rank) % 2 else DARK
                pygame.draw.rect(self.screen, color, rect)
        if self.last_move:
            for sq in (self.last_move.from_square, self.last_move.to_square):
                overlay = pygame.Surface((self.square, self.square), pygame.SRCALPHA)
                overlay.fill((*LIME, 48))
                self.screen.blit(overlay, self.square_rect(sq))
        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                check_overlay = pygame.Surface((self.square, self.square), pygame.SRCALPHA)
                pygame.draw.rect(check_overlay, (225, 70, 70, 75), check_overlay.get_rect(), border_radius=5)
                self.screen.blit(check_overlay, self.square_rect(king_sq).topleft)
                pygame.draw.rect(self.screen, (225, 86, 86), self.square_rect(king_sq), 3, border_radius=5)
        if self.selected is not None:
            pygame.draw.rect(self.screen, LIME, self.square_rect(self.selected), 3, border_radius=4)
        for sq in self.targets:
            center = self.square_rect(sq).center
            if self.board.piece_at(sq):
                pygame.draw.circle(self.screen, (*LIME, 150), center, 29, 3)
            else:
                dot = pygame.Surface((self.square, self.square), pygame.SRCALPHA)
                pygame.draw.circle(dot, (*LIME, 155), (self.square//2, self.square//2), 8)
                self.screen.blit(dot, self.square_rect(sq).topleft)
        # Координаты по краям доски.
        for i in range(8):
            file_char = "abcdefgh"[7-i if self.flipped else i]
            rank_char = str(i+1 if self.flipped else 8-i)
            self.screen.blit(self.small.render(file_char, True, MUTED),
                             (self.board_x+i*self.square+5, self.board_y+self.board_size+3))
            self.screen.blit(self.small.render(rank_char, True, MUTED),
                             (self.board_x-15, self.board_y+i*self.square+4))

    def _draw_pieces(self, board):
        moving = self.anim["move"] if self.anim else None
        for sq, piece in board.piece_map().items():
            if moving and sq == moving.to_square:
                continue
            if self.drag_square == sq:
                continue
            self._draw_piece(piece, sq)
        if self.drag_square is not None and self.drag_pos:
            piece = board.piece_at(self.drag_square)
            if piece:
                self._draw_piece(piece, self.drag_square, self.drag_pos)

    def _draw_animation(self, board):
        move = self.anim["move"]
        piece = board.piece_at(move.to_square)
        if not piece:
            return
        t = min(1.0, self.anim["elapsed"]/self.anim["duration"])
        eased = 1 - (1-t)**3
        start = self.square_rect(move.from_square).center
        end = self.square_rect(move.to_square).center
        center = (int(start[0]+(end[0]-start[0])*eased), int(start[1]+(end[1]-start[1])*eased))
        self._draw_piece(piece, move.to_square, center)

    
    def _draw_panel(self, board, history):
        x = self.panel_x

        self.screen.blit(
            self.title.render("CHESS", True, TEXT),
            (x, 30)
        )

        self.screen.blit(
            self.small.render("OFFLINE / PYTHON", True, MUTED),
            (x, 57)
        )

        pygame.draw.line(
            self.screen, (55, 58, 54),
            (x, 82), (x + self.panel_w, 82)
        )

        turn = "Белые ходят" if board.turn else "Чёрные ходят"

        self.screen.blit(
            self.font.render(turn, True, LIME),
            (x, 95)
        )

        if board.is_check():
            self.screen.blit(
                self.small.render("ШАХ", True, RED),
                (x, 120)
            )

        self.screen.blit(
            self.small.render(self.mode, True, MUTED),
            (x, 142)
        )

        self.screen.blit(
            self.small.render(
                getattr(self, "difficulty", "Средний"),
                True, LIME
            ),
            (x, 162)
        )

        pygame.draw.line(
            self.screen, (55, 58, 54),
            (x, 185), (x + self.panel_w, 185)
        )

        self.screen.blit(
            self.font.render("ИСТОРИЯ ХОДОВ", True, TEXT),
            (x, 198)
        )

        clip = pygame.Rect(x, 225, self.panel_w, 175)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip)

        rows = []

        for i in range(0, len(history), 2):
            rows.append((
                f"{i // 2 + 1:>2}.",
                history[i],
                history[i + 1] if i + 1 < len(history) else ""
            ))

        for idx, row in enumerate(rows):
            y = 228 + idx * 25 - self.move_scroll

            if y < 205 or y > 400:
                continue

            self.screen.blit(
                self.small.render(row[0], True, MUTED),
                (x, y)
            )

            self.screen.blit(
                self.font.render(row[1], True, TEXT),
                (x + 34, y - 2)
            )

            self.screen.blit(
                self.font.render(row[2], True, MUTED),
                (x + 112, y - 2)
            )

        self.screen.set_clip(old_clip)

        pygame.draw.line(
            self.screen, (55, 58, 54),
            (x, 410), (x + self.panel_w, 410)
        )

        self.screen.blit(
            self.font.render("ВЗЯТЫЕ ФИГУРЫ", True, TEXT),
            (x, 422)
        )

        white_taken = " ".join(
            self._symbol(p) for p in self.captured[chess.WHITE]
        )

        black_taken = " ".join(
            self._symbol(p) for p in self.captured[chess.BLACK]
        )

        self.screen.blit(
            self.small.render("Белые: " + white_taken, True, MUTED),
            (x, 450)
        )

        self.screen.blit(
            self.small.render("Чёрные: " + black_taken, True, MUTED),
            (x, 470)
        )

        self.screen.blit(
            self.small.render(self.status, True, TEXT),
            (x, 495)
        )

        self._draw_button(
            (x, 525, self.panel_w, 35),
            "Новая игра"
        )

        self._draw_button(
            (x, 568, self.panel_w, 35),
            "Отменить ход"
        )

        self._draw_button(
            (x, 611, self.panel_w, 35),
            "Перевернуть доску"
        )

        self._draw_button(
            (x, 654, self.panel_w, 35),
            "Сложность ИИ: " + getattr(self, "difficulty", "Средний")
        )

    def _draw_button(self, rect, label):
        pygame.draw.rect(
            self.screen,
            (29, 32, 29),
            rect,
            border_radius=7
        )

        pygame.draw.rect(
            self.screen,
            (65, 71, 62),
            rect,
            1,
            border_radius=7
        )

        text = self.small.render(label, True, TEXT)

        self.screen.blit(
            text,
            text.get_rect(
                center=(
                    rect[0] + rect[2] // 2,
                    rect[1] + rect[3] // 2
                )
            )
        )


    def _draw_button(self, rect, label):
        pygame.draw.rect(self.screen, (29, 32, 29), rect, border_radius=7)
        pygame.draw.rect(self.screen, (65, 71, 62), rect, 1, border_radius=7)
        text = self.small.render(label, True, TEXT)
        self.screen.blit(text, text.get_rect(center=(rect[0]+rect[2]//2, rect[1]+rect[3]//2)))

    def _symbol(self, piece):
        symbols = {chess.PAWN:"♟", chess.KNIGHT:"♞", chess.BISHOP:"♝",
                   chess.ROOK:"♜", chess.QUEEN:"♛", chess.KING:"♚"}
        return symbols.get(piece.piece_type, "?")

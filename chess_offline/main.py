"""Запуск: python main.py"""
import pygame
import chess
import sys
from board_ui import BoardUI, BG, LIME, RED, TEXT, MUTED
from engine import ChessBot

WIDTH, HEIGHT = 1040, 700
FPS = 120
BOT_DEPTHS = {
    "Лёгкий": 2,
    "Средний": 3,
    "Сложный": 4
}

DIFFICULTIES = list(BOT_DEPTHS.keys())
difficulty_index = 1
BOT_COLOR = chess.BLACK

def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error:
        pass
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Chess — Offline")
    clock = pygame.time.Clock()
    board = chess.Board()
    
    ui = BoardUI(screen, board)

    bot = ChessBot(
        BOT_DEPTHS[DIFFICULTIES[difficulty_index]]
    )

    ui.difficulty = DIFFICULTIES[difficulty_index]

    selected = None
    legal_targets = []

    selected = None
    legal_targets = []
    history_san = []
    move_stack_san = []
    last_move = None
    promotion_pending = None
    game_mode = 0  # 0: PvP, 1: игрок белыми против бота чёрными
    bot_waiting = False
    status = "Белые начинают"
    running = True

    def reset():
        nonlocal board, selected, legal_targets, history_san, move_stack_san
        nonlocal last_move, promotion_pending, status, bot_waiting, bot
        board = chess.Board()
        selected = None
        legal_targets = []
        history_san = []
        move_stack_san = []
        last_move = None
        promotion_pending = None
        status = "Белые начинают"
        bot_waiting = False
        bot = ChessBot(BOT_DEPTH)
        ui.captured = {chess.WHITE: [], chess.BLACK: []}
        ui.anim = None

    def commit_move(move):
        nonlocal last_move, selected, legal_targets, status, bot_waiting
        if move not in board.legal_moves:
            return False
        san = board.san(move)
        captured = board.piece_at(move.to_square)
        if board.is_en_passant(move):
            captured = chess.Piece(chess.PAWN, not board.turn)
        if captured:
            ui.captured[board.turn].append(captured)
        board.push(move)
        history_san.append(san)
        last_move = move
        ui.begin_animation(move)
        selected = None
        legal_targets = []
        if board.is_checkmate():
            status = "Мат — " + ("победили белые" if board.turn == chess.BLACK else "победили чёрные")
        elif board.is_stalemate():
            status = "Пат — ничья"
        elif board.is_insufficient_material() or board.can_claim_draw():
            status = "Ничья"
        elif board.is_check():
            status = "Шах"
        else:
            status = "Ход чёрных" if board.turn == chess.BLACK else "Ход белых"
        if game_mode == 1 and board.turn == BOT_COLOR and not board.is_game_over(claim_draw=True):
            bot.start(board)
            bot_waiting = True
        return True

    def open_promotion(from_sq, to_sq):
        nonlocal promotion_pending
        options = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        legal = [chess.Move(from_sq, to_sq, promotion=p) for p in options]
        if any(m in board.legal_moves for m in legal):
            promotion_pending = (from_sq, to_sq, legal)

    def draw_promotion():
        if not promotion_pending:
            return
        from_sq, to_sq, moves = promotion_pending
        rect = ui.square_rect(to_sq)
        menu_w, menu_h = 52, 48
        x = min(max(rect.centerx-menu_w*2, 8), WIDTH-menu_w*4-8)
        y = max(8, rect.y-menu_h-8)
        pygame.draw.rect(screen, (31,34,31), (x, y, menu_w*4, menu_h), border_radius=8)
        kinds = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        for i, kind in enumerate(kinds):
            piece = chess.Piece(kind, board.turn)
            img = ui.images[(piece.color, piece.piece_type)]
            screen.blit(pygame.transform.smoothscale(img, (42,42)), (x+i*menu_w+5, y+3))
            pygame.draw.rect(screen, LIME, (x+i*menu_w, y, menu_w, menu_h), 1, border_radius=5)
        return pygame.Rect(x, y, menu_w*4, menu_h)

    while running:
        dt = clock.tick(FPS)
        ui.update(dt)
        # Получаем результат бота, не блокируя основной цикл.
        if bot_waiting and not bot.thinking:
            move = bot.poll()
            bot_waiting = False
            if move and move in board.legal_moves:
                commit_move(move)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                ui.screen = screen
                ui.panel_w = screen.get_width()-ui.panel_x-24
            elif event.type == pygame.MOUSEWHEEL:
                if event.y:
                    ui.move_scroll = max(0, min(max(0, (len(history_san)//2)*27-230), ui.move_scroll-event.y*30))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    reset()
                elif event.key == pygame.K_u and board.move_stack and not bot_waiting:
                    # В режиме бота отменяем последний ход бота и предыдущий ход игрока.
                    count = 2 if game_mode == 1 and len(board.move_stack) >= 2 else 1
                    for _ in range(count):
                        board.pop()
                        if history_san: history_san.pop()
                    reset_captured = {chess.WHITE: [], chess.BLACK: []}
                    ui.captured = reset_captured
                    for mv in board.move_stack:
                        pass
                    selected = None; legal_targets = []; last_move = board.peek() if board.move_stack else None
                    status = "Ход белых" if board.turn else "Ход чёрных"
                elif event.key == pygame.K_f:
                    ui.flipped = not ui.flipped
                elif event.key == pygame.K_m:
                    game_mode = 1-game_mode
                    ui.mode = "Игрок vs Бот" if game_mode else "Игрок vs Игрок"
                    reset()
                elif event.key == pygame.K_ESCAPE:
                    promotion_pending = None
                    selected = None
                    legal_targets = []

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if promotion_pending:
                    from_sq, to_sq, moves = promotion_pending
                    menu = draw_promotion()
                    if menu and menu.collidepoint(pos):
                        idx = min(3, max(0, (pos[0]-menu.x)//52))
                        chosen = moves[idx]
                        promotion_pending = None
                        commit_move(chosen)
                    else:
                        promotion_pending = None
                    continue

                # Кнопки боковой панели.
                if pos[0] >= ui.panel_x:
                    mid = ui.panel_x + ui.panel_w // 2
                    if 548 <= pos[1] <= 590 and pos[0] < mid:
                        reset()
                    elif 548 <= pos[1] <= 590 and pos[0] >= mid and board.move_stack:
                        count = 2 if game_mode == 1 and len(board.move_stack) >= 2 else 1
                        for _ in range(count):
                            if board.move_stack: board.pop()
                            if history_san: history_san.pop()
                        selected = None; legal_targets = []
                        last_move = board.peek() if board.move_stack else None
                        status = "Ход белых" if board.turn else "Ход чёрных"
                        ui.captured = {chess.WHITE: [], chess.BLACK: []}
                    elif 600 <= pos[1] <= 642 and pos[0] < mid:
                        ui.flipped = not ui.flipped
                    elif 600 <= pos[1] <= 642 and pos[0] >= mid:
                        game_mode = 1-game_mode
                        ui.mode = "Игрок vs Бот" if game_mode else "Игрок vs Игрок"
                        reset()
                    continue

                sq = ui.pixel_to_square(pos)
                if sq is None or bot_waiting or board.is_game_over(claim_draw=True):
                    continue
                if game_mode == 1 and board.turn == BOT_COLOR:
                    continue
                if selected is not None and sq in legal_targets:
                    piece = board.piece_at(selected)
                    if piece and piece.piece_type == chess.PAWN and chess.square_rank(sq) in (0,7):
                        open_promotion(selected, sq)
                    else:
                        commit_move(chess.Move(selected, sq))
                    continue
                piece = board.piece_at(sq)
                if piece and piece.color == board.turn:
                    selected = sq
                    legal_targets = [m.to_square for m in board.legal_moves if m.from_square == sq]
                    ui.drag_square = sq
                    ui.drag_pos = pos

            elif event.type == pygame.MOUSEMOTION:
                if ui.drag_square is not None:
                    ui.drag_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if ui.drag_square is not None:
                    origin = ui.drag_square
                    destination = ui.pixel_to_square(event.pos)
                    ui.drag_square = None
                    ui.drag_pos = None
                    if destination is not None and destination in legal_targets:
                        piece = board.piece_at(origin)
                        if piece and piece.piece_type == chess.PAWN and chess.square_rank(destination) in (0,7):
                            open_promotion(origin, destination)
                        else:
                            commit_move(chess.Move(origin, destination))

        ui.draw(board, selected, legal_targets, last_move, status, history_san)
        draw_promotion()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

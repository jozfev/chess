
import chess
import threading
import queue
import math

VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}


def evaluate(board):
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000

    if board.is_game_over(claim_draw=True):
        return 0

    score = 0

    for square, piece in board.piece_map().items():
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        center = 3.5 - (
            abs(3.5 - file_idx) +
            abs(3.5 - rank_idx)
        ) / 2

        sign = 1 if piece.color == chess.WHITE else -1
        positional = 0

        if piece.piece_type == chess.PAWN:
            advance = rank_idx if piece.color == chess.WHITE else 7 - rank_idx
            positional = advance * 7 + center * 2

        elif piece.piece_type == chess.KNIGHT:
            positional = center * 8

        elif piece.piece_type == chess.BISHOP:
            positional = center * 5

        elif piece.piece_type == chess.QUEEN:
            positional = center * 1.5

        score += sign * (
            VALUES[piece.piece_type] + positional
        )

    mobility = board.legal_moves.count()
    score += mobility if board.turn == chess.WHITE else -mobility

    return score


def move_order_score(board, move):
    score = 0

    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)

        victim_value = VALUES[victim.piece_type] if victim else 100
        attacker_value = VALUES[attacker.piece_type] if attacker else 0

        score += 1000 + victim_value - attacker_value // 10

    if move.promotion:
        score += 800 + VALUES.get(move.promotion, 0)

    if board.gives_check(move):
        score += 50

    return score


def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or board.is_game_over(claim_draw=True):
        return evaluate(board), None

    moves = list(board.legal_moves)
    moves.sort(
        key=lambda move: move_order_score(board, move),
        reverse=True
    )

    best_move = None

    if maximizing:
        best = -math.inf

        for move in moves:
            board.push(move)

            value, _ = minimax(
                board, depth - 1,
                alpha, beta, False
            )

            board.pop()

            if value > best:
                best = value
                best_move = move

            alpha = max(alpha, best)

            if beta <= alpha:
                break

        return best, best_move

    else:
        best = math.inf

        for move in moves:
            board.push(move)

            value, _ = minimax(
                board, depth - 1,
                alpha, beta, True
            )

            board.pop()

            if value < best:
                best = value
                best_move = move

            beta = min(beta, best)

            if beta <= alpha:
                break

        return best, best_move


def choose_move(board, depth=3):
    if board.is_game_over(claim_draw=True):
        return None

    _, move = minimax(
        board,
        depth,
        -math.inf,
        math.inf,
        board.turn == chess.WHITE
    )

    return move


class ChessBot:

    def __init__(self, depth=3):
        self.depth = depth
        self.results = queue.Queue()
        self.thread = None
        self.thinking = False

    def start(self, board):
        if self.thinking:
            return

        snapshot = board.copy(stack=True)
        self.thinking = True

        def worker():
            try:
                result = choose_move(snapshot, self.depth)
                self.results.put(result)
            finally:
                self.thinking = False

        self.thread = threading.Thread(
            target=worker,
            daemon=True
        )

        self.thread.start()

    def poll(self):
        try:
            return self.results.get_nowait()
        except queue.Empty:
            return None

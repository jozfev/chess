"""Загрузка спрайтов шахматных фигур. PNG необязательны: есть встроенный рендер."""
from pathlib import Path
import pygame
import chess

PIECE_LETTERS = {
    chess.KING: "K", chess.QUEEN: "Q", chess.ROOK: "R",
    chess.BISHOP: "B", chess.KNIGHT: "N", chess.PAWN: "P",
}
UNICODE_PIECES = {
    (chess.WHITE, chess.KING): "♔", (chess.WHITE, chess.QUEEN): "♕",
    (chess.WHITE, chess.ROOK): "♖", (chess.WHITE, chess.BISHOP): "♗",
    (chess.WHITE, chess.KNIGHT): "♘", (chess.WHITE, chess.PAWN): "♙",
    (chess.BLACK, chess.KING): "♚", (chess.BLACK, chess.QUEEN): "♛",
    (chess.BLACK, chess.ROOK): "♜", (chess.BLACK, chess.BISHOP): "♝",
    (chess.BLACK, chess.KNIGHT): "♞", (chess.BLACK, chess.PAWN): "♟",
}

def _piece_surface(piece, size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # Мягкая тень и контрастный круг делают фигуры читаемыми даже без PNG.
    center = (size // 2, size // 2)
    pygame.draw.circle(surf, (0, 0, 0, 75), (center[0] + 2, center[1] + 3), int(size * .37))
    fill = (225, 229, 222) if piece.color == chess.WHITE else (35, 39, 39)
    edge = (38, 43, 40) if piece.color == chess.WHITE else (205, 214, 203)
    pygame.draw.circle(surf, fill, center, int(size * .355))
    pygame.draw.circle(surf, edge, center, int(size * .355), max(2, size // 32))
    symbol = UNICODE_PIECES[(piece.color, piece.piece_type)]
    font = pygame.font.SysFont("segoeuisymbol,dejavusans,arial", int(size * .64), bold=False)
    glyph = font.render(symbol, True, edge)
    # На системах без шахматного Unicode-глифа используем буквенный знак.
    if glyph.get_width() < size * .12:
        glyph = pygame.font.SysFont("arial", int(size * .43), bold=True).render(
            PIECE_LETTERS[piece.piece_type], True, edge)
    surf.blit(glyph, glyph.get_rect(center=center))
    return surf

def load_piece_images(square_size, assets_dir="assets"):
    """Ищет assets/{w,b}_{k,q,r,b,n,p}.png, иначе создаёт фигуры в памяти."""
    result = {}
    root = Path(assets_dir)
    codes = {chess.KING:"k", chess.QUEEN:"q", chess.ROOK:"r",
             chess.BISHOP:"b", chess.KNIGHT:"n", chess.PAWN:"p"}
    for color, prefix in ((chess.WHITE, "w"), (chess.BLACK, "b")):
        for kind, code in codes.items():
            key = (color, kind)
            path = root / f"{prefix}_{code}.png"
            try:
                image = pygame.image.load(str(path)).convert_alpha() if path.exists() else _piece_surface(chess.Piece(kind, color), square_size)
                result[key] = pygame.transform.smoothscale(image, (square_size, square_size))
            except (pygame.error, OSError):
                result[key] = _piece_surface(chess.Piece(kind, color), square_size)
    return result

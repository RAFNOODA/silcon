"""Small custom UI toolkit for the game's dark management-sim interface."""
from __future__ import annotations
from dataclasses import dataclass
import pygame

BG = (13, 17, 27)
SURFACE = (22, 28, 42)
SURFACE_2 = (29, 37, 54)
SURFACE_3 = (36, 46, 66)
BORDER = (48, 61, 83)
TEXT = (237, 242, 250)
MUTED = (147, 160, 181)
ACCENT = (83, 220, 185)
BLUE = (100, 157, 255)
PURPLE = (169, 127, 255)
YELLOW = (255, 197, 92)
RED = (255, 110, 125)
GREEN = (97, 220, 153)

@dataclass
class HitTarget:
    rect: pygame.Rect
    callback: object
    enabled: bool = True

class Painter:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self.hits: list[HitTarget] = []

    def set_surface(self, surface: pygame.Surface) -> None:
        self.surface = surface

    def font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont("segoeui", size, bold=bold)
        return self.fonts[key]

    def rounded(self, rect, color, radius=14, border=None, width=1):
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.surface, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.surface, border, rect, width, border_radius=radius)

    def label(self, text, x, y, size=16, color=TEXT, bold=False, anchor="topleft", max_width=None):
        font = self.font(size, bold)
        rendered = font.render(str(text), True, color)
        if max_width and rendered.get_width() > max_width:
            txt = str(text)
            while txt and font.size(txt + "…")[0] > max_width:
                txt = txt[:-1]
            rendered = font.render(txt + "…", True, color)
        rect = rendered.get_rect()
        setattr(rect, anchor, (int(x), int(y)))
        self.surface.blit(rendered, rect)
        return rect

    def paragraph(self, text, rect, size=14, color=MUTED, line_gap=5, max_lines=5):
        font = self.font(size)
        words = str(text).split()
        lines, line = [], ""
        for word in words:
            candidate = word if not line else line + " " + word
            if font.size(candidate)[0] <= rect.width:
                line = candidate
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
        for i, value in enumerate(lines[:max_lines]):
            self.label(value, rect.x, rect.y + i * (size + line_gap), size, color)
        return min(len(lines), max_lines) * (size + line_gap)

    def panel(self, rect, title=None, subtitle=None, accent=None):
        self.rounded(rect, SURFACE, 16, BORDER)
        if accent:
            pygame.draw.rect(self.surface, accent, pygame.Rect(rect.x, rect.y + 17, 3, 27), border_radius=2)
        if title:
            self.label(title, rect.x + 20, rect.y + 17, 17, TEXT, True)
        if subtitle:
            self.label(subtitle, rect.x + 20, rect.y + 42, 12, MUTED)

    def button(self, rect, text, callback, enabled=True, kind="primary", size=14):
        rect = pygame.Rect(rect)
        self.hits.append(HitTarget(rect, callback, enabled))
        if not enabled:
            fill, fg, border = (34, 39, 51), (105, 116, 132), None
        elif kind == "primary": fill, fg, border = (58, 190, 157), (8, 26, 28), None
        elif kind == "danger": fill, fg, border = (75, 38, 51), RED, RED
        elif kind == "selected": fill, fg, border = (36, 82, 80), ACCENT, ACCENT
        elif kind == "outline": fill, fg, border = SURFACE_2, TEXT, BORDER
        elif kind == "gold": fill, fg, border = (82, 65, 35), YELLOW, YELLOW
        else: fill, fg, border = SURFACE_2, TEXT, None
        self.rounded(rect, fill, 9, border)
        if enabled and kind in ("primary", "gold"):
            pygame.draw.line(self.surface, (255, 255, 255, 50), (rect.x + 12, rect.y + 1), (rect.right - 12, rect.y + 1), 1)
        self.label(text, rect.centerx, rect.centery, size, fg, True, "center", max_width=rect.width - 14)

    def meter(self, rect, value, max_value, color=ACCENT, bg=SURFACE_3):
        rect = pygame.Rect(rect)
        self.rounded(rect, bg, rect.height // 2)
        ratio = 0 if max_value <= 0 else max(0, min(1, value / max_value))
        if ratio > 0:
            self.rounded((rect.x, rect.y, max(4, int(rect.width * ratio)), rect.height), color, rect.height // 2)

    def divider(self, x1, y, x2, color=BORDER):
        pygame.draw.line(self.surface, color, (x1, y), (x2, y), 1)

    def icon_badge(self, rect, text, color=ACCENT):
        self.rounded(rect, (int(color[0] * .15), int(color[1] * .15), int(color[2] * .15)), 10)
        self.label(text, pygame.Rect(rect).centerx, pygame.Rect(rect).centery, 14, color, True, "center")

    def handle_click(self, pos):
        for target in reversed(self.hits):
            if target.rect.collidepoint(pos):
                if target.enabled:
                    target.callback()
                return True
        return False

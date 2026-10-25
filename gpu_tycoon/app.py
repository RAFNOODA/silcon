"""Main interface and application event loop."""
from __future__ import annotations
import random
import sys
import pygame
from .data import ARCHITECTURES, PROCESS_NODES, MEMORIES, MILESTONES
from .models import GameState
from .economy import (
    create_new_game, design_product, set_price, set_production, advance_month,
    invest_research, hire_staff, run_marketing_campaign, upgrade_factory,
    save_game, load_game, save_path, money, date_label, available_items,
    compute_specs, competitor_snapshot,
)
from .ui import Painter, HitTarget, BG, SURFACE, SURFACE_2, SURFACE_3, BORDER, TEXT, MUTED, ACCENT, BLUE, PURPLE, YELLOW, RED, GREEN

NAV_ITEMS = [
    ("dashboard", "Genel Bakış", "▦"),
    ("lab", "GPU Laboratuvarı", "◈"),
    ("factory", "Üretim Fabrikası", "▤"),
    ("market", "Pazar & Satış", "↗"),
    ("research", "AR-GE Merkezi", "⌘"),
    ("team", "Ekip & Marka", "♧"),
    ("finance", "Finans Raporu", "≋"),
]

class SiliconFoundryApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Silicon Foundry — GPU Company Simulator")
        self.screen = pygame.display.set_mode((1440, 900), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.p = Painter(self.screen)
        self.state = create_new_game()
        self.rng = random.Random()
        self.running = True
        self.intro = True
        self.company_input = "NovaSilicon"
        self.focused_input: str | None = None
        self.product_name = "NovaFire 100"
        self.selected_arch = ARCHITECTURES[0].name
        self.selected_node = PROCESS_NODES[0].name
        self.selected_memory = MEMORIES[0].name
        self.clock_speed = 200
        self.toast = ""
        self.toast_timer = 0
        self.last_report: dict | None = None
        self.dialog: str | None = None
        self.dialog_input = ""
        self._sync_technology_selection()

    def _sync_technology_selection(self):
        for kind, attr, items in (
            ("architecture", "selected_arch", ARCHITECTURES),
            ("node", "selected_node", PROCESS_NODES),
            ("memory", "selected_memory", MEMORIES),
        ):
            choices = available_items(self.state, kind)
            if choices and getattr(self, attr) not in [x.name for x in choices]:
                setattr(self, attr, choices[-1].name if len(choices) == 1 else choices[0].name)

    def notify(self, message: str, color=ACCENT):
        self.toast = message
        self.toast_timer = 3.6
        self.toast_color = color

    def handle_result(self, result):
        ok, message = result
        self.notify(message, ACCENT if ok else RED)

    def start_new_game(self):
        self.state = create_new_game(self.company_input)
        self.state.active_tab = "dashboard"
        self.intro = False
        self.focused_input = None
        self.notify(f"{self.state.company_name} için yönetim dönemi başladı.")
        self._sync_technology_selection()

    def try_load(self):
        try:
            self.state = load_game()
            self.intro = False
            self.focused_input = None
            self._sync_technology_selection()
            self.notify("Kayıt başarıyla yüklendi.")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.notify(f"Kayıt yüklenemedi: {exc}", RED)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            self.p.set_surface(self.screen)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.intro:
                if hasattr(self, "intro_input_rect") and self.intro_input_rect.collidepoint(pos):
                    self.focused_input = "company"
                elif hasattr(self, "intro_start_rect") and self.intro_start_rect.collidepoint(pos):
                    self.start_new_game()
                elif hasattr(self, "intro_load_rect") and self.intro_load_rect.collidepoint(pos):
                    self.try_load()
                else:
                    self.focused_input = None
            elif self.dialog:
                if hasattr(self, "dialog_input_rect") and self.dialog_input_rect.collidepoint(pos):
                    self.focused_input = "dialog"
                elif hasattr(self, "dialog_save_rect") and self.dialog_save_rect.collidepoint(pos):
                    if self.dialog == "rename":
                        new_name = " ".join(self.dialog_input.strip().split())[:28]
                        if new_name:
                            self.state.company_name = new_name
                            self.notify(f"Şirket adı: {new_name}")
                    self.dialog = None
                    self.focused_input = None
                elif hasattr(self, "dialog_cancel_rect") and self.dialog_cancel_rect.collidepoint(pos):
                    self.dialog = None
                    self.focused_input = None
                else:
                    self.focused_input = None
            else:
                clicked = self.p.handle_click(pos)
                if not clicked:
                    if hasattr(self, "product_name_rect") and self.product_name_rect.collidepoint(pos):
                        self.focused_input = "product"
                    else:
                        self.focused_input = None
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.dialog: self.dialog = None
                elif self.focused_input: self.focused_input = None
                else: self.state.active_tab = "dashboard"
            elif self.focused_input:
                target = self.focused_input
                current = self.company_input if target == "company" else (self.product_name if target == "product" else self.dialog_input)
                if event.key == pygame.K_RETURN:
                    if target == "company" and self.intro: self.start_new_game()
                    elif target == "dialog":
                        if self.dialog == "rename" and self.dialog_input.strip(): self.state.company_name = self.dialog_input.strip()[:28]
                        self.dialog = None
                    self.focused_input = None
                elif event.key == pygame.K_BACKSPACE:
                    current = current[:-1]
                elif event.unicode and event.unicode.isprintable() and len(current) < (32 if target == "product" else 28):
                    current += event.unicode
                if target == "company": self.company_input = current
                elif target == "product": self.product_name = current
                else: self.dialog_input = current

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get(): self.handle_event(event)
            if self.toast_timer > 0: self.toast_timer = max(0, self.toast_timer - dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()

    def draw(self):
        self.screen.fill(BG)
        self.p.hits = []
        if self.intro:
            self.draw_intro()
        else:
            self.draw_shell()
            tab = self.state.active_tab
            draw_methods = {
                "dashboard": self.draw_dashboard, "lab": self.draw_lab, "factory": self.draw_factory,
                "market": self.draw_market, "research": self.draw_research, "team": self.draw_team,
                "finance": self.draw_finance,
            }
            draw_methods.get(tab, self.draw_dashboard)()
            if self.dialog: self.draw_dialog()
            if self.toast_timer > 0: self.draw_toast()

    def draw_intro(self):
        w, h = self.screen.get_size()
        # Decorative grid and chip-inspired hero graphic.
        for x in range(0, w, 54): pygame.draw.line(self.screen, (21, 30, 44), (x, 0), (x, h), 1)
        for y in range(0, h, 54): pygame.draw.line(self.screen, (21, 30, 44), (0, y), (w, y), 1)
        pygame.draw.circle(self.screen, (25, 77, 77), (int(w*.77), int(h*.36)), 190, 1)
        pygame.draw.circle(self.screen, (24, 58, 83), (int(w*.77), int(h*.36)), 145, 1)
        chip = pygame.Rect(int(w*.77)-78, int(h*.36)-78, 156, 156)
        self.p.rounded(chip, (28, 68, 70), 27, ACCENT, 2)
        self.p.rounded(chip.inflate(-26, -26), (17, 43, 51), 19, (69, 142, 130), 1)
        for i in range(6):
            for j in range(6):
                r = pygame.Rect(chip.x+28+j*17, chip.y+28+i*17, 8, 8)
                pygame.draw.rect(self.screen, ACCENT if (i+j)%3 else BLUE, r, border_radius=2)
        x, y = int(w*.11), int(h*.22)
        self.p.icon_badge((x, y, 54, 54), "SF", ACCENT)
        self.p.label("SILICON FOUNDRY", x, y+76, 42, TEXT, True)
        self.p.label("GPU COMPANY SIMULATOR", x+1, y+125, 16, ACCENT, True)
        self.p.paragraph("1998 yılında küçük bir donanım girişimi olarak başla. Mimari geliştir, üretim düğümlerini araştır, fabrikayı büyüt ve küresel GPU pazarında yer edin.", pygame.Rect(x, y+170, min(480, w*.38), 85), 17, MUTED, 8, 4)
        self.p.label("ŞİRKETİNİ KUR", x, y+286, 13, YELLOW, True)
        box = pygame.Rect(x, y+315, 350, 52)
        self.p.rounded(box, SURFACE, 10, ACCENT if self.focused_input == "company" else BORDER)
        self.p.label(self.company_input + ("▏" if self.focused_input == "company" else ""), box.x+17, box.centery, 17, TEXT, False, "midleft")
        self.intro_input_rect = box
        self.p.button((x, y+385, 220, 54), "ŞİRKETİ KUR  →", self.start_new_game, True, "primary", 15)
        self.intro_start_rect = pygame.Rect(x, y+385, 220, 54)
        self.p.button((x+232, y+385, 118, 54), "KAYDI AÇ", self.try_load, True, "outline", 13)
        self.intro_load_rect = pygame.Rect(x+232, y+385, 118, 54)
        self.p.label("YÖNETİM SİMÜLASYONU  ·  1998—2035+", x, h-62, 12, MUTED, True)
        self.p.label("v0.1.0  |  Otomatik kayıt açık", w-28, h-34, 11, MUTED, False, "bottomright")
        if self.toast_timer > 0: self.draw_toast()

    def draw_shell(self):
        w, h = self.screen.get_size()
        # Header.
        self.p.rounded((18, 16, 48, 48), (24, 65, 68), 13, (49, 129, 119))
        self.p.label("SF", 42, 40, 15, ACCENT, True, "center")
        self.p.label("SILICON FOUNDRY", 78, 21, 15, TEXT, True)
        self.p.label(self.state.company_name, 78, 43, 12, MUTED)
        self.p.label(f"{date_label(self.state)}  ·  Mali dönem", w-365, 25, 13, MUTED, False, "topleft")
        self.p.icon_badge((w-142, 17, 42, 42), "₵", YELLOW)
        self.p.label(money(self.state.money), w-89, 24, 17, TEXT, True)
        self.p.label("KASA BAKİYESİ", w-89, 45, 10, MUTED, True)
        self.p.divider(18, 77, w-18)
        # Side navigation.
        sx, sy, sw = 18, 94, 218
        self.p.rounded((sx, sy, sw, h-114), SURFACE, 15, BORDER)
        self.p.label("YÖNETİM PANELİ", sx+18, sy+20, 11, MUTED, True)
        for i, (key, label, icon) in enumerate(NAV_ITEMS):
            r = pygame.Rect(sx+10, sy+52+i*51, sw-20, 43)
            active = self.state.active_tab == key
            if active:
                self.p.rounded(r, (34, 72, 73), 10, (47, 115, 108))
                self.p.rounded((r.x, r.y+8, 3, r.height-16), ACCENT, 2)
            self.p.label(icon, r.x+17, r.centery, 17, ACCENT if active else MUTED, True, "center")
            self.p.label(label, r.x+38, r.centery, 13, TEXT if active else MUTED, active, "midleft")
            self.p.hits.append(HitTarget(r, lambda key=key: setattr(self.state, "active_tab", key)))
        self.p.divider(sx+15, sy+425, sx+sw-15)
        self.p.label("ŞİRKET DURUMU", sx+18, sy+445, 10, MUTED, True)
        self.p.label(f"{self.state.engineers} mühendis", sx+18, sy+472, 12, TEXT)
        self.p.label(f"{self.state.researchers} araştırmacı", sx+18, sy+495, 12, TEXT)
        self.p.label(f"{len(self.state.products)} aktif ürün", sx+18, sy+518, 12, TEXT)
        self.p.label("İTİBAR", sx+18, sy+555, 10, MUTED, True)
        self.p.label(f"{self.state.reputation}/100", sx+sw-18, sy+555, 11, ACCENT, True, "topright")
        self.p.meter((sx+18, sy+576, sw-36, 6), self.state.reputation, 100, ACCENT)
        self.p.label("ESC  ·  Ana panele dön", sx+18, h-43, 10, (103, 117, 139))
        self.content = pygame.Rect(254, 94, max(420, w-272), h-114)

    def page_heading(self, title, subtitle, action=None):
        r = self.content
        self.p.label(title, r.x+3, r.y+4, 26, TEXT, True)
        self.p.label(subtitle, r.x+4, r.y+36, 13, MUTED)
        if action:
            rect = pygame.Rect(r.right-190, r.y+7, 184, 42)
            self.p.button(rect, action[0], action[1], action[2] if len(action)>2 else True, action[3] if len(action)>3 else "primary", 13)

    def kpi(self, rect, label, value, detail, color=ACCENT, icon=None):
        # Callers may pass either a pygame.Rect or an (x, y, w, h) tuple.
        # Normalize first so all KPI drawing paths have the same interface.
        rect = pygame.Rect(rect)
        self.p.rounded(rect, SURFACE, 14, BORDER)
        self.p.label(label.upper(), rect.x+16, rect.y+14, 10, MUTED, True)
        self.p.label(value, rect.x+16, rect.y+36, 23, TEXT, True)
        self.p.label(detail, rect.x+16, rect.bottom-22, 11, color, True)
        if icon: self.p.icon_badge((rect.right-42, rect.y+13, 28, 28), icon, color)

    def draw_dashboard(self):
        self.page_heading("Genel Bakış", "Donanım imparatorluğunu yönet · Aylık raporlarla büyümeyi takip et.", ("AYI İLERLET  →", self.advance_turn))
        r = self.content
        top = r.y+70
        gap = 12
        kw = (r.width-3*gap)//4
        profit = self.state.last_month_profit
        cards = [
            ("Kasa bakiyesi", money(self.state.money), "Şirket likiditesi", GREEN if self.state.money>=0 else RED, "$"),
            ("Son ay net kâr", money(profit), "Gelir − tüm giderler", GREEN if profit>=0 else RED, "↗"),
            ("Marka itibarı", f"{self.state.reputation}/100", "Müşteri güveni", ACCENT, "★"),
            ("AR-GE puanı", f"{self.state.research_points:.0f} RP", f"+{7+self.state.researchers*4+self.state.engineers*.6:.0f} / ay", PURPLE, "⌘"),
        ]
        for i, item in enumerate(cards): self.kpi((r.x+i*(kw+gap), top, kw, 104), *item[:3], item[3], item[4])
        chart_y = top+119
        left_w = int(r.width*.62)
        chart = pygame.Rect(r.x, chart_y, left_w, 270)
        self.p.panel(chart, "Finansal performans", "Gelir ve gider · Son 12 aylık kayıt", BLUE)
        self.draw_chart(pygame.Rect(chart.x+22, chart.y+76, chart.width-44, 154), "revenue", "expenses")
        self.p.label("Gelir", chart.x+23, chart.bottom-25, 11, ACCENT, True)
        self.p.label("Gider", chart.x+88, chart.bottom-25, 11, YELLOW, True)
        side = pygame.Rect(chart.right+12, chart_y, r.right-(chart.right+12), 270)
        self.p.panel(side, "Sektör gündemi", "Teknoloji ve pazar olayları", YELLOW)
        if self.state.current_event:
            ev = self.state.current_event
            self.p.icon_badge((side.x+18, side.y+69, 36, 36), "!", YELLOW)
            self.p.label(ev["title"], side.x+65, side.y+71, 14, TEXT, True, max_width=side.width-80)
            self.p.paragraph(ev["text"], pygame.Rect(side.x+19, side.y+119, side.width-38, 70), 12, MUTED, 4, 4)
        else:
            milestone = MILESTONES.get(self.state.year)
            title, text = milestone if milestone else ("Pazar gözlemi", "Teknoloji yatırımlarıyla ürün portföyünü güçlendir. Fiyatı ve üretim hedefini pazar koşullarına göre ayarla.")
            self.p.icon_badge((side.x+18, side.y+69, 36, 36), "i", BLUE)
            self.p.label(title, side.x+65, side.y+71, 13, TEXT, True, max_width=side.width-80)
            self.p.paragraph(text, pygame.Rect(side.x+19, side.y+119, side.width-38, 72), 12, MUTED, 4, 4)
        self.p.divider(side.x+18, side.y+205, side.right-18)
        self.p.label("Hızlı eylemler", side.x+18, side.y+218, 11, MUTED, True)
        self.p.button((side.x+15, side.y+237, max(90, (side.width-40)//2), 27), "GPU tasarla", lambda: setattr(self.state, "active_tab", "lab"), True, "selected", 11)
        self.p.button((side.x+22+max(90, (side.width-40)//2), side.y+237, max(80, (side.width-50)//2), 27), "Kaydet", self.save_current, True, "outline", 11)
        product_y = chart.bottom+14
        remaining_h = r.bottom-product_y-8
        products_rect = pygame.Rect(r.x, product_y, r.width, max(108, remaining_h))
        self.p.panel(products_rect, "Ürün portföyü", f"{len(self.state.products)} ürün · {sum(p.inventory for p in self.state.products):,} adet stokta", ACCENT)
        if not self.state.products:
            self.p.label("Henüz bir GPU ürünün yok.", products_rect.x+21, products_rect.y+74, 14, TEXT, True)
            self.p.label("Laboratuvara geçip ilk mimarini seç ve tasarımını piyasaya sür.", products_rect.x+21, products_rect.y+99, 12, MUTED)
            self.p.button((products_rect.right-175, products_rect.y+67, 155, 38), "İlk GPU'yu tasarla", lambda: setattr(self.state, "active_tab", "lab"), True, "primary", 12)
        else:
            card_gap = 10
            cardw = (products_rect.width-40-card_gap*min(3, len(self.state.products)-1))//min(4, len(self.state.products))
            for i, product in enumerate(self.state.products[:4]):
                xx = products_rect.x+19+i*(cardw+card_gap)
                yy = products_rect.y+68
                self.p.rounded((xx, yy, cardw, 94), SURFACE_2, 10, BORDER)
                self.p.label(product.name, xx+12, yy+12, 13, TEXT, True, max_width=cardw-22)
                self.p.label(f"{product.benchmark:.0f} benchmark", xx+12, yy+37, 11, ACCENT, True)
                self.p.label(f"{money(product.price)} · {product.inventory:,} stok", xx+12, yy+59, 11, MUTED)
                self.p.label(f"Son ay satış: {product.last_month_sales:,}", xx+12, yy+77, 10, GREEN)

    def draw_chart(self, rect, key_a="revenue", key_b="expenses"):
        hist = self.state.history[-12:]
        if len(hist) < 2:
            self.p.label("İlk mali rapor için ayı ilerlet.", rect.centerx, rect.centery, 12, MUTED, False, "center")
            return
        values = [max(0, float(row.get(key_a, 0))) for row in hist] + [max(0, float(row.get(key_b, 0))) for row in hist]
        peak = max(values + [1])
        for i in range(5):
            yy = rect.y + i*rect.height/4
            pygame.draw.line(self.screen, (36, 45, 61), (rect.x, int(yy)), (rect.right, int(yy)), 1)
        for key, color in ((key_a, ACCENT), (key_b, YELLOW)):
            pts = []
            for i, row in enumerate(hist):
                xx = rect.x + (i/(len(hist)-1))*rect.width
                vv = max(0, float(row.get(key, 0)))
                yy = rect.bottom - (vv/peak)*(rect.height-12)-5
                pts.append((int(xx), int(yy)))
            if len(pts)>1: pygame.draw.lines(self.screen, color, False, pts, 3)
            for pt in pts[-3:]: pygame.draw.circle(self.screen, color, pt, 3)

    def draw_lab(self):
        self.page_heading("GPU Laboratuvarı", "Mimariyi, üretim düğümünü ve belleği bir araya getirerek yeni bir ekran kartı tasarla.")
        r = self.content
        x, y, w = r.x, r.y+69, r.width
        leftw = int(w*.65)
        left = pygame.Rect(x, y, leftw, r.bottom-y-6)
        right = pygame.Rect(left.right+12, y, r.right-left.right-12, left.height)
        self.p.panel(left, "Yeni ürün tasarımı", "Teknolojiler yalnızca tarih ve AR-GE seviyen uygun olduğunda kullanılabilir.", ACCENT)
        name_rect = pygame.Rect(left.x+18, left.y+74, left.width-36, 43)
        self.p.label("ÜRÜN SERİSİ ADI", name_rect.x, name_rect.y-19, 10, MUTED, True)
        self.p.rounded(name_rect, SURFACE_2, 9, ACCENT if self.focused_input=="product" else BORDER)
        self.p.label(self.product_name + ("▏" if self.focused_input=="product" else ""), name_rect.x+13, name_rect.centery, 14, TEXT, False, "midleft")
        self.product_name_rect = name_rect
        section_y = name_rect.bottom+25
        self.draw_technology_picker(left, "MİMARİ", "architecture", ARCHITECTURES, "selected_arch", section_y, ACCENT)
        section_y += 142
        self.draw_technology_picker(left, "ÜRETİM DÜĞÜMÜ", "node", PROCESS_NODES, "selected_node", section_y, BLUE)
        section_y += 142
        self.draw_technology_picker(left, "BELLEK TEKNOLOJİSİ", "memory", MEMORIES, "selected_memory", section_y, PURPLE)
        # Clock speed is adjusted using compact controls.
        speed_y = min(left.bottom-100, section_y+139)
        self.p.label("ÇEKİRDEK SAATİ", left.x+20, speed_y, 11, MUTED, True)
        self.p.label(f"{self.clock_speed} MHz", left.x+20, speed_y+22, 19, TEXT, True)
        self.p.button((left.right-158, speed_y+4, 55, 33), "−100", lambda: setattr(self, "clock_speed", max(100, self.clock_speed-100)), True, "outline", 11)
        self.p.button((left.right-93, speed_y+4, 73, 33), "+100", lambda: setattr(self, "clock_speed", min(3000, self.clock_speed+100)), True, "outline", 11)
        self.p.button((left.x+18, left.bottom-57, left.width-36, 42), "TASARIMI TAMAMLA  →", self.launch_product, True, "primary", 14)
        self.p.panel(right, "Tasarım analizi", "Tahmini üretim ve performans", BLUE)
        try:
            benchmark, cost = compute_specs(self.selected_arch, self.selected_node, self.selected_memory, self.clock_speed, self.state.driver_level)
            arch = next(a for a in ARCHITECTURES if a.name==self.selected_arch)
            node = next(a for a in PROCESS_NODES if a.name==self.selected_node)
            mem = next(a for a in MEMORIES if a.name==self.selected_memory)
            suggested = max(49, round((85 + benchmark*1.15)/10)*10)
        except StopIteration:
            benchmark, cost, suggested, arch, node, mem = 100, 90, 199, ARCHITECTURES[0], PROCESS_NODES[0], MEMORIES[0]
        self.draw_gpu_art(pygame.Rect(right.x+right.width/2-72, right.y+76, 144, 85), benchmark)
        self.p.label(self.product_name.strip() or "Yeni GPU", right.centerx, right.y+179, 16, TEXT, True, "midtop", max_width=right.width-28)
        self.p.label(self.selected_arch, right.centerx, right.y+204, 10, MUTED, False, "midtop", max_width=right.width-22)
        self.p.divider(right.x+18, right.y+232, right.right-18)
        start = right.y+250
        stats = [("PERFORMANS", f"{benchmark:.0f} puan", ACCENT), ("BİRİM MALİYETİ", money(cost), YELLOW), ("ÖNERİLEN FİYAT", money(suggested), GREEN), ("SAAT HIZI", f"{self.clock_speed} MHz", BLUE)]
        for i, (label, value, color) in enumerate(stats):
            yy = start+i*61
            self.p.label(label, right.x+20, yy, 10, MUTED, True)
            self.p.label(value, right.x+20, yy+20, 17, TEXT, True)
            self.p.meter((right.x+20, yy+45, right.width-40, 4), benchmark if i==0 else (cost if i==1 else (suggested if i==2 else self.clock_speed)), 600 if i==0 else (180 if i==1 else (800 if i==2 else 3000)), color)
        self.p.rounded((right.x+15, right.bottom-106, right.width-30, 88), (27, 42, 52), 10, (39, 78, 83))
        self.p.label("TASARIM NOTU", right.x+28, right.bottom-91, 10, ACCENT, True)
        self.p.paragraph(f"Tahmini maliyet {money(cost)}/kart. Fiyatı ve üretim miktarını pazarda ayarlayabilirsin. Tasarım ücreti, teknoloji seviyesine göre değişir.", pygame.Rect(right.x+28, right.bottom-69, right.width-56, 48), 11, MUTED, 3, 3)

    def draw_gpu_art(self, rect, benchmark):
        x, y, w, h = rect
        body = pygame.Rect(x+7, y+8, w-14, h-16)
        self.p.rounded(body, (27, 45, 57), 12, (57, 111, 115), 2)
        chip = pygame.Rect(body.x+19, body.y+15, 49, 38)
        self.p.rounded(chip, (27, 89, 87), 7, ACCENT)
        for i in range(3): pygame.draw.line(self.screen, (113, 239, 208), (chip.x+12+i*12, chip.y+6), (chip.x+12+i*12, chip.bottom-6), 2)
        fanx, fany = body.right-36, body.centery
        pygame.draw.circle(self.screen, (17, 28, 40), (fanx, fany), 21, 2)
        pygame.draw.circle(self.screen, BLUE, (fanx, fany), 15, 2)
        for i in range(6):
            import math
            angle = i*math.pi/3
            pygame.draw.line(self.screen, BLUE, (fanx, fany), (fanx+int(math.cos(angle)*14), fany+int(math.sin(angle)*14)), 3)
        for i in range(4): pygame.draw.rect(self.screen, YELLOW, (body.x+12+i*8, body.bottom-5, 5, 7), border_radius=1)
        self.p.label(f"{benchmark:.0f}", body.centerx, body.centery+1, 13, TEXT, True, "center")

    def draw_technology_picker(self, panel, title, kind, items, attr, y, color):
        available = available_items(self.state, kind)
        self.p.label(title, panel.x+20, y, 10, MUTED, True)
        columns = 3
        gap = 8
        cardw = (panel.width-40-gap*(columns-1))//columns
        # Keep the currently selected option visible while exposing the newest technologies.
        shown = available[-9:]
        selected_name = getattr(self, attr)
        selected_item = next((item for item in available if item.name == selected_name), None)
        if selected_item and selected_item not in shown:
            shown = [selected_item] + shown[-8:]
        for i, item in enumerate(shown):
            row, col = divmod(i, columns)
            rr = pygame.Rect(panel.x+20+col*(cardw+gap), y+22+row*40, cardw, 34)
            selected = selected_name == item.name
            self.p.button(rr, item.name, lambda name=item.name, attr=attr: setattr(self, attr, name), True, "selected" if selected else "outline", 10)
            self.p.label(f"{item.year} · T{item.tier}", rr.x+7, rr.bottom-2, 8, ACCENT if selected else MUTED, False, "bottomleft")
        if not available:
            self.p.label("Henüz açılmadı", panel.x+22, y+28, 11, RED)

    def launch_product(self):
        result = design_product(self.state, self.product_name, self.selected_arch, self.selected_node, self.selected_memory, self.clock_speed)
        self.handle_result(result)
        if result[0]:
            self.product_name = f"{self.state.company_name[:10]} {len(self.state.products)+100}"
            self.state.active_tab = "factory"

    def draw_factory(self):
        self.page_heading("Üretim Fabrikası", "Wafer, paketleme ve montaj kapasiteni planla. Fazla üretim nakit akışını zorlayabilir.", ("FABRİKAYI BÜYÜT", self.factory_upgrade))
        r = self.content
        y = r.y+70
        gap = 12
        kw = (r.width-2*gap)//3
        kpis = [("Aylık kapasite", f"{self.state.factory_capacity:,} adet", f"Seviye {self.state.factory_level}", BLUE, "▤"), ("Planlanan üretim", f"{sum(p.production_target for p in self.state.products):,} adet", "Kapasite üstü planlar ölçeklenir", YELLOW, "⚙"), ("Stoktaki ürün", f"{sum(p.inventory for p in self.state.products):,} adet", "Satılana kadar sermaye bağlı", ACCENT, "□")]
        for i, k in enumerate(kpis): self.kpi((r.x+i*(kw+gap), y, kw, 100), *k[:3], k[3], k[4])
        panel = pygame.Rect(r.x, y+116, r.width, r.bottom-(y+116)-5)
        self.p.panel(panel, "Üretim planları", "Her ürün için aylık hedef belirle · Fabrika kapasitesi ürünlere paylaştırılır", ACCENT)
        if not self.state.products:
            self.p.label("Üretim yapabilmek için önce GPU Laboratuvarı'nda bir ürün tasarla.", panel.x+20, panel.y+77, 14, MUTED)
            self.p.button((panel.x+20, panel.y+112, 200, 40), "GPU Laboratuvarına git", lambda: setattr(self.state, "active_tab", "lab"), True, "primary", 12)
        else:
            for i, product in enumerate(self.state.products):
                yy = panel.y+66+i*105
                if yy+91>panel.bottom-10: break
                self.p.rounded((panel.x+16, yy, panel.width-32, 91), SURFACE_2, 11, BORDER)
                self.draw_gpu_art((panel.x+28, yy+11, 92, 68), product.benchmark)
                self.p.label(product.name, panel.x+132, yy+12, 14, TEXT, True)
                self.p.label(f"{product.node} · {product.memory} · {product.benchmark:.0f} perf", panel.x+132, yy+35, 10, MUTED)
                self.p.label(f"Stok: {product.inventory:,}  |  Maliyet: {money(product.unit_cost)}/adet", panel.x+132, yy+57, 10, MUTED)
                px = panel.right-224
                self.p.label(f"{product.production_target:,} / ay", px+104, yy+16, 12, ACCENT, True, "midtop")
                self.p.button((px, yy+12, 42, 32), "−500", lambda idx=i: self.handle_result(set_production(self.state, idx, -500)), True, "outline", 10)
                self.p.button((px+49, yy+12, 48, 32), "+500", lambda idx=i: self.handle_result(set_production(self.state, idx, 500)), True, "selected", 10)
                self.p.button((px+104, yy+49, 104, 27), "Pazarı gör →", lambda: setattr(self.state, "active_tab", "market"), True, "outline", 10)
                self.p.label(f"Tahmini üretim gideri: {money(product.production_target*product.unit_cost)}", px, yy+57, 9, YELLOW, False)

    def factory_upgrade(self): self.handle_result(upgrade_factory(self.state))

    def draw_market(self):
        self.page_heading("Pazar & Satış", "Fiyat konumlandırması, müşteri talebi ve rakip ürünlerle rekabet et.")
        r = self.content
        y = r.y+68
        leftw = int(r.width*.59)
        left = pygame.Rect(r.x, y, leftw, r.bottom-y-4)
        right = pygame.Rect(left.right+12, y, r.right-left.right-12, left.height)
        self.p.panel(left, "Kendi ürünlerin", "Fiyat · stok · satış performansı", ACCENT)
        if not self.state.products:
            self.p.label("Piyasada ürünün yok.", left.x+20, left.y+72, 14, TEXT, True)
            self.p.button((left.x+20, left.y+107, 190, 40), "Ürün tasarla", lambda: setattr(self.state, "active_tab", "lab"), True, "primary", 12)
        else:
            for i, p in enumerate(self.state.products):
                yy = left.y+66+i*134
                if yy+120 > left.bottom-8: break
                self.p.rounded((left.x+15, yy, left.width-30, 120), SURFACE_2, 11, BORDER)
                self.p.label(p.name, left.x+29, yy+13, 14, TEXT, True, max_width=left.width-60)
                self.p.label(f"Performans {p.benchmark:.0f}  ·  {p.node}  ·  {p.memory}", left.x+29, yy+37, 10, MUTED)
                self.p.label(f"{money(p.price)}", left.x+29, yy+64, 21, ACCENT, True)
                self.p.label(f"Stok {p.inventory:,}  ·  Son ay {p.last_month_sales:,} satıldı", left.x+29, yy+91, 10, MUTED)
                bx = left.right-176
                self.p.button((bx, yy+60, 52, 30), "−$25", lambda idx=i: self.handle_result(set_price(self.state, idx, -25)), True, "outline", 10)
                self.p.button((bx+59, yy+60, 52, 30), "+$25", lambda idx=i: self.handle_result(set_price(self.state, idx, 25)), True, "selected", 10)
                self.p.button((bx, yy+95, 111, 19), "Fiyatı düşür −$5", lambda idx=i: self.handle_result(set_price(self.state, idx, -5)), True, "outline", 8)
        self.p.panel(right, "Rakip analizi", "Tahmini pazar konumu", YELLOW)
        rivals = competitor_snapshot(self.state)
        rowy = right.y+67
        for i, rival in enumerate(rivals):
            yy = rowy+i*91
            if yy+80 > right.bottom-100: break
            self.p.rounded((right.x+14, yy, right.width-28, 77), SURFACE_2, 10, BORDER)
            self.p.icon_badge((right.x+25, yy+17, 38, 38), f"{i+1}", [ACCENT, RED, BLUE, PURPLE][i])
            self.p.label(rival["name"], right.x+74, yy+12, 12, TEXT, True, max_width=right.width-100)
            self.p.label(f"{rival['focus']}  ·  {rival['score']} perf", right.x+74, yy+33, 10, MUTED)
            self.p.label(f"Fiyat {money(rival['price'])}", right.x+74, yy+51, 10, YELLOW, True)
        summary_y = right.bottom-84
        self.p.rounded((right.x+14, summary_y, right.width-28, 68), (27, 43, 47), 9, (43, 79, 77))
        self.p.label("STRATEJİ İPUCU", right.x+26, summary_y+11, 10, ACCENT, True)
        self.p.paragraph("Yüksek performans tek başına yetmez. Stok, fiyat ve marka itibarı satış miktarını birlikte belirler.", pygame.Rect(right.x+26, summary_y+30, right.width-52, 34), 10, MUTED, 2, 2)

    def draw_research(self):
        self.page_heading("AR-GE Merkezi", "Araştırma puanlarını kullanarak yeni mimari, üretim düğümü, bellek ve sürücü teknolojileri aç.")
        r = self.content
        y = r.y+70
        self.p.rounded((r.x, y, r.width, 114), SURFACE, 14, BORDER)
        self.p.icon_badge((r.x+20, y+23, 56, 56), "⌘", PURPLE)
        self.p.label("Araştırma laboratuvarı", r.x+91, y+21, 17, TEXT, True)
        self.p.label(f"Mevcut araştırma puanı: {self.state.research_points:.0f} RP", r.x+91, y+48, 12, ACCENT, True)
        gain = 7+self.state.researchers*4+self.state.engineers*.6
        self.p.label(f"Üretim: yaklaşık +{gain:.0f} RP / ay", r.x+91, y+70, 11, MUTED)
        self.p.meter((r.right-255, y+45, 220, 9), self.state.research_points%100, 100, PURPLE)
        self.p.label("100 RP ölçeği", r.right-255, y+61, 10, MUTED)
        gap = 12
        cardw = (r.width-gap)//2
        cardh = (r.bottom-(y+130)-gap)//2
        options = [
            ("architecture", "Mimari araştırması", "Yeni işlem birimleri ve grafik özellikleri.", ACCENT, self.state.architecture_tier, ARCHITECTURES, "architecture"),
            ("node", "Üretim düğümü", "Daha yoğun kalıp ve daha düşük birim maliyeti.", BLUE, self.state.process_tier, PROCESS_NODES, "node"),
            ("memory", "Bellek teknolojisi", "Bant genişliği ve ürün segmentini güçlendir.", PURPLE, self.state.memory_tier, MEMORIES, "memory"),
            ("drivers", "Sürücü optimizasyonu", "Mevcut ürünleri yazılımla daha hızlı ve verimli yap.", YELLOW, self.state.driver_level, None, "drivers"),
        ]
        for i, (kind, title, desc, color, level, items, key) in enumerate(options):
            col, row = i%2, i//2
            card = pygame.Rect(r.x+col*(cardw+gap), y+130+row*(cardh+gap), cardw, cardh)
            self.p.panel(card, title, desc, color)
            self.p.label(f"SEVİYE {level}", card.x+20, card.y+71, 11, color, True)
            if items:
                nxt = items[level+1] if level+1 < len(items) else None
                if nxt:
                    req = f"Sonraki: {nxt.name} · {nxt.year}+"
                    points = 18+(level+1)*12
                    cost = 160_000+(level+1)*140_000
                    available = self.state.year >= nxt.year
                else:
                    req, points, cost, available = "Teknoloji ağacının son seviyesi", 9999, 999999999, False
            else:
                nxt = None
                req = f"Mevcut sürücü optimizasyonu: seviye {level}"
                points = 24+level*8
                cost = 180_000+level*125_000
                available = level < 8
            self.p.label(req, card.x+20, card.y+98, 12, TEXT if available else MUTED, True, max_width=card.width-40)
            self.p.label(f"Maliyet {money(cost)}  ·  {points} RP", card.x+20, card.y+126, 11, MUTED)
            self.p.button((card.x+20, card.bottom-52, card.width-40, 36), "ARAŞTIRMAYI TAMAMLA  →", lambda kind=kind: self.handle_result(invest_research(self.state, kind)), available, "primary", 12)
            if nxt and self.state.year < nxt.year:
                self.p.label(f"Tarihsel kilit: {nxt.year} yılında açılır", card.x+20, card.bottom-70, 10, RED)

    def draw_team(self):
        self.page_heading("Ekip & Marka", "İnsan kaynağı, pazarlama yatırımı ve şirket kimliği uzun vadeli rekabet gücünü belirler.")
        r = self.content
        y = r.y+70
        roles = [("Mühendisler", self.state.engineers, "Ürün geliştirme ve üretim verimi", BLUE, "engineer", "$72K işe alım", 2),
                 ("Araştırmacılar", self.state.researchers, "Aylık AR-GE puanını artırır", PURPLE, "researcher", "$92K işe alım", 1),
                 ("Pazarlamacılar", self.state.marketers, "Marka ve kampanya etkinliği", YELLOW, "marketer", "$58K işe alım", 1)]
        gap = 12
        cw = (r.width-2*gap)//3
        for i, (title, count, desc, color, role, hire, n) in enumerate(roles):
            x = r.x+i*(cw+gap)
            card = pygame.Rect(x, y, cw, 202)
            self.p.panel(card, title, desc, color)
            self.p.label(f"{count:02d}", card.x+20, card.y+89, 34, TEXT, True)
            self.p.label("çalışan", card.x+70, card.y+105, 11, MUTED)
            self.p.meter((card.x+20, card.y+142, card.width-40, 6), count, 30, color)
            self.p.button((card.x+20, card.bottom-42, card.width-40, 30), f"İşe al · {hire}", lambda role=role: self.handle_result(hire_staff(self.state, role)), True, "selected", 11)
        brand_y = y+218
        left = pygame.Rect(r.x, brand_y, int(r.width*.55), r.bottom-brand_y-5)
        right = pygame.Rect(left.right+12, brand_y, r.right-left.right-12, left.height)
        self.p.panel(left, "Marka kimliği", "Kurumsal isim ve itibar", ACCENT)
        self.p.label("ŞİRKET ADI", left.x+20, left.y+70, 10, MUTED, True)
        self.p.label(self.state.company_name, left.x+20, left.y+93, 20, TEXT, True, max_width=left.width-40)
        self.p.button((left.x+20, left.y+130, left.width-40, 38), "Şirket adını değiştir", self.open_rename, True, "outline", 12)
        self.p.label("MARKA İTİBARI", left.x+20, left.y+189, 10, MUTED, True)
        self.p.label(f"{self.state.reputation}/100", left.right-20, left.y+189, 12, ACCENT, True, "topright")
        self.p.meter((left.x+20, left.y+213, left.width-40, 8), self.state.reputation, 100, ACCENT)
        self.p.paragraph("Ürün lansmanları ve başarılı sürücü güncellemeleri itibarı yükseltir. Sorunlar ve negatif nakit akışı ise güveni azaltabilir.", pygame.Rect(left.x+20, left.y+236, left.width-40, 51), 11, MUTED, 3, 3)
        self.p.panel(right, "Pazarlama bütçesi", "Her ay otomatik harcanan tutar", YELLOW)
        self.p.label(money(self.state.marketing_budget), right.x+22, right.y+73, 25, TEXT, True)
        self.p.label("Aylık harcama", right.x+22, right.y+105, 11, MUTED)
        self.p.button((right.x+22, right.y+135, 70, 33), "−$10K", lambda: setattr(self.state, "marketing_budget", max(0, self.state.marketing_budget-10_000)), True, "outline", 11)
        self.p.button((right.x+101, right.y+135, 70, 33), "+$10K", lambda: setattr(self.state, "marketing_budget", min(500_000, self.state.marketing_budget+10_000)), True, "selected", 11)
        self.p.divider(right.x+20, right.y+187, right.right-20)
        self.p.label("Tek seferlik kampanya", right.x+22, right.y+204, 12, TEXT, True)
        self.p.paragraph("İtibarı artırır ve gelecek ay için talep bonusu sağlayabilir.", pygame.Rect(right.x+22, right.y+225, right.width-44, 35), 10, MUTED, 2, 2)
        self.p.button((right.x+22, right.bottom-45, right.width-44, 31), "KAMPANYA BAŞLAT", lambda: self.handle_result(run_marketing_campaign(self.state)), True, "gold", 11)

    def open_rename(self):
        self.dialog = "rename"
        self.dialog_input = self.state.company_name
        self.focused_input = "dialog"

    def draw_finance(self):
        self.page_heading("Finans Raporu", "Gelir tablosu, üretim harcamaları ve nakit bakiyesini değerlendir.", ("KAYDI KAYDET", self.save_current, True, "outline"))
        r = self.content
        y = r.y+70
        gap = 12
        kw = (r.width-3*gap)//4
        stats = [("Toplam gelir", money(self.state.total_revenue), "Tüm dönemler", ACCENT, "$"), ("Son ay gelir", money(self.state.last_month_revenue), "Brüt satış", GREEN, "↗"), ("Son ay gider", money(self.state.last_month_expenses), "Üretim + işletme", YELLOW, "−"), ("Birim başı satış", f"{self.state.total_sales:,}", "Toplam satılan adet", BLUE, "□")]
        for i, item in enumerate(stats): self.kpi((r.x+i*(kw+gap), y, kw, 100), *item[:3], item[3], item[4])
        cy = y+116
        chart_h = int((r.bottom-cy-10)*.52)
        chart = pygame.Rect(r.x, cy, r.width, chart_h)
        self.p.panel(chart, "Aylık nakit akışı", "Son 12 dönem · gelir ve gider karşılaştırması", ACCENT)
        self.draw_chart(pygame.Rect(chart.x+23, chart.y+69, chart.width-46, chart.height-104), "revenue", "expenses")
        table = pygame.Rect(r.x, chart.bottom+12, r.width, r.bottom-chart.bottom-12)
        self.p.panel(table, "Dönem kayıtları", "En son mali raporlar", BLUE)
        rows = self.state.history[-5:][::-1]
        headers = [("DÖNEM", .04), ("GELİR", .31), ("GİDER", .52), ("NET SONUÇ", .73), ("ADET", .92)]
        hy = table.y+57
        for label, pos in headers: self.p.label(label, table.x+int(table.width*pos), hy, 9, MUTED, True)
        self.p.divider(table.x+18, hy+19, table.right-18)
        for i, row in enumerate(rows):
            yy = hy+27+i*24
            values = [row.get("date", "—"), money(row.get("revenue", 0)), money(row.get("expenses", 0)), money(row.get("profit", 0)), f"{row.get('sales', 0):,}"]
            for (label, pos), val in zip(headers, values):
                col = (GREEN if float(row.get("profit", 0))>=0 else RED) if label=="NET SONUÇ" else TEXT
                self.p.label(val, table.x+int(table.width*pos), yy, 10, col, label=="NET SONUÇ")

    def advance_turn(self):
        report = advance_month(self.state, self.rng)
        self.last_report = report
        self._sync_technology_selection()
        self.notify(f"{report['date']} kapandı · net {money(report['profit'])} · {report['sales']:,} satış", ACCENT if report['profit']>=0 else RED)

    def save_current(self):
        try:
            path = save_game(self.state)
            self.notify(f"Kayıt alındı: {path}")
        except OSError as exc:
            self.notify(f"Kayıt başarısız: {exc}", RED)

    def draw_toast(self):
        w, h = self.screen.get_size()
        msg = self.toast
        font = self.p.font(12, True)
        txt = font.render(msg, True, TEXT)
        rect = pygame.Rect(0, 0, min(w-40, max(270, txt.get_width()+36)), 47)
        rect.topright = (w-22, h-22)
        self.p.rounded(rect, (28, 45, 55), 11, getattr(self, "toast_color", ACCENT))
        self.p.label(msg, rect.x+16, rect.centery, 12, TEXT, True, "midleft", rect.width-30)

    def draw_dialog(self):
        w, h = self.screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(w//2-235, h//2-125, 470, 250)
        self.p.rounded(rect, SURFACE, 16, BORDER, 2)
        self.p.label("Şirket adını değiştir", rect.x+24, rect.y+24, 19, TEXT, True)
        self.p.label("Yeni isim, arayüzde ve kayıt dosyanda kullanılacak.", rect.x+24, rect.y+56, 12, MUTED)
        entry = pygame.Rect(rect.x+24, rect.y+100, rect.width-48, 46)
        self.p.rounded(entry, SURFACE_2, 9, ACCENT if self.focused_input=="dialog" else BORDER)
        self.p.label(self.dialog_input+ ("▏" if self.focused_input=="dialog" else ""), entry.x+13, entry.centery, 14, TEXT, False, "midleft")
        self.dialog_input_rect = entry
        save = pygame.Rect(rect.right-219, rect.bottom-58, 105, 36)
        cancel = pygame.Rect(rect.right-103, rect.bottom-58, 79, 36)
        self.p.button(save, "Kaydet", lambda: self.commit_rename(), True, "primary", 12)
        self.p.button(cancel, "İptal", lambda: self.close_dialog(), True, "outline", 12)
        self.dialog_save_rect, self.dialog_cancel_rect = save, cancel

    def commit_rename(self):
        new_name = " ".join(self.dialog_input.strip().split())[:28]
        if new_name:
            self.state.company_name = new_name
            self.notify(f"Şirket adı güncellendi: {new_name}")
        self.close_dialog()

    def close_dialog(self):
        self.dialog = None
        self.focused_input = None


import pygame

WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)

class UIButton:
    def __init__(self, rect, text, font, callback=None,
                 bg_color=(245, 245, 245, 255), fg_color=(20, 20, 20),
                 accent_color=(66, 133, 244), radius=10, enabled=True,
                 with_background=True,                 # << nouveau
                 show_border_when_no_bg=False,         # << optionnel
                 underline_on_hover=True):             # << optionnel
        """
        rect: (x, y, w, h)
        text: libellé du bouton
        font: pygame.font.Font
        callback: fonction appelée au clic
        bg_color: couleur de base du bouton (alpha supporté)
        fg_color: couleur du texte
        accent_color: couleur d’accent (hover/contour)
        radius: arrondi des coins
        enabled: état actif/inactif
        with_background: True = bouton plein (fond/ombre/contour), False = texte seul
        show_border_when_no_bg: dessine un contour même sans fond
        underline_on_hover: souligner le texte au survol si pas de fond
        """
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback

        self.bg_color = bg_color
        self.fg_color = fg_color
        self.accent_color = accent_color
        self.radius = radius
        self.enabled = enabled

        self.with_background = with_background
        self.show_border_when_no_bg = show_border_when_no_bg
        self.underline_on_hover = underline_on_hover

        self.hover = False
        self.pressed = False
        self.focused = False

        self.text_surf = self.font.render(self.text, True, self.fg_color)

        # Curseur
        self._hand_cursor = False

        # Animation (0..1) pour hover
        self.hover_t = 0.0

    # -------- helpers --------
    def set_label(self, label):
        self.text = label
        self.text_surf = self.font.render(self.text, True, self.fg_color)
    def _lerp(self, a, b, t): return a + (b - a) * t

    def _color_lerp(self, c1, c2, t):
        return (
            int(self._lerp(c1[0], c2[0], t)),
            int(self._lerp(c1[1], c2[1], t)),
            int(self._lerp(c1[2], c2[2], t))
        )

    def _draw_rounded_rect(self, surface, rect, color, radius, width=0):
        pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

    def _draw_gradient_rect(self, surface, rect, color_top, color_bottom, radius):
        grad = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for y in range(rect.height):
            t = y / max(1, rect.height - 1)
            col = self._color_lerp(color_top, color_bottom, t)
            pygame.draw.line(grad, (*col, 255), (0, y), (rect.width, y))
        mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        self._draw_rounded_rect(mask, mask.get_rect(), (255, 255, 255, 255), radius)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(grad, rect.topleft)

    # -------- draw --------
    def draw(self, screen):
        # Animation hover (lissage)
        target = 1.0 if (self.hover and self.enabled) else 0.0
        self.hover_t = self._lerp(self.hover_t, target, 0.2)

        # Décalage si pressé
        offset = (0, 1) if (self.pressed and self.enabled) else (0, 0)

        # Surface du bouton (alpha propre)
        btn_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        if self.with_background:
            # Ombre douce
            shadow_offset = 4
            shadow_rect = self.rect.move(shadow_offset, shadow_offset)
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            shadow_color = (0, 0, 0, int(60 + 60 * (1 - self.hover_t)))
            self._draw_rounded_rect(shadow_surf, shadow_surf.get_rect(), shadow_color, self.radius + 1)
            screen.blit(shadow_surf, shadow_rect.topleft)

            # Couleurs de base + hover
            base = self.bg_color
            hover_color = self._color_lerp(base, (255, 255, 255), 0.12)  # éclaircissement
            bg = self._color_lerp(base, hover_color, self.hover_t)

            # Dégradé subtil
            top = self._color_lerp(bg, (255, 255, 255), 0.06)
            bottom = self._color_lerp(bg, (0, 0, 0), 0.06)

            # Dégradé + contour
            self._draw_gradient_rect(btn_surf, btn_surf.get_rect(), top, bottom, self.radius)
            border_col = self._color_lerp((0, 0, 0), self.accent_color, 0.15 if self.hover_t > 0.05 else 0.0)
            self._draw_rounded_rect(btn_surf, btn_surf.get_rect(), border_col, self.radius, width=2)
        else:
            # Pas de fond : optionnellement un contour discret
            if self.show_border_when_no_bg:
                self._draw_rounded_rect(btn_surf, btn_surf.get_rect(), (0, 0, 0, 255), self.radius, width=2)

        # État disabled (désaturé)
        text_color = self.fg_color
        if not self.enabled:
            if self.with_background:
                btn_surf.fill((200, 200, 200, 120), special_flags=pygame.BLEND_RGBA_MULT)
            text_color = (120, 120, 120)

        # Texte (recalculer pour la couleur finale)
        self.text_surf = self.font.render(self.text, True, text_color)
        text_rect = self.text_surf.get_rect(center=(self.rect.width // 2, self.rect.height // 2 + (1 if self.pressed else 0)))

        # Dessin final (avec offset pressé)
        screen.blit(btn_surf, (self.rect.x + offset[0], self.rect.y + offset[1]))
        screen.blit(self.text_surf, (self.rect.x + text_rect.x + offset[0],
                                      self.rect.y + text_rect.y + offset[1]))

        # Si pas de fond : soulignement au survol (affordance)
        if self.underline_on_hover and self.hover and not self.with_background:
            underline_y = self.rect.y + text_rect.y + text_rect.height + offset[1] + 2
            start_x = self.rect.x + text_rect.x
            end_x = start_x + text_rect.width
            pygame.draw.line(screen, self.accent_color, (start_x, underline_y), (end_x, underline_y), 2)

    # -------- events --------
    def handle_event(self, event):
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
            # curseur main
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if self.hover else pygame.SYSTEM_CURSOR_ARROW)
                self._hand_cursor = self.hover
            except Exception:
                pass

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                self.focused = True
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self.pressed
            self.pressed = False
            if was_pressed and self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True

        return False

    # -------- utilitaires --------
    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self.hover = False
            self.pressed = False

    def set_background(self, enabled: bool):
        """Activer/désactiver le fond du bouton à la volée."""
        self.with_background = enabled




class UIDropdown:
    def __init__(self, rect, options, font, on_select=None,
                 label="Choisir Partition",
                 radius=10,
                 bg_color=(245, 245, 245),
                 fg_color=(20, 20, 20),
                 accent_color=(66, 133, 244),
                 option_bg=(235, 235, 235),
                 option_hover=(220, 230, 255),
                 max_visible_options=6):
        """
        rect: (x, y, w, h) -> bouton principal (place inchangée)
        options: liste de chaînes
        font: pygame.font.Font
        on_select: callback(option)
        label: texte sur le bouton
        radius: arrondi des coins
        max_visible_options: nb de lignes visibles (scroll au-delà)
        """
        self.rect = pygame.Rect(rect)
        self.options = options[:] if options else ["Aucune partition"]
        self.font = font
        self.on_select = on_select
        self.label = label

        self.open = False
        self.selected = self.options[0]

        self.radius = radius
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.accent_color = accent_color
        self.option_bg = option_bg
        self.option_hover = option_hover

        self.option_height = self.rect.height
        self.max_visible_options = max(1, int(max_visible_options))
        self.scroll = 0
        self.hover_index = None

        # états pour l’animation
        self.hover_btn = False
        self.pressed_btn = False
        self._hover_t = 0.0  # animation hover

    # ---------- helpers ----------
    def _lerp(self, a, b, t): return a + (b - a) * t

    def _color_lerp(self, c1, c2, t):
        return (int(self._lerp(c1[0], c2[0], t)),
                int(self._lerp(c1[1], c2[1], t)),
                int(self._lerp(c1[2], c2[2], t)))

    def _rounded_rect(self, surf, rect, color, radius, width=0):
        pygame.draw.rect(surf, color, rect, width=width, border_radius=radius)

    def _gradient_rect(self, surf, rect, top_col, bottom_col, radius):
        grad = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for y in range(rect.height):
            t = y / max(1, rect.height - 1)
            col = self._color_lerp(top_col, bottom_col, t)
            pygame.draw.line(grad, (*col, 255), (0, y), (rect.width, y))
        mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        self._rounded_rect(mask, mask.get_rect(), (255, 255, 255, 255), radius)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(grad, rect.topleft)

    def _draw_shadow(self, screen, rect, radius, alpha=90, offset=(4, 4)):
        srect = rect.move(offset)
        sh = pygame.Surface((srect.width, srect.height), pygame.SRCALPHA)
        self._rounded_rect(sh, sh.get_rect(), (0, 0, 0, alpha), radius + 1)
        screen.blit(sh, srect.topleft)

    def _caret(self, screen, center, open):
        # triangle ▼ (fermé) / ▲ (ouvert)
        x, y = center
        if open:
            points = [(x - 6, y + 3), (x + 6, y + 3), (x, y - 3)]  # ▲ renversé
        else:
            points = [(x - 6, y - 3), (x + 6, y - 3), (x, y + 3)]  # ▼
        pygame.draw.polygon(screen, self.fg_color, points)

    # ---------- drawing ----------
    def draw(self, screen):
        # animation hover
        target = 1.0 if self.hover_btn else 0.0
        self._hover_t = self._lerp(self._hover_t, target, 0.2)

        # --- bouton principal ---
        self._draw_shadow(screen, self.rect, self.radius, alpha=70)
        btn_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        base = self.bg_color
        hover_col = self._color_lerp(base, (255, 255, 255), 0.12)
        bg = self._color_lerp(base, hover_col, self._hover_t)
        top = self._color_lerp(bg, (255, 255, 255), 0.06)
        bottom = self._color_lerp(bg, (0, 0, 0), 0.06)
        self._gradient_rect(btn_surf, btn_surf.get_rect(), top, bottom, self.radius)

        border_col = self._color_lerp((0, 0, 0), self.accent_color, 0.15 if self._hover_t > 0.05 else 0.0)
        self._rounded_rect(btn_surf, btn_surf.get_rect(), border_col, self.radius, width=2)

        # label du bouton
        label_surf = self.font.render(self.label, True, self.fg_color)
        label_rect = label_surf.get_rect(center=(self.rect.width // 2 - 10, self.rect.height // 2))
        btn_surf.blit(label_surf, label_rect)

        # caret (ouvre/ferme)
        caret_center = (self.rect.width - 18, self.rect.height // 2)
        self._caret(btn_surf, caret_center, self.open)
        screen.blit(btn_surf, self.rect.topleft)

        # --- liste déroulante (directement sous le bouton) ---
        if self.open:
            visible = min(self.max_visible_options, len(self.options))
            list_height = visible * self.option_height
            list_rect = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, list_height)

            self._draw_shadow(screen, list_rect, self.radius, alpha=80)
            list_surf = pygame.Surface((list_rect.width, list_rect.height), pygame.SRCALPHA)

            # fond + contour
            self._rounded_rect(list_surf, list_surf.get_rect(), self.option_bg, self.radius)
            self._rounded_rect(list_surf, list_surf.get_rect(), (0, 0, 0), self.radius, width=2)

            # items visibles (scroll si besoin)
            start = self.scroll
            end = min(start + visible, len(self.options))

            self.hover_index = None
            mouse_x, mouse_y = pygame.mouse.get_pos()

            for i, idx in enumerate(range(start, end)):
                row_rect = pygame.Rect(0, i * self.option_height, list_rect.width, self.option_height)
                absolute_row = pygame.Rect(list_rect.x, list_rect.y + row_rect.y, row_rect.width, row_rect.height)
                is_hover = absolute_row.collidepoint(mouse_x, mouse_y)
                if is_hover:
                    pygame.draw.rect(list_surf, self.option_hover, row_rect,
                                     border_radius=self.radius if i in (0, visible - 1) else 0)
                    self.hover_index = idx

                # séparateur discret
                if i > 0:
                    pygame.draw.line(list_surf, (200, 200, 200),
                                     (10, row_rect.y), (list_rect.width - 10, row_rect.y), 1)

                # label option
                opt = self.options[idx]
                opt_surf = self.font.render(opt, True, self.fg_color)
                opt_rect = opt_surf.get_rect()
                opt_rect.x = 12
                opt_rect.centery = row_rect.centery
                list_surf.blit(opt_surf, opt_rect)

                # marque sélection (●)
                if opt == self.selected:
                    dot = self.font.render("●", True, self.accent_color)
                    drect = dot.get_rect()
                    drect.right = list_rect.width - 10
                    drect.centery = row_rect.centery
                    list_surf.blit(dot, drect)

            screen.blit(list_surf, list_rect.topleft)

            # barre de scroll si nécessaire
            if len(self.options) > visible:
                bar_w = 4
                rail_rect = pygame.Rect(list_rect.right - bar_w - 2, list_rect.y + 4, bar_w, list_rect.height - 8)
                pygame.draw.rect(screen, (200, 200, 200), rail_rect, border_radius=3)
                frac = self.scroll / max(1, len(self.options) - visible)
                thumb_h = max(14, int(rail_rect.height * (visible / len(self.options))))
                thumb_y = rail_rect.y + int((rail_rect.height - thumb_h) * frac)
                thumb_rect = pygame.Rect(rail_rect.x, thumb_y, bar_w, thumb_h)
                pygame.draw.rect(screen, self.accent_color, thumb_rect, border_radius=3)

    # ---------- events ----------
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_btn = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # clic sur le bouton
            if self.rect.collidepoint(event.pos):
                self.pressed_btn = True
                return True

            # clic dans la liste ouverte
            if self.open:
                visible = min(self.max_visible_options, len(self.options))
                list_height = visible * self.option_height
                list_rect = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, list_height)

                if list_rect.collidepoint(event.pos):
                    rel_y = event.pos[1] - list_rect.y
                    row = int(rel_y // self.option_height)
                    idx = self.scroll + row
                    if 0 <= idx < len(self.options):
                        self.selected = self.options[idx]
                        self.open = False
                        if self.on_select:
                            self.on_select(self.selected)
                        return True
                else:
                    # clic ailleurs -> fermer
                    self.open = False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed_btn:
                self.pressed_btn = False
                if self.rect.collidepoint(event.pos):
                    self.open = not self.open
                    return True

        # molette de souris pour scroll
        if event.type == pygame.MOUSEWHEEL and self.open:
            visible = min(self.max_visible_options, len(self.options))
            mx, my = pygame.mouse.get_pos()
            list_rect = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, visible * self.option_height)
            if list_rect.collidepoint((mx, my)):
                max_scroll = max(0, len(self.options) - visible)
                self.scroll = max(0, min(max_scroll, self.scroll - event.y))  # wheel up = +y
                return True

        return False


import pygame
import time

class GameDisplay:

    def __init__(self, width=800, height=600):

        pygame.init()

        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height))

        pygame.display.set_caption("MoveJoy")

        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("Arial", 80, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 36)

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

    def clear(self):

        self.screen.fill((30, 30, 30))

    def draw_center_text(self, text, font, color=(255, 255, 255)):

        rendered = font.render(text, True, color)

        rect = rendered.get_rect(
            center=(self.width // 2, self.height // 2)
        )

        self.screen.blit(rendered, rect)

    def show_message(self, message, duration=1.5):

        start = time.time()

        while time.time() - start < duration:

            self.handle_events()

            self.clear()

            self.draw_center_text(
                message,
                self.font_small
            )

            pygame.display.flip()

            self.clock.tick(60)

    def show_action(self, action, duration=2):

        start = time.time()

        while time.time() - start < duration:

            self.handle_events()

            self.clear()

            self.draw_center_text(
                action,
                self.font_big
            )

            pygame.display.flip()

            self.clock.tick(60)

    def close(self):

        pygame.quit()
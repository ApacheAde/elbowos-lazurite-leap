#!/usr/bin/env python3
"""Lazurite Leap — neon frogger-style tide hopper arcade for ElbowOS. Python 3 + pygame.
Featured: https://x.com/ElbowOS
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/LAZURITE_LEAP_ElbowOS.mp4")
TITLE, HANDLE = "LAZURITE LEAP", "x.com/ElbowOS"

# Palette: deep indigo, electric cyan, magenta, gold, lime
BG = (8, 4, 32)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 180)
GOLD = (255, 220, 40)
LIME = (120, 255, 80)
WHITE = (240, 245, 255)
DARK = (20, 10, 50)
PLATFORM = (40, 180, 255)
HAZARD = (255, 60, 100)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("arial", 72, bold=True)
        self.font_med = pygame.font.SysFont("arial", 42, bold=True)
        self.font_small = pygame.font.SysFont("arial", 28)
        self.reset()

    def reset(self):
        self.frog_y = H - 180
        self.frog_x = W // 2
        self.vx = 0
        self.score = 0
        self.lives = 3
        self.platforms = []
        self.gems = []
        self.hazards = []
        self.scroll = 0
        self.time = 0
        self.hop_cooldown = 0
        # Generate initial platforms
        for i in range(8):
            self.spawn_row(i * 180)

    def spawn_row(self, y_offset):
        y = H - 200 - y_offset
        direction = 1 if random.random() > 0.5 else -1
        speed = random.uniform(2.5, 6.0) * direction
        length = random.randint(280, 480)
        x = random.randint(50, W - length - 50)
        self.platforms.append({"x": x, "y": y, "w": length, "h": 28, "speed": speed, "dir": direction})
        if random.random() > 0.4:
            gx = x + random.randint(40, length - 40)
            self.gems.append({"x": gx, "y": y - 40, "r": 18, "collected": False})
        if random.random() > 0.6:
            hx = random.randint(80, W - 80)
            self.hazards.append({"x": hx, "y": y - 20, "r": 22})

    def update(self, auto=False):
        self.time += 1
        if self.hop_cooldown > 0:
            self.hop_cooldown -= 1

        # Move platforms
        for p in self.platforms:
            p["x"] += p["speed"]
            if p["x"] > W + 100:
                p["x"] = -p["w"] - 50
            elif p["x"] < -p["w"] - 100:
                p["x"] = W + 50

        # Auto or player hop
        if auto and self.hop_cooldown == 0:
            # Find a platform above
            target = None
            for p in self.platforms:
                if self.frog_y - 160 < p["y"] < self.frog_y - 40:
                    if abs((p["x"] + p["w"]/2) - self.frog_x) < 200:
                        target = p
                        break
            if target:
                self.frog_x = max(40, min(W-40, target["x"] + target["w"]//2 + random.randint(-30, 30)))
                self.frog_y -= 150
                self.score += 10
                self.hop_cooldown = 12
                # Collect gem if close
                for g in self.gems:
                    if not g["collected"] and abs(g["x"] - self.frog_x) < 50 and abs(g["y"] - self.frog_y) < 60:
                        g["collected"] = True
                        self.score += 50
            else:
                # Drift a bit
                self.frog_x += random.choice([-3, 0, 3])
                self.frog_x = max(60, min(W-60, self.frog_x))

        # Check landing
        landed = False
        for p in self.platforms:
            if abs(self.frog_y - p["y"]) < 20 and p["x"] < self.frog_x < p["x"] + p["w"]:
                landed = True
                self.frog_y = p["y"]
                break
        if not landed and self.frog_y < H - 200:
            self.frog_y += 4  # fall slowly
            if self.frog_y > H - 100:
                self.lives -= 1
                self.frog_y = H - 180
                self.frog_x = W // 2
                if self.lives <= 0:
                    self.score = max(0, self.score - 100)
                    self.lives = 3

        # Hazard collision
        for h in self.hazards:
            if abs(h["x"] - self.frog_x) < 40 and abs(h["y"] - self.frog_y) < 40:
                self.lives -= 1
                self.frog_y = H - 180
                if self.lives <= 0:
                    self.lives = 3

        # Scroll platforms down slowly for progression
        if self.time % 8 == 0:
            for p in self.platforms:
                p["y"] += 1
            for g in self.gems:
                g["y"] += 1
            for h in self.hazards:
                h["y"] += 1
            if self.frog_y < H - 300:
                self.frog_y += 1

        # Remove off-screen and spawn new
        self.platforms = [p for p in self.platforms if p["y"] < H + 50]
        self.gems = [g for g in self.gems if g["y"] < H + 50]
        self.hazards = [h for h in self.hazards if h["y"] < H + 50]
        if len(self.platforms) < 7:
            self.spawn_row(self.platforms[0]["y"] - 200 if self.platforms else 0)

    def draw(self, surf):
        surf.fill(BG)
        # Stars
        for i in range(40):
            sx = (i * 137) % W
            sy = (i * 89 + self.time * 2) % H
            pygame.draw.circle(surf, (40, 30, 80), (sx, sy), 1)

        # Platforms
        for p in self.platforms:
            pygame.draw.rect(surf, PLATFORM, (int(p["x"]), int(p["y"]), p["w"], p["h"]), border_radius=8)
            pygame.draw.rect(surf, CYAN, (int(p["x"]), int(p["y"]), p["w"], p["h"]), 3, border_radius=8)

        # Gems
        for g in self.gems:
            if not g["collected"]:
                pygame.draw.circle(surf, GOLD, (int(g["x"]), int(g["y"])), g["r"])
                pygame.draw.circle(surf, WHITE, (int(g["x"]), int(g["y"])), g["r"], 2)

        # Hazards
        for h in self.hazards:
            pygame.draw.circle(surf, HAZARD, (int(h["x"]), int(h["y"])), h["r"])
            pygame.draw.circle(surf, MAGENTA, (int(h["x"]), int(h["y"])), h["r"], 3)

        # Frog
        fx, fy = int(self.frog_x), int(self.frog_y)
        pygame.draw.ellipse(surf, LIME, (fx - 28, fy - 18, 56, 36))
        pygame.draw.circle(surf, WHITE, (fx - 12, fy - 8), 6)
        pygame.draw.circle(surf, WHITE, (fx + 12, fy - 8), 6)
        pygame.draw.circle(surf, (0, 0, 0), (fx - 12, fy - 8), 3)
        pygame.draw.circle(surf, (0, 0, 0), (fx + 12, fy - 8), 3)
        # Legs
        pygame.draw.line(surf, LIME, (fx - 20, fy + 10), (fx - 35, fy + 28), 4)
        pygame.draw.line(surf, LIME, (fx + 20, fy + 10), (fx + 35, fy + 28), 4)

        # UI overlay
        title_surf = self.font_big.render(TITLE, True, CYAN)
        surf.blit(title_surf, (W//2 - title_surf.get_width()//2, 40))
        score_surf = self.font_med.render(f"SCORE: {self.score}", True, GOLD)
        surf.blit(score_surf, (40, 140))
        lives_surf = self.font_med.render(f"LIVES: {self.lives}", True, MAGENTA)
        surf.blit(lives_surf, (W - 280, 140))
        handle_surf = self.font_small.render(HANDLE, True, WHITE)
        surf.blit(handle_surf, (W//2 - handle_surf.get_width()//2, H - 80))

    def run_play(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.hop_cooldown == 0:
                        self.frog_y -= 150
                        self.hop_cooldown = 15
                        self.score += 5
                    if event.key == pygame.K_LEFT:
                        self.frog_x -= 40
                    if event.key == pygame.K_RIGHT:
                        self.frog_x += 40
                    if event.key == pygame.K_r:
                        self.reset()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.frog_x -= 6
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.frog_x += 6
            self.frog_x = max(40, min(W - 40, self.frog_x))
            self.update(auto=False)
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def run_record(self):
        total = FPS * SECS
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{W}x{H}",
            "-pix_fmt", "rgb24",
            "-r", str(FPS),
            "-i", "-",
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "20",
            "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(total):
            self.update(auto=True)
            self.draw(self.screen)
            frame = pygame.surfarray.array3d(self.screen).transpose(1, 0, 2)
            proc.stdin.write(frame.tobytes())
            if i % 30 == 0:
                print(f"Frame {i}/{total}")
        proc.stdin.close()
        proc.wait()
        print(f"Encoded {OUT}")
        pygame.quit()

if __name__ == "__main__":
    g = Game()
    if PLAY:
        g.run_play()
    else:
        g.run_record()

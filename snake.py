import asyncio
import pygame
import random
import sys
import json
import os
import colorsys
import datetime

# numpy is only used for procedural sound on desktop. Skip it entirely in the
# browser (emscripten/pygbag) build: browser audio needs a user gesture anyway,
# and importing heavy native packages there slows or stalls startup.
if sys.platform == 'emscripten':
    NUMPY_AVAILABLE = False
else:
    try:
        import numpy as np
        NUMPY_AVAILABLE = True
    except ImportError:
        NUMPY_AVAILABLE = False

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
FPS = 10

# Colors
BLACK = (20, 20, 20)
WHITE = (240, 240, 240)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
DARK_GREEN = (39, 174, 96)
YELLOW = (241, 196, 15)
GRAY = (149, 165, 166)
PURPLE = (155, 89, 182)
ORANGE = (230, 126, 34)
CYAN = (26, 188, 156)

class Snake:
    def __init__(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.reset()
        
        # Animation properties for elastic movement
        self.segment_positions = []  # For smooth interpolation
        self.target_positions = []
        self.animation_speed = 0.3
    
    def reset(self):
        self.body = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = (1, 0)  # Moving right
        self.grow = False
        self.segment_positions = [(self.grid_width // 2, self.grid_height // 2)]
        self.target_positions = [(self.grid_width // 2, self.grid_height // 2)]
    
    def move(self, wrap_around=True):
        head_x, head_y = self.body[0]
        dir_x, dir_y = self.direction
        new_head = (head_x + dir_x, head_y + dir_y)
        
        if wrap_around:
            # Wrap around walls instead of game over
            new_head = (new_head[0] % self.grid_width, new_head[1] % self.grid_height)
        else:
            # Check wall collision (game over)
            if (new_head[0] < 0 or new_head[0] >= self.grid_width or
                new_head[1] < 0 or new_head[1] >= self.grid_height):
                return False
        
        # Check self collision
        if new_head in self.body:
            return False
        
        # Update target positions for elastic animation
        self.target_positions.insert(0, new_head)
        if len(self.target_positions) > len(self.body) + 1:
            self.target_positions.pop()
        
        # Update actual body positions
        self.body.insert(0, new_head)
        if not self.grow:
            self.body.pop()
            # Also remove from segment positions
            if len(self.segment_positions) > len(self.body):
                self.segment_positions.pop()
        else:
            self.grow = False
        
        # Initialize segment positions if needed
        while len(self.segment_positions) < len(self.body):
            self.segment_positions.append(self.body[-1])
        
        return True
    
    def update_animation(self):
        # Smoothly interpolate segment positions towards targets
        for i in range(len(self.segment_positions)):
            if i < len(self.target_positions):
                target = self.target_positions[i]
                current = self.segment_positions[i]
                
                # Elastic interpolation with spring-like behavior
                dx = target[0] - current[0]
                dy = target[1] - current[1]
                
                # Apply spring force
                self.segment_positions[i] = (
                    current[0] + dx * self.animation_speed,
                    current[1] + dy * self.animation_speed
                )
    
    def change_direction(self, new_dir):
        # Prevent 180 degree turns
        if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
            self.direction = new_dir
    
    def draw(self, screen, grid_size, skin_color=None, is_rainbow=False):
        # Calculate squash and stretch based on movement
        dir_x, dir_y = self.direction
        stretch_factor = 1.0
        
        # Stretch in direction of movement
        if dir_x != 0:
            stretch_factor = 1.15  # Stretch horizontally
        elif dir_y != 0:
            stretch_factor = 1.15  # Stretch vertically
        
        for i, segment in enumerate(self.body):
            # Calculate position with smooth offset for animation
            x = segment[0] * grid_size
            y = segment[1] * grid_size
            size = grid_size - 2  # Small gap between segments
            
            # Apply squash and stretch to head
            if i == 0:
                stretch_x = size * (stretch_factor if dir_x != 0 else 0.9)
                stretch_y = size * (stretch_factor if dir_y != 0 else 0.9)
            else:
                stretch_x = size
                stretch_y = size
            
            # Determine color based on skin with smooth gradients
            if is_rainbow:
                # Rainbow effect with smooth color transitions
                hue = (i * 15 + pygame.time.get_ticks() // 20) % 360
                rgb = colorsys.hsv_to_rgb(hue / 360, 0.85, 0.85)
                segment_color = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                # Add glow effect
                glow_color = (int(rgb[0] * 255 * 0.6), int(rgb[1] * 255 * 0.6), int(rgb[2] * 255 * 0.6))
            elif skin_color:
                # Smooth gradient effect with skin color
                color_ratio = i / max(len(self.body), 1)
                # Use smooth easing function
                eased_ratio = color_ratio * color_ratio * (3 - 2 * color_ratio)  # Smoothstep
                
                r = int(skin_color[0] * (0.4 + 0.6 * eased_ratio))
                g = int(skin_color[1] * (0.4 + 0.6 * eased_ratio))
                b = int(skin_color[2] * (0.4 + 0.6 * eased_ratio))
                segment_color = (r, g, b)
                glow_color = (int(r * 0.6), int(g * 0.6), int(b * 0.6))
            else:
                # Default green gradient with smooth transitions
                color_ratio = i / max(len(self.body), 1)
                eased_ratio = color_ratio * color_ratio * (3 - 2 * color_ratio)
                
                r = int(GREEN[0] * (0.4 + 0.6 * eased_ratio))
                g = int(GREEN[1] * (0.4 + 0.6 * eased_ratio))
                b = int(GREEN[2] * (0.4 + 0.6 * eased_ratio))
                segment_color = (r, g, b)
                glow_color = (int(r * 0.6), int(g * 0.6), int(b * 0.6))
            
            # Draw glow effect for head with anti-aliasing and smooth gradient
            if i == 0:
                glow_size = int(max(size, stretch_x, stretch_y) + 12)
                glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                # Draw multiple layers for smooth glow gradient
                for radius in range(glow_size//2 + 6, glow_size//2, -1):
                    alpha = int(120 * (1 - (radius - glow_size//2) / 6))
                    pygame.draw.circle(glow_surface, (*glow_color, alpha), 
                                     (glow_size//2, glow_size//2), radius)
                screen.blit(glow_surface, (x + 1 - 6, y + 1 - 6))
            
            # Draw rounded rectangle with anti-aliasing and squash/stretch
            segment_surface = pygame.Surface((int(stretch_x) + 4, int(stretch_y) + 4), pygame.SRCALPHA)
            
            # Apply squash and stretch to the segment
            rect_x = 2
            rect_y = 2
            rect_w = stretch_x
            rect_h = stretch_y
            
            pygame.draw.rect(segment_surface, (*segment_color, 255), 
                           (rect_x, rect_y, rect_w, rect_h), border_radius=int(min(stretch_x, stretch_y)//3))
            
            # Add smooth border with gradient
            border_color = tuple(max(0, c - 25) for c in segment_color)
            pygame.draw.rect(segment_surface, (*border_color, 220), 
                           (rect_x, rect_y, rect_w, rect_h), width=2, border_radius=int(min(stretch_x, stretch_y)//3))
            
            # Add smooth highlight for 3D effect with gradient
            highlight_color = tuple(min(255, c + 60) for c in segment_color)
            highlight_rect = pygame.Rect(rect_x + 2, rect_y + 2, rect_w//3, rect_h//3)
            pygame.draw.ellipse(segment_surface, (*highlight_color, 190), highlight_rect)
            
            # Add secondary highlight for extra depth
            highlight2_color = tuple(min(255, c + 40) for c in segment_color)
            highlight2_rect = pygame.Rect(rect_x + rect_w//2, rect_y + rect_h//2, rect_w//4, rect_h//4)
            pygame.draw.ellipse(segment_surface, (*highlight2_color, 150), highlight2_rect)
            
            # Center the stretched segment
            screen.blit(segment_surface, (x + 1 - (stretch_x - size)//2, y + 1 - (stretch_y - size)//2))
            
            # Draw eyes on head with Pixar-style design and anti-aliasing
            if i == 0:
                eye_size = max(3, int(grid_size // 5))
                eye_offset = int(grid_size // 3)
                
                # Calculate eye positions based on direction with stretch
                if dir_x == 1:  # Right
                    eye1_pos = (x + grid_size - eye_offset + 2 + (stretch_x - size)//2, y + eye_offset + 2 - (stretch_y - size)//2)
                    eye2_pos = (x + grid_size - eye_offset + 2 + (stretch_x - size)//2, y + grid_size - eye_offset - 2 - (stretch_y - size)//2)
                elif dir_x == -1:  # Left
                    eye1_pos = (x + eye_offset + 2 - (stretch_x - size)//2, y + eye_offset + 2 - (stretch_y - size)//2)
                    eye2_pos = (x + eye_offset + 2 - (stretch_x - size)//2, y + grid_size - eye_offset - 2 - (stretch_y - size)//2)
                elif dir_y == -1:  # Up
                    eye1_pos = (x + eye_offset + 2 - (stretch_x - size)//2, y + eye_offset + 2 - (stretch_y - size)//2)
                    eye2_pos = (x + grid_size - eye_offset - 2 - (stretch_x - size)//2, y + eye_offset + 2 - (stretch_y - size)//2)
                else:  # Down
                    eye1_pos = (x + eye_offset + 2 - (stretch_x - size)//2, y + grid_size - eye_offset - 2 - (stretch_y - size)//2)
                    eye2_pos = (x + grid_size - eye_offset - 2 - (stretch_x - size)//2, y + grid_size - eye_offset - 2 - (stretch_y - size)//2)
                
                # Draw eye whites with anti-aliasing and gradient
                eye_surface1 = pygame.Surface((eye_size + 4, eye_size + 4), pygame.SRCALPHA)
                eye_surface2 = pygame.Surface((eye_size + 4, eye_size + 4), pygame.SRCALPHA)
                
                # Gradient for eye whites
                pygame.draw.circle(eye_surface1, (*WHITE, 255), (eye_size + 2, eye_size + 2), eye_size + 2)
                pygame.draw.circle(eye_surface2, (*WHITE, 255), (eye_size + 2, eye_size + 2), eye_size + 2)
                
                # Add subtle blue tint to eyes for depth
                pygame.draw.circle(eye_surface1, (230, 240, 255, 50), (eye_size + 2, eye_size + 2), eye_size + 1)
                pygame.draw.circle(eye_surface2, (230, 240, 255, 50), (eye_size + 2, eye_size + 2), eye_size + 1)
                
                # Draw pupils with gradient
                pupil_offset_x = dir_x * 2
                pupil_offset_y = dir_y * 2
                pygame.draw.circle(eye_surface1, (*BLACK, 255), 
                                 (eye_size + 2 + pupil_offset_x, eye_size + 2 + pupil_offset_y), 
                                 eye_size - 1)
                pygame.draw.circle(eye_surface2, (*BLACK, 255), 
                                 (eye_size + 2 + pupil_offset_x, eye_size + 2 + pupil_offset_y), 
                                 eye_size - 1)
                
                # Add eye shine with anti-aliasing
                shine_size = max(1, eye_size // 3)
                pygame.draw.circle(eye_surface1, (*WHITE, 255), 
                                 (eye_size + 2 + pupil_offset_x - 1, eye_size + 2 + pupil_offset_y - 1), 
                                 shine_size)
                pygame.draw.circle(eye_surface2, (*WHITE, 255), 
                                 (eye_size + 2 + pupil_offset_x - 1, eye_size + 2 + pupil_offset_y - 1), 
                                 shine_size)
                
                # Add secondary shine for extra detail
                shine2_size = max(1, shine_size // 2)
                pygame.draw.circle(eye_surface1, (*WHITE, 200), 
                                 (eye_size + 2 + pupil_offset_x + 1, eye_size + 2 + pupil_offset_y + 1), 
                                 shine2_size)
                pygame.draw.circle(eye_surface2, (*WHITE, 200), 
                                 (eye_size + 2 + pupil_offset_x + 1, eye_size + 2 + pupil_offset_y + 1), 
                                 shine2_size)
                
                screen.blit(eye_surface1, (eye1_pos[0] - eye_size - 2, eye1_pos[1] - eye_size - 2))
                screen.blit(eye_surface2, (eye2_pos[0] - eye_size - 2, eye2_pos[1] - eye_size - 2))

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(4, 8)
        self.speed_x = random.uniform(-4, 4)
        self.speed_y = random.uniform(-4, 4)
        self.life = 40
        self.max_life = 40
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-5, 5)
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_x *= 0.98  # Friction
        self.speed_y *= 0.98
        self.life -= 1
        self.size = max(0, self.size - 0.08)
        self.rotation += self.rotation_speed
    
    def draw(self, screen):
        if self.life > 0 and self.size > 0:
            # Calculate alpha based on life
            alpha = min(255, int((self.life / self.max_life) * 255))
            
            # Create gradient particle surface
            particle_size = int(self.size * 2)
            surface = pygame.Surface((particle_size, particle_size), pygame.SRCALPHA)
            
            # Draw multiple layers for gradient effect
            center = particle_size // 2
            
            # Outer glow
            glow_color = (*self.color, max(0, alpha - 100))
            pygame.draw.circle(surface, glow_color, (center, center), int(self.size))
            
            # Inner bright core
            core_color = (*self.color, alpha)
            pygame.draw.circle(surface, core_color, (center, center), int(self.size * 0.6))
            
            # Bright center
            bright_color = (255, 255, 255, alpha)
            pygame.draw.circle(surface, bright_color, (center, center), int(self.size * 0.3))
            
            # Rotate the particle
            rotated_surface = pygame.transform.rotate(surface, self.rotation)
            
            # Blit to screen
            screen.blit(rotated_surface, (self.x - self.size, self.y - self.size))

class Food:
    def __init__(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.position = (0, 0)
        self.food_type = 'normal'  # normal, bonus, slow
        self.timer = 0
        self.randomize_position()
    
    def randomize_position(self, snake_body=None, obstacles=None):
        if snake_body is None:
            snake_body = []
        if obstacles is None:
            obstacles = []
        
        self.position = (random.randint(0, self.grid_width - 1),
                        random.randint(0, self.grid_height - 1))
        
        # Make sure food doesn't appear on snake or obstacles
        while self.position in snake_body or self.position in obstacles:
            self.position = (random.randint(0, self.grid_width - 1),
                            random.randint(0, self.grid_height - 1))
        
        # Random food type
        rand = random.random()
        if rand < 0.1:
            self.food_type = 'bonus'
            self.timer = 100
        elif rand < 0.2:
            self.food_type = 'slow'
            self.timer = 80
        else:
            self.food_type = 'normal'
            self.timer = 0
    
    def update(self):
        if self.food_type in ['bonus', 'slow']:
            self.timer -= 1
            if self.timer <= 0:
                self.food_type = 'normal'
    
    def draw(self, screen, grid_size):
        x = self.position[0] * grid_size
        y = self.position[1] * grid_size
        size = grid_size - 2
        center_x = x + grid_size // 2
        center_y = y + grid_size // 2
        
        if self.food_type == 'normal':
            # Draw apple-like food with Pixar style
            # Main body
            pygame.draw.circle(screen, RED, (center_x, center_y), size // 2)
            
            # Add gradient/shading
            gradient_color = (min(255, RED[0] + 30), min(255, RED[1] + 30), min(255, RED[2] + 30))
            pygame.draw.circle(screen, gradient_color, (center_x - 2, center_y - 2), size // 3)
            
            # Add stem
            stem_color = (139, 69, 19)
            pygame.draw.line(screen, stem_color, (center_x, center_y - size // 2), 
                           (center_x, center_y - size // 2 - 4), 2)
            
            # Add leaf
            leaf_color = (34, 139, 34)
            pygame.draw.ellipse(screen, leaf_color, 
                              (center_x - 3, center_y - size // 2 - 6, 6, 4))
            
            # Add shine
            shine_color = (255, 255, 255)
            pygame.draw.circle(screen, shine_color, (center_x - 3, center_y - 3), 2)
            
            # Add subtle glow
            glow_surface = pygame.Surface((size + 8, size + 8), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*RED, 50), (size//2 + 4, size//2 + 4), size//2 + 4)
            screen.blit(glow_surface, (x + 1 - 4, y + 1 - 4))
            
        elif self.food_type == 'bonus':
            # Draw star-like bonus food with animation
            # Pulsing effect
            pulse = abs(pygame.time.get_ticks() % 500 - 250) / 250
            pulse_size = size // 2 + int(pulse * 3)
            
            # Draw star shape
            points = []
            for i in range(10):
                angle = i * 36 * 3.14159 / 180
                if i % 2 == 0:
                    radius = pulse_size
                else:
                    radius = pulse_size // 2
                px = center_x + radius * 0.866 * (1 if i % 4 < 2 else -1)
                py = center_y + radius * 0.5 * (1 if i % 4 in [0, 1] else -1)
                points.append((px, py))
            
            pygame.draw.polygon(screen, PURPLE, points)
            
            # Add inner glow
            inner_color = (min(255, PURPLE[0] + 50), min(255, PURPLE[1] + 50), min(255, PURPLE[2] + 50))
            pygame.draw.polygon(screen, inner_color, points, width=2)
            
            # Add center
            pygame.draw.circle(screen, YELLOW, (center_x, center_y), pulse_size // 3)
            
            # Add shine
            pygame.draw.circle(screen, WHITE, (center_x - 2, center_y - 2), 3)
            
            # Add strong glow
            glow_surface = pygame.Surface((size + 12, size + 12), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*PURPLE, 80), (size//2 + 6, size//2 + 6), size//2 + 6)
            screen.blit(glow_surface, (x + 1 - 6, y + 1 - 6))
            
        elif self.food_type == 'slow':
            # Draw ice crystal-like food
            # Main crystal shape
            crystal_points = [
                (center_x, center_y - size // 2),
                (center_x + size // 3, center_y - size // 4),
                (center_x + size // 2, center_y),
                (center_x + size // 3, center_y + size // 4),
                (center_x, center_y + size // 2),
                (center_x - size // 3, center_y + size // 4),
                (center_x - size // 2, center_y),
                (center_x - size // 3, center_y - size // 4)
            ]
            pygame.draw.polygon(screen, CYAN, crystal_points)
            
            # Add inner facets
            inner_color = (min(255, CYAN[0] + 50), min(255, CYAN[1] + 50), min(255, CYAN[2] + 50))
            pygame.draw.polygon(screen, inner_color, crystal_points, width=2)
            
            # Add sparkle effect
            sparkle_size = 3
            pygame.draw.circle(screen, WHITE, (center_x - 2, center_y - 2), sparkle_size)
            pygame.draw.circle(screen, WHITE, (center_x + 3, center_y + 1), sparkle_size - 1)
            
            # Add ice glow
            glow_surface = pygame.Surface((size + 10, size + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*CYAN, 70), (size//2 + 5, size//2 + 5), size//2 + 5)
            screen.blit(glow_surface, (x + 1 - 5, y + 1 - 5))

class Obstacle:
    def __init__(self, x, y):
        self.position = (x, y)
    
    def draw(self, screen, grid_size):
        x = self.position[0] * grid_size
        y = self.position[1] * grid_size
        size = grid_size - 2
        
        # Draw rounded obstacle with 3D effect
        rect = pygame.Rect(x + 1, y + 1, size, size)
        
        # Main body with gradient
        pygame.draw.rect(screen, GRAY, rect, border_radius=size//4)
        
        # Add 3D shading
        shadow_color = tuple(max(0, c - 40) for c in GRAY)
        pygame.draw.rect(screen, shadow_color, rect, width=3, border_radius=size//4)
        
        # Add highlight
        highlight_color = tuple(min(255, c + 30) for c in GRAY)
        highlight_rect = pygame.Rect(x + 3, y + 3, size//4, size//4)
        pygame.draw.ellipse(screen, highlight_color, highlight_rect)
        
        # Add subtle texture lines
        for i in range(2):
            line_y = y + size//3 + i * size//4
            pygame.draw.line(screen, shadow_color, 
                           (x + 4, line_y), 
                           (x + size - 4, line_y), 1)

class SoundManager:
    """Generates simple sound effects procedurally (no external asset files)."""
    SAMPLE_RATE = 44100

    def __init__(self):
        self.enabled = True
        self.available = False
        self.sounds = {}
        self.channels = 2
        self.sample_rate = self.SAMPLE_RATE
        if not NUMPY_AVAILABLE:
            return
        try:
            # pygame.init() usually initialises the mixer already; adapt to
            # whatever format it chose rather than fighting it.
            init = pygame.mixer.get_init()
            if init is None:
                pygame.mixer.init(self.SAMPLE_RATE, -16, 2, 512)
                init = pygame.mixer.get_init()
            self.sample_rate = init[0]
            self.channels = init[2]
            self._build_sounds()
            self.available = True
        except Exception:
            # Audio device may be unavailable (e.g. headless) — degrade gracefully.
            self.available = False

    def _tone(self, start_freq, end_freq, ms, volume=0.35, wave='sine'):
        n = max(1, int(self.sample_rate * ms / 1000))
        freqs = np.linspace(start_freq, end_freq, n)
        phase = 2 * np.pi * np.cumsum(freqs) / self.sample_rate
        if wave == 'square':
            samples = np.sign(np.sin(phase))
        else:
            samples = np.sin(phase)
        # Attack/decay envelope to avoid clicks
        env = np.ones(n)
        fade = max(1, n // 8)
        env[:fade] = np.linspace(0, 1, fade)
        env[-fade:] = np.linspace(1, 0, fade)
        samples = (samples * env * volume * 32767).astype(np.int16)
        # Match the mixer's channel layout (mono -> 1D, stereo -> 2D).
        if self.channels > 1:
            samples = np.repeat(samples.reshape(n, 1), self.channels, axis=1)
        return pygame.sndarray.make_sound(np.ascontiguousarray(samples))

    def _build_sounds(self):
        self.sounds['eat'] = self._tone(440, 660, 90)
        self.sounds['bonus'] = self._tone(660, 990, 160, volume=0.4)
        self.sounds['slow'] = self._tone(520, 300, 160)
        self.sounds['game_over'] = self._tone(400, 120, 450, volume=0.4, wave='square')
        self.sounds['achievement'] = self._tone(700, 1100, 260, volume=0.4)
        self.sounds['buy'] = self._tone(600, 900, 200, volume=0.4)
        self.sounds['denied'] = self._tone(300, 200, 180, wave='square')

    def play(self, name):
        if self.enabled and self.available and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass


class Game:
    def __init__(self):
        pygame.init()
        
        # Detect screen size for responsive design
        info = pygame.display.Info()
        self.screen_width = min(800, info.current_w - 20)
        self.screen_height = min(800, info.current_h - 20)
        
        # Ensure minimum size
        self.screen_width = max(400, self.screen_width)
        self.screen_height = max(400, self.screen_height)
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Calculate responsive grid with smaller cells for more visibility
        self.grid_size = max(12, min(20, self.screen_width // 40))
        self.grid_width = self.screen_width // self.grid_size
        self.grid_height = self.screen_height // self.grid_size

        # Pre-rendered gradient background
        self.background = self.build_background()

        self.snake = Snake(self.grid_width, self.grid_height)
        self.food = Food(self.grid_width, self.grid_height)
        self.particles = []
        self.obstacles = []
        self.score = 0
        self.high_score = self.load_high_score()
        self.game_over = False
        self.paused = False
        self.level = 1
        self.base_fps = FPS
        self.speed_boost = False
        self.speed_boost_timer = 0
        self.combo = 0
        self.combo_timer = 0
        self.screen_shake = 0
        
        # Touch controls
        self.touch_start = None
        self.swipe_threshold = 50
        
        # Settings
        self.sound_enabled = True
        self.vibration_enabled = True
        self.load_settings()
        self.show_tutorial = self.high_score == 0
        self.in_settings = False

        # Sound engine (procedurally generated effects)
        self.sound_manager = SoundManager()
        self.sound_manager.enabled = self.sound_enabled

        # On-screen notifications (achievements, purchases, challenges)
        self.notifications = []
        
        # Achievements
        self.achievements = {
            'first_score': {'name': 'First Blood', 'desc': 'Score 10 points', 'unlocked': False},
            'combo_master': {'name': 'Combo Master', 'desc': 'Reach 5x combo', 'unlocked': False},
            'level_5': {'name': 'Rising Star', 'desc': 'Reach level 5', 'unlocked': False},
            'score_100': {'name': 'Century', 'desc': 'Score 100 points', 'unlocked': False},
            'survivor': {'name': 'Survivor', 'desc': 'Play for 2 minutes', 'unlocked': False}
        }
        self.load_achievements()
        self.game_time = 0
        
        # Daily challenges
        self.daily_challenge = self.generate_daily_challenge()
        self.daily_challenge_completed = False
        self.load_daily_challenge()
        
        # Shop and skins
        self.currency = 0
        self.load_currency()
        self.current_skin = 'classic'
        self.skins = {
            'classic': {'name': 'Classic', 'color': GREEN, 'price': 0, 'unlocked': True},
            'fire': {'name': 'Fire', 'color': (255, 100, 50), 'price': 100, 'unlocked': False},
            'ice': {'name': 'Ice', 'color': (100, 200, 255), 'price': 150, 'unlocked': False},
            'gold': {'name': 'Gold', 'color': (255, 215, 0), 'price': 200, 'unlocked': False},
            'neon': {'name': 'Neon', 'color': (255, 0, 255), 'price': 300, 'unlocked': False},
            'rainbow': {'name': 'Rainbow', 'color': None, 'price': 500, 'unlocked': False, 'rainbow': True}
        }
        self.load_skins()
        self.in_shop = False
        
        # Game mode: 'classic' (no obstacles, wrap around), 'obstacles' (with obstacles, walls kill)
        self.game_mode = 'classic'  # Default mode
        self.in_mode_selection = True

        self.generate_obstacles()
        # Make sure food never starts on top of an obstacle
        self.food.randomize_position(self.snake.body, [obs.position for obs in self.obstacles])

    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    data = json.load(f)
                    self.sound_enabled = data.get('sound_enabled', True)
                    self.vibration_enabled = data.get('vibration_enabled', True)
        except Exception:
            pass

    def save_settings(self):
        try:
            with open('settings.json', 'w') as f:
                json.dump({
                    'sound_enabled': self.sound_enabled,
                    'vibration_enabled': self.vibration_enabled
                }, f)
        except Exception:
            pass

    def notify(self, text, color=None):
        """Queue an on-screen notification banner."""
        if color is None:
            color = YELLOW
        self.notifications.append({'text': text, 'color': color, 'timer': 30})

    def load_currency(self):
        try:
            if os.path.exists('currency.json'):
                with open('currency.json', 'r') as f:
                    data = json.load(f)
                    self.currency = data.get('currency', 0)
        except:
            pass
    
    def save_currency(self):
        try:
            with open('currency.json', 'w') as f:
                json.dump({'currency': self.currency}, f)
        except:
            pass
    
    def load_skins(self):
        try:
            if os.path.exists('skins.json'):
                with open('skins.json', 'r') as f:
                    data = json.load(f)
                    self.current_skin = data.get('current_skin', 'classic')
                    unlocked_skins = data.get('unlocked', [])
                    for skin_id in unlocked_skins:
                        if skin_id in self.skins:
                            self.skins[skin_id]['unlocked'] = True
        except:
            pass
    
    def save_skins(self):
        try:
            unlocked_skins = [sid for sid, skin in self.skins.items() if skin['unlocked']]
            with open('skins.json', 'w') as f:
                json.dump({
                    'current_skin': self.current_skin,
                    'unlocked': unlocked_skins
                }, f)
        except:
            pass
    
    def buy_skin(self, skin_id):
        if skin_id in self.skins and not self.skins[skin_id]['unlocked']:
            price = self.skins[skin_id]['price']
            if self.currency >= price:
                self.currency -= price
                self.skins[skin_id]['unlocked'] = True
                self.current_skin = skin_id
                self.save_currency()
                self.save_skins()
                return True
        return False
    
    def equip_skin(self, skin_id):
        if skin_id in self.skins and self.skins[skin_id]['unlocked']:
            self.current_skin = skin_id
            self.save_skins()
            return True
        return False
    
    def handle_shop_selection(self, index):
        skin_keys = list(self.skins.keys())
        if index < len(skin_keys):
            skin_id = skin_keys[index]
            if self.skins[skin_id]['unlocked']:
                self.equip_skin(skin_id)
                self.sound_manager.play('eat')
            else:
                if self.buy_skin(skin_id):
                    self.notify(f"Unlocked {self.skins[skin_id]['name']} skin!", GREEN)
                    self.sound_manager.play('buy')
                else:
                    self.notify("Not enough coins", RED)
                    self.sound_manager.play('denied')
    
    def generate_daily_challenge(self):
        challenges = [
            {'type': 'score', 'target': 50, 'name': 'Score 50 points', 'reward': 100},
            {'type': 'score', 'target': 100, 'name': 'Score 100 points', 'reward': 200},
            {'type': 'combo', 'target': 3, 'name': 'Reach 3x combo', 'reward': 150},
            {'type': 'level', 'target': 3, 'name': 'Reach level 3', 'reward': 150},
            {'type': 'survival', 'target': 60, 'name': 'Survive 60 seconds', 'reward': 100}
        ]
        # Deterministic per calendar day: everyone gets the same challenge on a
        # given date, and it stays stable across restarts within that day.
        day_index = datetime.date.today().toordinal()
        return challenges[day_index % len(challenges)]

    def load_daily_challenge(self):
        try:
            if os.path.exists('daily_challenge.json'):
                with open('daily_challenge.json', 'r') as f:
                    data = json.load(f)
                    today = datetime.date.today().isoformat()
                    # Only restore the "completed" flag if it belongs to today.
                    if data.get('date') == today:
                        self.daily_challenge_completed = data.get('completed', False)
        except Exception:
            pass

    def save_daily_challenge(self):
        try:
            today = datetime.date.today().isoformat()
            with open('daily_challenge.json', 'w') as f:
                json.dump({
                    'date': today,
                    'challenge': self.daily_challenge,
                    'completed': self.daily_challenge_completed
                }, f)
        except Exception:
            pass
    
    def check_daily_challenge(self):
        if self.daily_challenge_completed:
            return
        
        challenge_type = self.daily_challenge['type']
        target = self.daily_challenge['target']
        
        if challenge_type == 'score' and self.score >= target:
            self.daily_challenge_completed = True
        elif challenge_type == 'combo' and self.combo >= target:
            self.daily_challenge_completed = True
        elif challenge_type == 'level' and self.level >= target:
            self.daily_challenge_completed = True
        elif challenge_type == 'survival' and self.game_time >= target * 10:  # Convert seconds to frames
            self.daily_challenge_completed = True
        
        if self.daily_challenge_completed:
            self.save_daily_challenge()
            # Award currency
            self.currency += self.daily_challenge['reward']
            self.save_currency()
            self.notify(f"Daily Challenge! +{self.daily_challenge['reward']} coins", GREEN)
            self.sound_manager.play('achievement')
    
    def generate_obstacles(self):
        self.obstacles = []
        if self.game_mode == 'obstacles':
            num_obstacles = min(5 + self.level * 2, 20)
            obstacle_positions = []
            for _ in range(num_obstacles):
                while True:
                    x = random.randint(2, self.grid_width - 3)
                    y = random.randint(2, self.grid_height - 3)
                    pos = (x, y)
                    # Don't place on snake start position or existing obstacles
                    if pos != (self.grid_width // 2, self.grid_height // 2) and pos not in obstacle_positions:
                        self.obstacles.append(Obstacle(x, y))
                        obstacle_positions.append(pos)
                        break
    
    def build_background(self):
        """Pre-render a smooth vertical gradient background once (cheap to blit)."""
        bg = pygame.Surface((self.screen_width, self.screen_height))
        top = (34, 40, 68)      # soft indigo
        bottom = (18, 22, 40)   # deep navy
        h = max(1, self.screen_height)
        for y in range(self.screen_height):
            t = y / h
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            pygame.draw.line(bg, (r, g, b), (0, y), (self.screen_width, y))
        # Subtle grid on top of the gradient
        grid_color = (255, 255, 255)
        grid_overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        for x in range(0, self.screen_width, self.grid_size):
            pygame.draw.line(grid_overlay, (*grid_color, 12), (x, 0), (x, self.screen_height), 1)
        for y in range(0, self.screen_height, self.grid_size):
            pygame.draw.line(grid_overlay, (*grid_color, 12), (0, y), (self.screen_width, y), 1)
        bg.blit(grid_overlay, (0, 0))
        return bg

    def draw_background(self, surface):
        surface.blit(self.background, (0, 0))

    def create_particles(self, x, y, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        return False
                else:
                    if event.key == pygame.K_UP:
                        self.snake.change_direction((0, -1))
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction((0, 1))
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction((-1, 0))
                    elif event.key == pygame.K_RIGHT:
                        self.snake.change_direction((1, 0))
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_s:
                        if self.in_shop:
                            self.in_shop = False
                        else:
                            self.in_settings = not self.in_settings
                    elif event.key == pygame.K_b:
                        if not self.in_settings:
                            self.in_shop = not self.in_shop
                    elif event.key == pygame.K_1 and self.in_mode_selection:
                        self.start_game('classic')
                    elif event.key == pygame.K_2 and self.in_mode_selection:
                        self.start_game('obstacles')
                    elif event.key == pygame.K_1 and self.in_settings:
                        self.sound_enabled = not self.sound_enabled
                        self.sound_manager.enabled = self.sound_enabled
                        self.save_settings()
                    elif event.key == pygame.K_2 and self.in_settings:
                        self.vibration_enabled = not self.vibration_enabled
                        self.save_settings()
                    elif event.key == pygame.K_1 and self.in_shop:
                        self.handle_shop_selection(0)
                    elif event.key == pygame.K_2 and self.in_shop:
                        self.handle_shop_selection(1)
                    elif event.key == pygame.K_3 and self.in_shop:
                        self.handle_shop_selection(2)
                    elif event.key == pygame.K_4 and self.in_shop:
                        self.handle_shop_selection(3)
                    elif event.key == pygame.K_5 and self.in_shop:
                        self.handle_shop_selection(4)
                    elif event.key == pygame.K_6 and self.in_shop:
                        self.handle_shop_selection(5)
                    elif event.key == pygame.K_ESCAPE:
                        return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.touch_start = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.touch_start:
                    touch_end = event.pos
                    dx = touch_end[0] - self.touch_start[0]
                    dy = touch_end[1] - self.touch_start[1]
                    
                    # Detect swipe direction
                    if abs(dx) > abs(dy):
                        if abs(dx) > self.swipe_threshold:
                            if dx > 0:
                                self.snake.change_direction((1, 0))
                            else:
                                self.snake.change_direction((-1, 0))
                    else:
                        if abs(dy) > self.swipe_threshold:
                            if dy > 0:
                                self.snake.change_direction((0, 1))
                            else:
                                self.snake.change_direction((0, -1))
                    
                    self.touch_start = None
        return True
    
    def update(self):
        # Notifications fade out regardless of game state
        for note in self.notifications:
            note['timer'] -= 1
        self.notifications = [n for n in self.notifications if n['timer'] > 0]

        if not self.game_over and not self.paused and not self.in_settings and not self.in_shop and not self.in_mode_selection:
            # Update game time for survivor achievement
            self.game_time += 1
            if self.game_time >= 1200:  # 2 minutes at 10 FPS
                self.unlock_achievement('survivor')
            
            # Update food timer
            self.food.update()
            
            # Update speed boost
            if self.speed_boost:
                self.speed_boost_timer -= 1
                if self.speed_boost_timer <= 0:
                    self.speed_boost = False
            
            # Update combo
            if self.combo_timer > 0:
                self.combo_timer -= 1
                if self.combo_timer <= 0:
                    self.combo = 0
            
            # Update screen shake
            if self.screen_shake > 0:
                self.screen_shake -= 1
            
            # Update particles
            self.particles = [p for p in self.particles if p.life > 0]
            for particle in self.particles:
                particle.update()
            
            # Update snake animation
            self.snake.update_animation()
            
            # Move snake based on game mode
            wrap_around = (self.game_mode == 'classic')
            if not self.snake.move(wrap_around):
                self.trigger_game_over()

            # Check obstacle collision (only in obstacles mode)
            if not self.game_over and self.game_mode == 'obstacles':
                if self.snake.body[0] in [obs.position for obs in self.obstacles]:
                    self.trigger_game_over()
            
            # Check food collision
            if self.snake.body[0] == self.food.position:
                self.snake.grow = True
                
                # Update combo
                self.combo += 1
                self.combo_timer = 60  # 6 seconds at 10 FPS
                
                # Check combo achievement
                if self.combo >= 5:
                    self.unlock_achievement('combo_master')
                
                # Calculate score based on food type with combo bonus
                combo_multiplier = 1 + (self.combo - 1) * 0.1
                
                if self.food.food_type == 'normal':
                    points = int(10 * combo_multiplier)
                    self.score += points
                    self.create_particles(self.food.position[0] * self.grid_size + self.grid_size // 2,
                                       self.food.position[1] * self.grid_size + self.grid_size // 2,
                                       RED, 8)
                    self.sound_manager.play('eat')
                elif self.food.food_type == 'bonus':
                    points = int(30 * combo_multiplier)
                    self.score += points
                    self.create_particles(self.food.position[0] * self.grid_size + self.grid_size // 2,
                                       self.food.position[1] * self.grid_size + self.grid_size // 2,
                                       PURPLE, 15)
                    self.sound_manager.play('bonus')
                elif self.food.food_type == 'slow':
                    points = int(15 * combo_multiplier)
                    self.score += points
                    self.speed_boost = True
                    self.speed_boost_timer = 50
                    self.create_particles(self.food.position[0] * self.grid_size + self.grid_size // 2,
                                       self.food.position[1] * self.grid_size + self.grid_size // 2,
                                       CYAN, 12)
                    self.sound_manager.play('slow')
                
                # Check score achievements
                if self.score >= 10:
                    self.unlock_achievement('first_score')
                if self.score >= 100:
                    self.unlock_achievement('score_100')
                
                self.update_level()
                obstacle_positions = [obs.position for obs in self.obstacles]
                self.food.randomize_position(self.snake.body, obstacle_positions)
                
                # Check daily challenge
                self.check_daily_challenge()
    
    def draw(self):
        # Apply screen shake
        shake_x = 0
        shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.randint(-5, 5)
            shake_y = random.randint(-5, 5)
        
        # Draw animated background
        self.draw_background(self.screen)
        
        if not self.game_over:
            # Draw obstacles
            for obstacle in self.obstacles:
                obstacle.draw(self.screen, self.grid_size)
            
            # Draw snake with current skin
            skin_data = self.skins[self.current_skin]
            skin_color = skin_data.get('color')
            is_rainbow = skin_data.get('rainbow', False)
            self.snake.draw(self.screen, self.grid_size, skin_color, is_rainbow)
            
            self.food.draw(self.screen, self.grid_size)
            
            # Draw particles
            for particle in self.particles:
                particle.draw(self.screen)

        # Apply screen shake offset
        if shake_x != 0 or shake_y != 0:
            temp_surface = pygame.Surface((self.screen_width, self.screen_height))
            temp_surface.blit(self.screen, (0, 0))
            self.screen.fill(BLACK)
            self.screen.blit(temp_surface, (shake_x, shake_y))
        
        # Draw UI on top (no shake, at screen resolution)
        # Draw score and level
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        high_score_text = self.small_font.render(f"High Score: {self.high_score}", True, YELLOW)
        level_text = self.small_font.render(f"Level: {self.level}", True, BLUE)
        
        ui_offset_x = 10
        ui_offset_y = 10
        ui_spacing = 25
        
        self.screen.blit(score_text, (ui_offset_x, ui_offset_y))
        self.screen.blit(high_score_text, (ui_offset_x, ui_offset_y + ui_spacing))
        self.screen.blit(level_text, (ui_offset_x, ui_offset_y + ui_spacing * 2))
        
        # Draw combo
        if self.combo > 1:
            combo_text = self.small_font.render(f"Combo: {self.combo}x", True, ORANGE)
            self.screen.blit(combo_text, (ui_offset_x, ui_offset_y + ui_spacing * 3))
        
        # Draw speed boost indicator
        if self.speed_boost:
            boost_text = self.small_font.render("SLOW MOTION!", True, CYAN)
            self.screen.blit(boost_text, (self.screen_width - 120, ui_offset_y))
        
        # Draw daily challenge
        if not self.daily_challenge_completed:
            challenge_text = self.small_font.render(f"Daily: {self.daily_challenge['name']}", True, ORANGE)
            self.screen.blit(challenge_text, (self.screen_width - challenge_text.get_width() - 10, ui_offset_y + ui_spacing))
        else:
            completed_text = self.small_font.render("Daily: COMPLETED!", True, GREEN)
            self.screen.blit(completed_text, (self.screen_width - completed_text.get_width() - 10, ui_offset_y + ui_spacing))
        
        # Draw tutorial
        if self.show_tutorial and not self.game_over:
            tutorial_text = self.small_font.render("Swipe or use arrow keys to move", True, WHITE)
            self.screen.blit(tutorial_text, (self.screen_width // 2 - tutorial_text.get_width() // 2,
                                           self.screen_height - 30))
        
        # Draw mode selection menu
        if self.in_mode_selection:
            mode_bg = pygame.Surface((self.screen_width, self.screen_height))
            mode_bg.fill((20, 20, 40))
            mode_bg.set_alpha(230)
            self.screen.blit(mode_bg, (0, 0))
            
            title = self.font.render("SELECT GAME MODE", True, WHITE)
            self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))
            
            classic_text = self.small_font.render("1. Classic Mode (No obstacles, wrap around)", True, GREEN)
            obstacles_text = self.small_font.render("2. Obstacles Mode (With obstacles, walls kill)", True, ORANGE)
            instruction_text = self.small_font.render("Press 1 or 2 to select", True, YELLOW)
            
            self.screen.blit(classic_text, (self.screen_width // 2 - classic_text.get_width() // 2, 150))
            self.screen.blit(obstacles_text, (self.screen_width // 2 - obstacles_text.get_width() // 2, 200))
            self.screen.blit(instruction_text, (self.screen_width // 2 - instruction_text.get_width() // 2, 300))
        
        # Draw settings menu
        if self.in_settings:
            settings_bg = pygame.Surface((self.screen_width, self.screen_height))
            settings_bg.fill((30, 30, 30))
            settings_bg.set_alpha(200)
            self.screen.blit(settings_bg, (0, 0))
            
            title = self.font.render("SETTINGS", True, WHITE)
            self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))
            
            sound_text = self.small_font.render(f"Sound: {'ON' if self.sound_enabled else 'OFF'} (Press 1)", True, WHITE)
            vibration_text = self.small_font.render(f"Vibration: {'ON' if self.vibration_enabled else 'OFF'} (Press 2)", True, WHITE)
            back_text = self.small_font.render("Press S to return", True, YELLOW)
            
            self.screen.blit(sound_text, (self.screen_width // 2 - sound_text.get_width() // 2, 150))
            self.screen.blit(vibration_text, (self.screen_width // 2 - vibration_text.get_width() // 2, 200))
            self.screen.blit(back_text, (self.screen_width // 2 - back_text.get_width() // 2, 300))
        
        # Draw shop menu
        if self.in_shop:
            shop_bg = pygame.Surface((self.screen_width, self.screen_height))
            shop_bg.fill((40, 30, 50))
            shop_bg.set_alpha(200)
            self.screen.blit(shop_bg, (0, 0))
            
            title = self.font.render("SKIN SHOP", True, WHITE)
            currency_text = self.small_font.render(f"Currency: {self.currency}", True, YELLOW)
            back_text = self.small_font.render("Press B to return, 1-6 to select", True, YELLOW)
            
            self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 30))
            self.screen.blit(currency_text, (self.screen_width // 2 - currency_text.get_width() // 2, 80))
            self.screen.blit(back_text, (self.screen_width // 2 - back_text.get_width() // 2, self.screen_height - 50))
            
            # Draw skin options
            skin_keys = list(self.skins.keys())
            for i, skin_id in enumerate(skin_keys):
                skin = self.skins[skin_id]
                y_pos = 120 + i * 50
                
                if skin['unlocked']:
                    if self.current_skin == skin_id:
                        status_text = self.small_font.render(f"{i+1}. {skin['name']} (EQUIPPED)", True, GREEN)
                    else:
                        status_text = self.small_font.render(f"{i+1}. {skin['name']} (Press {i+1})", True, WHITE)
                else:
                    status_text = self.small_font.render(f"{i+1}. {skin['name']} - {skin['price']} (Press {i+1})", True, RED)
                
                self.screen.blit(status_text, (self.screen_width // 2 - status_text.get_width() // 2, y_pos))
        
        if self.paused:
            pause_text = self.font.render("PAUSED", True, YELLOW)
            resume_text = self.small_font.render("Press P to resume", True, WHITE)
            
            self.screen.blit(pause_text, (self.screen_width // 2 - pause_text.get_width() // 2,
                                         self.screen_height // 2 - 20))
            self.screen.blit(resume_text, (self.screen_width // 2 - resume_text.get_width() // 2,
                                          self.screen_height // 2 + 20))
        
        if self.game_over:
            game_over_text = self.font.render("GAME OVER", True, RED)
            restart_text = self.font.render("Press SPACE to restart", True, WHITE)
            quit_text = self.font.render("Press ESC to quit", True, WHITE)
            
            if self.score >= self.high_score and self.score > 0:
                new_high_text = self.font.render("NEW HIGH SCORE!", True, YELLOW)
                self.screen.blit(new_high_text, (self.screen_width // 2 - new_high_text.get_width() // 2,
                                                self.screen_height // 2 - 90))
            
            self.screen.blit(game_over_text, (self.screen_width // 2 - game_over_text.get_width() // 2, 
                                            self.screen_height // 2 - 60))
            self.screen.blit(restart_text, (self.screen_width // 2 - restart_text.get_width() // 2, 
                                           self.screen_height // 2))
            self.screen.blit(quit_text, (self.screen_width // 2 - quit_text.get_width() // 2, 
                                       self.screen_height // 2 + 40))

        # Draw notification banners (newest at top), fading out
        for idx, note in enumerate(self.notifications):
            alpha = min(255, int(note['timer'] / 30 * 255))
            note_surface = self.small_font.render(note['text'], True, note['color'])
            note_surface.set_alpha(alpha)
            bg = pygame.Surface((note_surface.get_width() + 20, note_surface.get_height() + 10), pygame.SRCALPHA)
            bg.fill((0, 0, 0, min(180, alpha)))
            y_pos = 120 + idx * 40
            x_pos = self.screen_width // 2 - note_surface.get_width() // 2
            self.screen.blit(bg, (x_pos - 10, y_pos - 5))
            self.screen.blit(note_surface, (x_pos, y_pos))

        pygame.display.flip()
    
    def start_game(self, mode):
        self.game_mode = mode
        self.in_mode_selection = False
        self.generate_obstacles()
        self.food.randomize_position(self.snake.body, [obs.position for obs in self.obstacles])

    def trigger_game_over(self):
        if self.game_over:
            return
        self.game_over = True
        self.screen_shake = 10
        self.combo = 0
        self.sound_manager.play('game_over')
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def reset_game(self):
        self.snake.reset()
        obstacle_positions = [obs.position for obs in self.obstacles]
        self.food.randomize_position(self.snake.body, obstacle_positions)
        self.score = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.particles = []
        self.speed_boost = False
        self.speed_boost_timer = 0
        self.combo = 0
        self.combo_timer = 0
        self.screen_shake = 0
        self.show_tutorial = False
        self.generate_obstacles()
    
    def update_level(self):
        self.level = 1 + (self.score // 50)
        if self.level >= 5:
            self.unlock_achievement('level_5')
    
    def unlock_achievement(self, achievement_id):
        if achievement_id in self.achievements and not self.achievements[achievement_id]['unlocked']:
            self.achievements[achievement_id]['unlocked'] = True
            self.save_achievements()
            self.notify(f"Achievement: {self.achievements[achievement_id]['name']}", YELLOW)
            self.sound_manager.play('achievement')
    
    def load_achievements(self):
        try:
            if os.path.exists('achievements.json'):
                with open('achievements.json', 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if key in self.achievements:
                            self.achievements[key]['unlocked'] = value.get('unlocked', False)
        except:
            pass
    
    def save_achievements(self):
        try:
            with open('achievements.json', 'w') as f:
                json.dump(self.achievements, f)
        except:
            pass
    
    def get_current_fps(self):
        fps = self.base_fps + (self.level - 1) * 2
        if self.speed_boost:
            fps = max(5, fps - 5)  # Slow down when speed boost is active
        return fps
    
    def load_high_score(self):
        try:
            if os.path.exists('high_score.json'):
                with open('high_score.json', 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except:
            pass
        return 0
    
    def save_high_score(self):
        try:
            with open('high_score.json', 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except:
            pass
    
    async def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.get_current_fps())
            # Yield to the event loop — required for the web (pygbag/wasm)
            # build, harmless on desktop.
            await asyncio.sleep(0)

        pygame.quit()


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())

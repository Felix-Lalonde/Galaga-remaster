# code 12 affichage entre niveau, highscore, power up et vie donnee
#INIT ECRAN et-base
import pygame
import random
import os
pygame.init()
screen = pygame.display.set_mode((1080,1880))
pygame.display.set_caption("GALAGA")
screen_width = 1080
screen_height = 1880
clock = pygame.time.Clock()
screen.fill((0, 0, 0))

flag_twin_hit = False

score = 0
score_font = pygame.font.Font(None, 60)
YELLOW = (255,215,0)
WHITE = (255,255,255)
LBLUE = (120, 200, 255)

title_font = pygame.font.Font(None, 130)   # "LEVEL : N"
info_font  = pygame.font.Font(None, 90)   # statistiques de fin de niveau

INTRO_MS   = 2000
SUMMARY_MS = 3500

FLAG_SHOOT = True
# FLAG_SHOOT = False

#variable power up
twin_offset = 50
POWERUP_HITS_REQUIRED = 4     # l'orbe doit être touchée 4 fois
POWERUP_CHECK_EVERY_MS = 12000 # on tente un spawn toutes les ~12 s pendant le jeu
twin_active = False
next_powerup_check_ms = pygame.time.get_ticks() + 4000  # 1ère tentative après 4 s

game_over_font = pygame.font.Font(None, 200)  
game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
game_over_rect = game_over_text.get_rect(center=(screen_width // 2, screen_height // 2))
new_highscore_font = pygame.font.Font(None, 80) 
overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
overlay.fill((0, 0, 0, 128)) 

#ETOILES
STAR_COUNT_SM = 50   # petites étoiles
STAR_COUNT_MD = 35   # moyennes
STAR_COUNT_LG = 20   # grosses 
STAR_SPEED_SM = 2
STAR_SPEED_MD = 3
STAR_SPEED_LG = 4

# Twinkle très léger (pas de per-pixel alpha chaque frame)
# On alterne juste entre 2 intensités selon un compteur global.
STAR_TWINKLE_MIN = 20   # nb frames avant de potentiellement changer
STAR_TWINKLE_MAX = 50

# Surfaces prefaite
_star_px_small_dim  = 2
_star_px_medium_dim = 3
_star_px_large_dim  = 4
star_surf_small  = pygame.Surface((_star_px_small_dim,  _star_px_small_dim),  pygame.SRCALPHA)
star_surf_medium = pygame.Surface((_star_px_medium_dim, _star_px_medium_dim), pygame.SRCALPHA)
star_surf_large  = pygame.Surface((_star_px_large_dim,  _star_px_large_dim),  pygame.SRCALPHA)
star_surf_small.fill((255, 255, 255, 220))
star_surf_medium.fill((255, 255, 255, 230))
star_surf_large.fill((255, 255, 255, 255))

# Conteneur des étoiles
stars = []
_frame_counter = 0

def _mk_star(size_tag):
    if size_tag == "sm":
        speed = STAR_SPEED_SM;  surf = star_surf_small
    elif size_tag == "md":
        speed = STAR_SPEED_MD;  surf = star_surf_medium
    else:
        speed = STAR_SPEED_LG;  surf = star_surf_large

    return {
        "x": random.randint(0, screen_width - 1),
        "y": random.randint(0, screen_height - 1),
        "speed": speed,
        "surf": surf,
        # scintillement “léger” (deux niveaux)
        "phase": random.randint(0, 1),
        "next_twinkle": random.randint(STAR_TWINKLE_MIN, STAR_TWINKLE_MAX),
        "twinkle_timer": 0,
        "base_alpha": surf.get_at((0,0)).a
    }

def init_stars():
    stars.clear()
    for _ in range(STAR_COUNT_SM):
        s = _mk_star("sm")
        stars.append(s)
    for _ in range(STAR_COUNT_MD):
        s = _mk_star("md")
        stars.append(s)
    for _ in range(STAR_COUNT_LG):
        s = _mk_star("lg")
        stars.append(s)

def update_and_draw_stars(target_surface):
    global _frame_counter
    _frame_counter += 1

    for s in stars:
        # descente
        s["y"] += s["speed"]
        if s["y"] >= screen_height:
            s["y"] = 0
            s["x"] = random.randint(0, screen_width - 1)
            s["twinkle_timer"] = 0
            s["phase"] = random.randint(0, 1)

        # twinkle (toggle très peu coûteux)
        s["twinkle_timer"] += 1
        if s["twinkle_timer"] >= s["next_twinkle"]:
            s["twinkle_timer"] = 0
            s["next_twinkle"] = random.randint(STAR_TWINKLE_MIN, STAR_TWINKLE_MAX)
            s["phase"] ^= 1  

        alpha = s["base_alpha"] if s["phase"] == 1 else int(s["base_alpha"] * 0.5)
        s["surf"].set_alpha(alpha)
        target_surface.blit(s["surf"], (s["x"], s["y"]))


#AUDIO
try:
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
    pygame.mixer.init()
    pygame.mixer.set_num_channels(24)  # un peu de marge (SFX + ambiance)
    AUDIO_ENABLED = True
except Exception as e:
    AUDIO_ENABLED = False
#dossier audio
try:
    BASE_DIR = os.path.dirname(__file__)
except NameError:
    BASE_DIR = os.getcwd()
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

SOUNDS = {}

def _load_sound(name, filename, volume=0.8):
    if not AUDIO_ENABLED:
        return None
    path = os.path.join(AUDIO_DIR, filename)
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        SOUNDS[name] = s
        return s
    except Exception as e:
        print(f"[AUDIO] failed to load {path}: {e}")
        return None

class Audio:
    enabled = AUDIO_ENABLED
    
    @staticmethod
    def init_bank():
        _load_sound("autre",       "autre.mp3",      volume=0.6)
        _load_sound("bee_kill",    "bee_kill.mp3",   volume=0.4)
        _load_sound("boss_kill",   "boss_kill.mp3",  volume=0.4)  # 1ère vie du boss
        _load_sound("boss_kill2",  "boss_kill2.mp3", volume=0.4) # mort du boss
        _load_sound("game_over",   "game_over.mp3",  volume=0.7)
        _load_sound("new_life",    "new_life.mp3",   volume=0.7)
        _load_sound("pap_kill",    "pap_kill.mp3",   volume=0.3)
        _load_sound("power_up",    "power-up.mp3",   volume=0.8)
        _load_sound("shoot",       "shoot.mp3",      volume=0.10)
        _load_sound("stage_start", "stage_start.mp3",volume=0.8)
        _load_sound("player_hit",  "player_hit.mp3", volume=0.6)
        _load_sound("game_start",  "game_start.mp3", volume=0.35)

    @staticmethod
    def play(key, loops=0, fade_ms=0):
        if not Audio.enabled: 
            return
        s = SOUNDS.get(key)
        if not s:
            return
        ch = pygame.mixer.find_channel()
        if ch:
            ch.play(s, loops=loops, fade_ms=fade_ms)

    @staticmethod
    def stop_all():
        if Audio.enabled:
            pygame.mixer.stop()    


#POUR AFFICHAGE SCORE ET ESTHETIQUE
def draw_outline_text(surface, text, font, center_pos, inner_color, outline_color, pad=3):
    inner = font.render(text, True, inner_color)
    outline = font.render(text, True, outline_color)
    cx, cy = center_pos
    # pour le contour 
    for dx, dy in [(-pad, 0), (pad, 0), (0, -pad), (0, pad),
                   (-pad, -pad), (-pad, pad), (pad, -pad), (pad, pad)]:
        rect = outline.get_rect(center=(cx + dx, cy + dy))
        surface.blit(outline, rect)
    rect = inner.get_rect(center=center_pos)
    surface.blit(inner, rect)

def draw_score(surface, value):
    label = f"SCORE : {value}"
    # on calcule la taille pour caler le 'center' près du coin bas-droite
    temp = score_font.render(label, True, YELLOW)
    w, h = temp.get_width(), temp.get_height()
    margin = 30
    center_x = surface.get_width() - margin - w // 2
    center_y = surface.get_height() - margin - h // 2
    draw_outline_text(surface, label, score_font, (center_x, center_y), YELLOW, WHITE, pad=1)

#POINTS POUR CHAQUE ENNEMI
def enemy_points(enemy):
    # Boss = 100 ; Bee/Papillon = 50 ;
    try:
        from types import SimpleNamespace  # évite erreur si import en haut
    except Exception:
        pass
    if isinstance(enemy, Boss):
        return 100
    elif isinstance(enemy, (Bee, Papillon)):
        return 50
    else:
        return 50

#fonctions pour power up
def powerup_spawn_probability(current_level, score, lives):
    # Dominant: level & score; bonus si peu de vies
    #plus on progresse plus on a de prbablite de lavoir
    base = 0.05
    lev  = 0.0125 * current_level                 # +1.5% / niveau
    scr  = 0.01  * min(score / 1000.0, 10.0)    # (cap 10k -> +10%)
    hp   = 0.06  * max(0, 4 - lives)            # +6% par vie manquante
    return min(base + lev + scr + hp, 0.60)     # clamp à 60%

def try_spawn_powerup(now):
    global next_powerup_check_ms
    if now < next_powerup_check_ms:
        return
    next_powerup_check_ms = now + POWERUP_CHECK_EVERY_MS

    if twin_active:
        return
    if len(powerup_group) > 0:
        return

    p = powerup_spawn_probability(current_level, score, player.lives)
    if random.random() <= p:
        x = random.randint(120, screen_width - 120)
        y = random.randint(140, screen_height - 600)
        powerup_group.add(PowerUp(x, y))
        Audio.play("new_life")

#CLASSES DES ENTITES
#init joueur
class Player(pygame.sprite.Sprite):
    def __init__(self, path_png, pos,scale=None):
        super().__init__()
        img = pygame.image.load(path_png).convert_alpha()
        img = pygame.transform.scale(img, (int(img.get_width()*0.25),
                                           int(img.get_height()*0.25)))
        self.image = img
        self.rect  = self.image.get_rect(center=pos)

        self.shoot_cooldown_ms = 160 # en ms
        self._last_shot_time = 0

        #gestion des vies
        self.lives = 4
        self.invulnerable = False
        self.invulnerable_time = 0
        self.invulnerable_duration = 3000  # 3 secondes d'invulnérabilité
        self.life_image = img.copy()
        self.life_image = pygame.transform.scale(self.life_image, (60, 60))

    def move(self, x, y):
        self.rect.move_ip((int(x),int(y)))
        screen_rect = pygame.Rect(0, 0, 1080, 1880)
        self.rect.clamp_ip(screen_rect)

    def shoot(self, bullet_group):
        global level_shots
        now = pygame.time.get_ticks()
        if now - self._last_shot_time < self.shoot_cooldown_ms:
            return  # encore en cooldown
        self._last_shot_time = now
        x = self.rect.centerx
        y = self.rect.top + 10
        Bullet(x, y, bullet_group)
        level_shots += 1
        if twin_active:
            tx = twin_centerx_for_draw()
            Bullet(tx,y,bullet_group)
            level_shots += 1

    def take_damage(self):
        global flag_twin_hit
        if flag_twin_hit == True:
            self.invulnerable = True
            self.invulnerable_time = pygame.time.get_ticks()
            flag_twin_hit = False
            return False
        if not self.invulnerable and self.lives > 0:
            self.lives -= 1
            self.invulnerable = True
            self.invulnerable_time = pygame.time.get_ticks()
            return True
        return False
    
    #update invinsibilite
    def update(self):
        if self.invulnerable:
            current_time = pygame.time.get_ticks()
            if current_time - self.invulnerable_time > self.invulnerable_duration:
                self.invulnerable = False
    
    def draw_lives(self, screen):
        for i in range(self.lives - 1):
            x = 40 + (i * 70)
            y = screen.get_height() - 100
            screen.blit(self.life_image, (x, y))
    
    #clignote joueur si toucher
    def draw(self, screen):
        if self.invulnerable:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                screen.blit(self.image, self.rect)
        else:
            screen.blit(self.image, self.rect)

class Bullet(pygame.sprite.Sprite):
    def __init__(self,x,y,bullet_group,speed=-50):
        super().__init__()
        img = pygame.image.load("/home/fileux/Desktop/Galaga/photos/bullet.png").convert_alpha()
        img = pygame.transform.scale(img, (30, 30))
        self.image = img
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        bullet_group.add(self)

    #vitesse bullet
    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, explosion_group):
        super().__init__()
        self.radius = 5
        self.max_radius = 40
        self.growth_rate = 3 #vitesse circle
        self.center_x = x
        self.center_y = y
        
        # Surface transparente pour l'explosion (a ajuster)
        self.image = pygame.Surface((self.max_radius * 2, self.max_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        
        explosion_group.add(self)
    
    def update(self):
        # Efface l'image précédente
        self.image.fill((0, 0, 0, 0))
        
        # draws explosion
        if self.radius < self.max_radius:
            alpha = int(255 * (1 - self.radius / self.max_radius))  # Plus transparent avec le temps
            color = (255, 150, 0, alpha)  # Orange avec transparence
            pygame.draw.circle(self.image, color, (self.max_radius, self.max_radius), int(self.radius))
            self.radius += self.growth_rate
        else:
            self.kill() 
  
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.hits_left = POWERUP_HITS_REQUIRED
        self.base_radius = 28
        self.image = pygame.Surface((80, 80), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(x, y))
        self._redraw()

    def _redraw(self):
        self.image.fill((0,0,0,0))
        stage  = POWERUP_HITS_REQUIRED - self.hits_left  # 0..3
        radius = self.base_radius - stage*5
        alpha  = 160 + stage*20
        color  = (80, 170 + stage*20, 255, alpha)
        pygame.draw.circle(self.image, color, (40,40), radius)
        pygame.draw.circle(self.image, (200,230,255,220), (40,40), radius, 3)

    def hit_by_player(self):
        self.hits_left -= 1
        if self.hits_left <= 0:
            self.kill()
            return True
        self._redraw()
        return False

def deactivate_twin():
    global twin_active, flag_twin_hit
    twin_active = False
    flag_twin_hit = True


def twin_centerx_for_draw():
    global twin_offset
    cx = player.rect.centerx + twin_offset
    if cx < 40 or cx > (screen_width - 40):
        twin_offset *= -1
        cx = player.rect.centerx + twin_offset
    return cx

def twin_rect_current():
    cx = twin_centerx_for_draw()
    return player.image.get_rect(center=(cx, player.rect.centery))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, img_path, x_spawn,x_final, y_spawn, y_final, speed, movement_pattern,row_id=0):
        super().__init__()
        img = pygame.image.load(img_path).convert_alpha()
        img = pygame.transform.scale(img, (80, 80))
        self.image = img
        self.rect = self.image.get_rect(center=(x_spawn, y_spawn))
        self.speed = speed
        self.movement_pattern = movement_pattern
        self.spawn_time = pygame.time.get_ticks()
        self.x_final = x_final
        self.y_final = y_final
        self.alive = True
        self.can_shoot = FLAG_SHOOT
        self.row_id = row_id
        self.initial_speed = speed
        self.formation_speed = None
        self.has_hit_wall = False 
        self.has_transformed = False

        if movement_pattern == "random":
            self.random_direction_x = random.choice([-1, 1])
            self.random_direction_y = random.choice([-1, 1])
            self.random_speed_x = random.randint(2, 6)
            self.random_speed_y = random.randint(2, 6)
            self.direction_change_timer = 0
            self.direction_change_delay = random.randint(100, 200)

    def kill_enemy(self, explosion_group):
        if self.alive:
            self.alive = False
            Explosion(self.rect.centerx, self.rect.centery, explosion_group)
            # Rend l'ennemi invisible mais garde sa hitbox pour l'espacement
            self.image = pygame.Surface((80, 80), pygame.SRCALPHA)  # transparent
            self.image.fill((0, 0, 0, 0))  

    def shoot(self, enemy_bullet_group, player):
        now = pygame.time.get_ticks()
        if not self.can_shoot or not self.alive:
            return
        
        #probabilite de tir ennemi
        if random.random() < 0.0025: ######### FREQUENCE TIR ENEMY
            x = self.rect.centerx
            y = self.rect.bottom
            target_x = player.rect.centerx
            target_y = player.rect.centery
            EnemyBullet(x, y, target_x, target_y, enemy_bullet_group)
    
    
#init type enemy et png correspondant
class Bee(Enemy):
    def __init__(self, x_spawn, x_final, y_spawn, y_final, speed, movement_pattern,row_id=0):
        super().__init__("/home/fileux/Desktop/Galaga/photos/bee.png", x_spawn, x_final, y_spawn, y_final, speed, movement_pattern,row_id)
        img = pygame.image.load("/home/fileux/Desktop/Galaga/photos/bee.png").convert_alpha()
        self.image = pygame.transform.scale(img, (60,50))
        self.rect = self.image.get_rect(center=(x_spawn,y_spawn))
        self.can_shoot = FLAG_SHOOT

class Papillon(Enemy):
    def __init__(self, x_spawn, x_final, y_spawn, y_final, speed, movement_pattern,row_id=0):
        super().__init__("/home/fileux/Desktop/Galaga/photos/papillon.png", x_spawn, x_final, y_spawn, y_final, speed, movement_pattern,row_id)
        img = pygame.image.load("/home/fileux/Desktop/Galaga/photos/papillon.png").convert_alpha()
        self.image = pygame.transform.scale(img, (55,50))
        self.rect = self.image.get_rect(center=(x_spawn,y_spawn))
        self.can_shoot = FLAG_SHOOT

class Boss(Enemy):
    def __init__(self, x_spawn, x_final, y_spawn, y_final, speed, movement_pattern,row_id=0):
        super().__init__("/home/fileux/Desktop/Galaga/photos/boss.png", x_spawn, x_final, y_spawn, y_final, speed, movement_pattern,row_id)
        img = pygame.image.load("/home/fileux/Desktop/Galaga/photos/boss.png").convert_alpha()
        self.image = pygame.transform.scale(img, (75,75))
        self.rect = self.image.get_rect(center=(x_spawn,y_spawn))

        self.can_shoot = FLAG_SHOOT
        self.health = 2
        self.normal_image = self.image.copy()
        
        img = pygame.image.load("/home/fileux/Desktop/Galaga/photos/boss2.png").convert_alpha()
        self.damaged_image = pygame.transform.scale(img, (75,75))
    
    #gere la 2e vie
    def hit(self, explosion_group):
        self.health -= 1
        if self.health <= 0:
            self.kill_enemy(explosion_group)
            return True
        else:
            self.image = self.damaged_image
            return False

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, bullet_group):
        super().__init__()
        # Image différente pour les balles ennemies (rouge ou autre couleur)
        img = pygame.image.load("/home/fileux/Desktop/Galaga/photos/enemy_bullet.png").convert_alpha()
        img = pygame.transform.scale(img, (20, 20))
        self.image = img
        
        self.rect = self.image.get_rect(center=(x, y))
        
        # Calcul direction 
        dx = target_x - x
        dy = target_y - y
        distance = (dx**2 + dy**2)**0.5
        
        bullet_speed = 19
        
        # ajuste direction
        if distance > 0:
            self.vel_x = (dx / distance) * bullet_speed
            self.vel_y = (dy / distance) * bullet_speed
        else:
            self.vel_x = 0
            self.vel_y = bullet_speed
        
        bullet_group.add(self)
    
    def update(self):
        self.rect.centerx += self.vel_x
        self.rect.centery += self.vel_y
        
        # Supprime si hors écran
        if (self.rect.bottom < 0 or self.rect.top > 1880 or 
            self.rect.right < 0 or self.rect.left > 1080):
            self.kill()

#creation des niveaux
#LEVEL 1
espacement = 100
X_bee = 60
X_boss = 80
X_pap = X_bee
# speed = 12 #speed darrivee (pas meme speed que le mouvement static horizontal)
# def create_level_1():
#     level = []

#     y_spawn = 120
#     #setup horizontal gauche vers droite
#     nombre_bee = 11
#     # row_width_bee = (nombre_bee - 1)*espacement
#     # start_x_bee = (screen_width - row_width_bee) // 2
#     for i in range(nombre_bee):
#         row_id = 1
#         x_final = (i * espacement)
#         x_spawn = -100 - (i*X_bee) #on change le i*X pour actually modifier lespacement
#         y_final = y_spawn
#         level.append({
#             "cnt": 1,#i * 100,
#             "type": Bee,
#             "x_spawn": x_spawn,
#             "x_final": x_final,
#             "y_spawn": y_spawn,
#             "y_final": y_final,
#             "speed": speed,
#             "movement": "horizontal",
#             "row_id": row_id
#         })
    #setup horizontal droite vers gauche
    # y_spawn += 120
    # nombre_boss = 11
    # # row_width_boss = (nombre_boss - 1)*espacement
    # # start_x_boss = (screen_width - row_width_boss) // 2
    # for i in range(nombre_boss):
    #     row_id = 2
    #     x_final = (i * espacement)
    #     x_spawn = (screen_width + 100) + (i*X_boss)
    #     y_final = y_spawn
    #     level.append({
    #         "cnt": 1,#(600) + (i * 100), 
    #         "type": Boss,
    #         "x_spawn": x_spawn,
    #         "x_final": x_final,
    #         "y_spawn": y_spawn,
    #         "y_final": y_final,
    #         "speed": speed,
    #         "movement": "horizontal",
    #         "row_id": row_id
    #     })
    #setup arrive from top en rangee horizontale
    # y_spawn += 120
    # nombre_pap = 10
    # row_width_pap = (nombre_pap - 1)*espacement
    # start_x_pap = (screen_width - row_width_pap) // 2
    # for i in range(nombre_pap):
    #     y_spawn = 0
    #     y_final = 500
    #     row_id = 3
    #     x_final = (start_x_pap + i * espacement)
    #     x_spawn = x_final
    #     level.append({
    #         "cnt": i * 100,
    #         "type": Papillon,
    #         "x_spawn": x_spawn,
    #         "x_final": x_final,
    #         "y_spawn": y_spawn,
    #         "y_final": y_final,
    #         "speed": speed,
    #         "movement": "arrive_from_top",
    #         "row_id": row_id
    # })
    #setup arrive de haut en bas en queue leu leu
    # nombre_pap = 10
    # for i in range(nombre_pap):
    #     row_id = 3
    #     y_spawn = -100 - (i*X_pap)
    #     y_final = 500
    #     x_final = 900
    #     x_spawn = x_final
    #     level.append({
    #         "cnt": 1,#(i * 700),
    #         "type": Papillon,
    #         "x_spawn": x_spawn,
    #         "x_final": x_final,
    #         "y_spawn": y_spawn,
    #         "y_final": y_final,
    #         "speed": speed,
    #         "movement": "arrive_from_top",
    #         "row_id": row_id
    # })
    # #setup arrive de bas en haut en queue leu leu
    # nombre_pap = 10
    # for i in range(nombre_pap):
    #     row_id = 4
    #     y_spawn = (screen_height + 100) + (i*X_pap)
    #     y_final = 700
    #     x_final = 150
    #     x_spawn = x_final
    #     level.append({
    #         "cnt": 1,#(i * 700),
    #         "type": Papillon,
    #         "x_spawn": x_spawn,
    #         "x_final": x_final,
    #         "y_spawn": y_spawn,
    #         "y_final": y_final,
    #         "speed": speed,
    #         "movement": "arrive_from_bottom",
    #         "row_id": row_id
    # })
    # return level

enemy_types = [Bee, Boss, Papillon]
movement_patterns = ["horizontal", "arrive_from_top", "arrive_from_bottom","random","chase"]

y_liste = [40,160,280,400,520,640,760,880,1000,1120]
y_liste2 = [100,220,340,460,580,700,820,940,1060,1180]

def create_random_level(row_id, speed_level, index):
    level = []
    buf_row_id = row_id

    #plus on avance dans les niveau plus il y a de vague
    if index < 2:
        waves = random.randint(6, 10)
    elif index >= 2  and index < 5:
        waves = random.randint(8, 13)
    elif index >= 5 and index <= 7:
        waves = random.randint(10, 15)
    elif index > 7:
        waves = random.randint(15, 20)


    for j in range(waves):
        if index < 2:
            enemy_type = random.choice([Bee,Papillon])
        elif index == 2:
            enemy_type = random.choice([Bee,Papillon,Boss,Bee,Papillon])
        else:
            enemy_type = random.choice(enemy_types)

        direction = random.choice([-1,1])
        if row_id == len(y_liste) + len(y_liste2):
            movement = random.choice(["random","chase"])
        else: #on assigne le mouvement ici

            if index < 1:   #niveau 1
                movement = random.choice(["horizontal","arrive_from_top"])
            elif 3 > index >= 1:    #niveau 2 et 3
                movement = random.choice(["horizontal","arrive_from_top","random","horizontal","arrive_from_top"])
            else:   # niveau 3 et plus
                movement = random.choice(movement_patterns)

        if movement in ["random", "chase"]:
            nbr_ennemi = 1
        else:
            if index <= 1:
                nbr_ennemi = random.randint(3,9)
            else:
                nbr_ennemi = random.randint(6,11)
        

       
        if movement in ["horizontal", "arrive_from_top", "arrive_from_bottom"]:  
            if row_id < len(y_liste): 
                y_final = y_liste[row_id]
            else:
                y_final = y_liste2[row_id - len(y_liste)]
                
        for i in range(nbr_ennemi):
            if enemy_type is Bee or enemy_type is Papillon:
                espace = 60
            elif enemy_type == "Boss":
                espace = 90
            else:
                espace = 60

            if movement == "horizontal":
                if direction == -1: #vers gauche
                    x_spawn = (screen_width + 100) + (i*espace)
                else: #vers la droite
                    x_spawn = -100 - (i*espace)

                x_final = i*espacement
                y_spawn = y_final
                x_final = i * espacement
                
            elif movement == "arrive_from_top":
                y_spawn = -100 - (i*espace)
                if i == 0:
                    x_final = random.choice([80,180,900,1000])
                x_spawn = x_final
                
            elif movement == "arrive_from_bottom":
                y_spawn = (screen_height + 100) + (i*espace)
                if i == 0:
                    x_final = random.choice([80,180,900,1000])
                x_spawn = x_final

            elif movement in ["random", "chase"]:
                spawn_side = random.choice(['top','bottom','left','right'])
                if spawn_side == 'top':
                    # if i == 0:
                    x_spawn = random.randint(100,screen_width - 100)
                    y_final = random.randint(100,screen_height - 400)
                    y_spawn = -100 - (i*espace)
                    x_final = x_spawn
                elif spawn_side == 'bottom':
                    y_spawn = screen_height + 100
                    # if i == 0:
                    y_final = random.randint(100,screen_height - 400)
                    x_spawn = random.choice([random.randint(100,200),random.randint(screen_width - 200,screen_width - 100)])
                    x_final = x_spawn
                elif spawn_side == 'left':
                    x_spawn = -100 - (i*espace)
                    # if i == 0:
                    x_final = random.randint(100, screen_width - 100)
                    y_spawn = random.randint(100, screen_height - 500)
                    y_final = y_spawn 
                elif spawn_side == 'right':
                    x_spawn = screen_width + 100 + (i*espace)
                    # if i == 0:
                    x_final = random.randint(100, screen_width - 100)
                    y_spawn = random.randint(100, screen_height - 500)
                    y_final = y_spawn
#row id trop grand pour pas prendre emplacement rangee, si en mode random ou chase
            if movement in ["random", "chase"]:
                special_row_id = 1000 + j  
            else:
                special_row_id = buf_row_id
            level.append({
                "cnt": 1,
                "type": enemy_type,
                "x_spawn": x_spawn,
                "x_final": x_final,
                "y_spawn": y_spawn,
                "y_final": y_final,
                "speed": speed_level, 
                "movement": movement,
                "row_id": special_row_id
            })
        if movement not in ["random", "chase"]:
            row_id += 1
        buf_row_id = row_id
    return level


#tableau de niveau:
NBR_LEVEL = 50
levels = [[] for _ in range(NBR_LEVEL)]
speed_level = 0
for i in range(NBR_LEVEL):
    row_id = 0
    if i < 2:
        speed_level = random.randint(8, 16)
    elif i >= 2 and i < 5:
        speed_level = random.randint(10, 20)
    elif i >= 5 and i < 10:
        speed_level = random.randint(15, 22)
    elif i >= 10:
        speed_level = random.randint(20, 22)
    level = create_random_level(row_id, speed_level, i)
    levels[i] = level

#groupes
player = Player("/home/fileux/Desktop/Galaga/photos/fighter.png",pos=(540,1650))
player_group = pygame.sprite.Group(player)
bullet_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
enemy_bullet_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
powerup_group = pygame.sprite.Group()

#init groupe detoile
init_stars()

#init joystick et bouton
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

level_index=0
level_start_time = pygame.time.get_ticks()
current_level = 0
enemy_direction = 1
level_done = False
game_won = False
game_over = False
row_directions = {}
timer_spawn = 0
counter_lenght = 0
counter_spawn = 0
current_wave_spawning = 1
wave_complete = False
wave_start_time = 0
flag_game_over = 0
flag_new_highscore = 0

STATE_PLAYING       = "PLAYING"
STATE_LEVEL_INTRO   = "LEVEL_INTRO"
STATE_LEVEL_SUMMARY = "LEVEL_SUMMARY"
state = STATE_LEVEL_INTRO
intro_start_ms = pygame.time.get_ticks()
summary_start_ms = 0
level_kills = 0
level_kills_for_accuracy = 0
level_shots = 0

#audio
Audio.init_bank()
#Audio.play("stage_start")

#loop principale
running = True
while running:
    current_time = pygame.time.get_ticks()
    
    # JOYSTICK
     #mouvement joueur * un chiffre pour augmenter vitesse joueur
    if len(joysticks) > 0 and not game_over:
        x = round(pygame.joystick.Joystick(0).get_axis(0))*35 #0 est laxe x sur manette de ps4
        y = round(pygame.joystick.Joystick(0).get_axis(1))*35 #1 est laxe y sur manette de ps4
        player.move(x,y)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
        if event.type == pygame.JOYBUTTONDOWN and getattr(event,"button",None) == 0 and not game_over and state == STATE_PLAYING:
            player.shoot(bullet_group)
            Audio.play("shoot")
            #print(event)
            #bouton 0 = bouton X ps4

    #donne les caracteristique de lennemi du niveau en cours
    if not game_over and state == STATE_PLAYING:
        if current_level < len(levels) and level_index < len(levels[current_level]) and not game_over:
            
            if current_level >= len(levels) or len(levels[current_level]) == 0:
                game_won = True
                continue #on termine literation de la boucle
            enemy_data = levels[current_level][level_index]
            current_time = pygame.time.get_ticks()
        
            # Vérifier si on change de vague (row_id différent)
            if enemy_data["row_id"] != current_wave_spawning:
                if not wave_complete:
                    wave_complete = True
                    wave_start_time = current_time

                # delai entre chauq vague dennemi (au hazard ou non)
                if enemy_data["row_id"] < 2:
                    wave_delay_between = 800
                else:
                    match current_level:
                        case current_level if current_level < 2:
                            wave_delay_between = random.randint(3000,8000)
                        case current_level if 4 > current_level >= 2:
                            wave_delay_between = random.randint(3000,7000)
                        case current_level if 5 > current_level >= 4:
                            wave_delay_between = random.randint(2500,6500)
                        case current_level if 8 > current_level >= 5:
                            wave_delay_between = random.randint(1000,6500)
                        case current_level if current_level >= 8:
                            wave_delay_between = random.randint(500,6000)

                if current_time - wave_start_time >= wave_delay_between:
                    current_wave_spawning = enemy_data["row_id"]
                    wave_complete = False
                    counter_lenght = 0
                    counter_spawn = 0

            if enemy_data["row_id"] == current_wave_spawning and not wave_complete:
                counter_spawn += enemy_data["cnt"]
                
                #probabilite davoir un power up
                try_spawn_powerup(current_time)


                if counter_spawn <= counter_lenght + 1: #or enemy_data["row_id"] >= 1000:                
                    enemy = enemy_data["type"](
                        enemy_data["x_spawn"], enemy_data["x_final"], enemy_data["y_spawn"],
                        enemy_data["y_final"], enemy_data["speed"], enemy_data["movement"], enemy_data["row_id"])
                    enemy_group.add(enemy)
                    counter_lenght = len(enemy_group)
                    
                    row_id = enemy_data["row_id"]

                    #pour bien espacer en y
                    if enemy.movement_pattern == "arrive_from_top":
                        if enemy.rect.centery < enemy.y_final:
                            enemy.rect.centery = enemy_data["y_spawn"]

                    if enemy.movement_pattern == "arrive_from_bottom":
                        if enemy.rect.centery > enemy.y_final:
                            enemy.rect.centery = enemy_data["y_spawn"]
                    #initialisation direction
                    if row_id not in row_directions:
                        if enemy_data["x_spawn"] < enemy_data["x_final"]:
                            row_directions[row_id] = 1
                        elif enemy_data["x_spawn"] > enemy_data["x_final"]:
                            row_directions[row_id] = -1
                        else:
                            row_directions[row_id] = 1
                    if enemy.movement_pattern in ["arrive_from_top","arrive_from_bottom"]:
                        if enemy_data["x_spawn"] > (screen_width/2):
                            row_directions[row_id] = -1  # Commence vers la gauche
                        if enemy_data["x_spawn"] < (screen_width/2):
                            row_directions[row_id] = 1  # Commence vers la droite
                    
                    level_index += 1

    # kill ennemi, explosion et bullet disparait
    if state == STATE_PLAYING and not game_over:
        for bullet in list(bullet_group):
            got_orb = False
            for orb in list(powerup_group):
                if bullet.rect.colliderect(orb.rect):
                    bullet.kill()
                    got_orb = True
                    Audio.play("autre")
                    level_kills_for_accuracy += 1
                    if orb.hit_by_player():
                        twin_active = True
                        Audio.play("power_up")
                    break             
            if got_orb:
                continue

        for bullet in bullet_group:
            for enemy in enemy_group:
                if enemy.alive and bullet.rect.colliderect(enemy.rect):
                    #verifie si cest un boss pour gerer la 2e vie
                    if hasattr(enemy,'hit'): #est un boss
                        killed = enemy.hit(explosion_group)
                        if killed:
                            level_kills += 1
                            score += enemy_points(enemy)
                            #audio boss vie 2 mort
                            Audio.play("boss_kill2")
                        else:
                            #audio boss vie 1 mort
                            level_kills_for_accuracy += 1
                            Audio.play("boss_kill")
                    else:      #autre ennemi (bee, pap)          
                        enemy.kill_enemy(explosion_group) 
                        level_kills += 1
                        score += enemy_points(enemy)
                        #audio mort
                        if isinstance(enemy, Bee):
                            Audio.play("bee_kill")
                        elif isinstance(enemy, Papillon):
                            Audio.play("pap_kill")
                        else:
                            Audio.play("autre")
                    bullet.kill()
                    break 

    if state == STATE_PLAYING and not game_over:         
        for enemy in enemy_group:         
            if enemy.movement_pattern == "arrive_from_top":
                # Descend jusqu'à la position Y finale
                if enemy.rect.centery < enemy.y_final:
                    enemy.rect.centery += enemy.initial_speed
                else:
                    enemy.rect.centery = enemy.y_final
                    enemy.movement_pattern = "horizontal"  # Change pour horizontal après
            elif enemy.movement_pattern == "arrive_from_bottom":
                # Monte jusqu'à la position Y finale  
                if enemy.rect.centery > enemy.y_final:
                    enemy.rect.centery -= enemy.initial_speed
                else:
                    enemy.rect.centery = enemy.y_final
                    enemy.movement_pattern = "horizontal"  # Change pour horizontal après
            
            elif enemy.movement_pattern == "random" or enemy.movement_pattern == "chase":
                dx = enemy.x_final - enemy.rect.centerx
                dy = enemy.y_final - enemy.rect.centery
                distance = (dx*dx + dy*dy)**0.5
                
                if distance < 20: 
                    enemy.rect.centerx = enemy.x_final
                    enemy.rect.centery = enemy.y_final
                    if enemy.movement_pattern == "random":
                        enemy.movement_pattern = "random_arrived"
                    elif enemy.movement_pattern == "chase":
                        enemy.movement_pattern = "chase_arrived"
                else:
                    # Mouvement proportionnel à la distance
                    speed = min(enemy.initial_speed, distance)  # Ralentit en approchant
                    
                    if distance > 0:
                        move_x = (dx / distance) * speed * 2  #ajuste vitesse arrivee
                        move_y = (dy / distance) * speed * 2
                        enemy.rect.centerx += move_x
                        enemy.rect.centery += move_y
                
                enemy.rect.clamp_ip(pygame.Rect(0, 0, screen_width, screen_height))       
            
            elif enemy.movement_pattern == "random_arrived":

                if not hasattr(enemy, 'group_dx'):
                    enemy.group_dx = random.choice([-7,-6,-5,-1,1,5,6,7])
                    enemy.group_dy = random.choice([-7,-6,-5,-1,1,5,6,7])
                    enemy.change_timer = 0
                    enemy.change_delay = random.randint(0, 60)
                    
                # Change de direction périodiquement
                enemy.change_timer += 1
                if enemy.change_timer >= enemy.change_delay:
                    enemy.group_dx = random.choice([-7,-6,-5,-1,1,5,6,7])
                    enemy.group_dy = random.choice([-7,-6,-5,-1,1,5,6,7])
                    enemy.change_timer = 0
                    enemy.change_delay = random.randint(0, 60)
                
                # Rebondit sur les bords
                enemy_new_x = enemy.rect.centerx + enemy.group_dx
                enemy_new_y = enemy.rect.centery + enemy.group_dy
                
                if enemy_new_x <= 0 or enemy_new_x >= screen_width - 80:
                    enemy.group_dx *= -1
                if enemy_new_y <= 50 or enemy_new_y >= screen_height - 100:
                    enemy.group_dy *= -1
                
                
                enemy.rect.centerx += enemy.group_dx * 2.5
                enemy.rect.centery += enemy.group_dy * 2.5
                
                enemy.rect.clamp_ip(pygame.Rect(0, 0, screen_width, screen_height))
            
            #GESTION CHASE    
            elif enemy.movement_pattern == "chase_arrived":
                dx = player.rect.centerx - enemy.rect.centerx
                dy = player.rect.centery - enemy.rect.centery
                distance = (dx**2 + dy**2)**0.5
                
                if distance > 0:
                    base_speed = 3
                    chase_speed = base_speed * 4.5 #intensite du chase
                    
                    # Mouvement vers le joueur
                    vel_x = (dx / distance) * chase_speed
                    vel_y = (dy / distance) * chase_speed
                    enemy.rect.centerx += vel_x
                    enemy.rect.centery += vel_y
                    
                    # Garde l'ennemi dans l'écran
                    enemy.rect.clamp_ip(pygame.Rect(0, 0, screen_width, screen_height))
    
    #probabilite de changer un ennemi en chase
    for enemy in enemy_group:  
        if (enemy.movement_pattern in ["horizontal","arrive_from_top","arrive_from_bottom"] and 
            enemy.alive and not enemy.has_transformed): 
            if current_level >= 7:
                if random.random() < 0.0008:
                    enemy.movement_pattern = "chase_arrived" 
                    enemy.has_transformed = True
            elif 7 > current_level > 3:
                if random.random() < 0.00035:
                    enemy.movement_pattern = "chase_arrived" 
                    enemy.has_transformed = True
            else:
                if random.random() < 0.0002:
                    enemy.movement_pattern = "chase_arrived" 
                    enemy.has_transformed = True

    #GESTION HORIZONTAL    
    if len(enemy_group) > 0 :
        rows = {}
        for enemy in enemy_group:
            if enemy.row_id not in rows:
                rows[enemy.row_id] = []
            rows[enemy.row_id].append(enemy)
        
        # Traite chaque rangée indépendamment
        for row_id, enemies_in_row in rows.items():
            if not enemies_in_row:
                continue 
            
            # Calcule la vitesse ACTUELLE de cette rangée (pas la vitesse maximale)
            row_speed = 3
            speed_set = False
            for enemy in enemies_in_row:
                if not speed_set:
                    row_speed = enemy.formation_speed if enemy.formation_speed else enemy.initial_speed
                    speed_set = True
                    break
        
            row_direction = row_directions[row_id]
            
            # Trouve les ennemis les plus à gauche et à droite DE CETTE RANGÉE
            leftmost = min(enemies_in_row, key=lambda e: e.rect.left)
            rightmost = max(enemies_in_row, key=lambda e: e.rect.right)

            will_hit_left = row_direction == -1 and leftmost.rect.left + (row_speed * row_direction) <= 0
            will_hit_right = row_direction == 1 and rightmost.rect.right + (row_speed * row_direction) >= screen_width

            # Change la direction de CETTE RANGÉE seulement
            if will_hit_left or will_hit_right:
                row_directions[row_id] *= -1
                row_direction = row_directions[row_id]
                
                # Change la vitesse au premier mur pour cette rangée (UNE SEULE FOIS)
                for enemy in enemies_in_row:
                    if not enemy.has_hit_wall:
                        enemy.has_hit_wall = True
                        enemy.formation_speed = 4 #speed en mode static horizontal

            # Déplace tous les ennemis de CETTE RANGÉE avec la MÊME vitesse
            current_row_speed = enemies_in_row[0].formation_speed if enemies_in_row[0].formation_speed else enemies_in_row[0].initial_speed
            for enemy in enemies_in_row:
                if enemy.movement_pattern == "horizontal":
                    enemy.rect.x += current_row_speed * row_direction

   # Collision joueur-ennemi
    if not game_over:
        twin_r = twin_rect_current() if twin_active else None
        for enemy in list(enemy_group):
            if not enemy.alive:
                continue
            if player.invulnerable:
                continue
            hit_main = player.rect.colliderect(enemy.rect)
            hit_twin = (twin_active and twin_r is not None and twin_r.colliderect(enemy.rect))
            if hit_main:
                if twin_active == True:
                    Audio.play("player_hit")
                    deactivate_twin()
                    player.take_damage()#pour invinsibilite
                    continue
                else:
                    if player.take_damage():
                        Audio.play("player_hit")
                        if player.lives <= 0:
                            game_over = True
                            Audio.play("game_over")
                    enemy.kill_enemy(explosion_group)
                    continue  # ennemi déjà géré
            if hit_twin:
                # Twin "prend" le coup -> on perd le power-up, pas de vie
                Audio.play("player_hit")
                deactivate_twin()
                player.take_damage()#pour invinsibilite
                enemy.kill_enemy(explosion_group)
                continue
    
    # ennemy shoot
    if not game_over:
        for enemy in enemy_group:
            enemy.shoot(enemy_bullet_group, player)
    
    # Collision balles ennemies - joueur 
    if not game_over:
        #le twin peut absorber une balle (désactive le power-up)
        twin_r = twin_rect_current() if twin_active else None
        for bullet in list(enemy_bullet_group):
            hit_main = player.rect.colliderect(bullet.rect)
            hit_twin = (twin_active and twin_r is not None and twin_r.colliderect(bullet.rect))
            if hit_main:
                if twin_active == True:
                    Audio.play("player_hit")
                    deactivate_twin()
                    player.take_damage()#pour invinsibilite
                    bullet.kill()
                    continue
                else:
                    if player.take_damage():
                        Audio.play("player_hit")
                        if player.lives <= 0:
                            game_over = True
                            Audio.play("game_over")
                bullet.kill()
                continue
            if hit_twin:
                Audio.play("player_hit")
                deactivate_twin()
                player.take_damage()#pour invinsibilite
                bullet.kill()
                continue

    #updates
    player.update()
    bullet_group.update()
    enemy_bullet_group.update()
    explosion_group.update()

    alive_count = sum(1 for enemy in enemy_group if enemy.alive)
    if not game_over:
        if state == STATE_PLAYING and level_index >= len(levels[current_level]) and alive_count == 0 and not level_done:
            level_done = True
            state = STATE_LEVEL_SUMMARY
            summary_start_ms = pygame.time.get_ticks()
            # Nettoyage complet du niveau
            enemy_group.empty()
            bullet_group.empty()
            enemy_bullet_group.empty()
            explosion_group.empty()
            powerup_group.empty()   

        if state == STATE_LEVEL_SUMMARY:
            if current_time - summary_start_ms >= SUMMARY_MS:  
                current_level += 1
                if current_level >= len(levels):
                    game_won = True
                else:
                    level_kills = 0
                    level_kills_for_accuracy = 0
                    level_shots = 0
                    level_index = 0
                    level_start_time = pygame.time.get_ticks()
                    level_done = False
                    row_directions.clear()
                    current_wave_spawning = 1
                    wave_complete = False
                    counter_lenght = 0
                    counter_spawn = 0
                    # bascule vers écran d'intro du prochain niveau
                    state = STATE_LEVEL_INTRO
                    intro_start_ms = current_time

        elif state == STATE_LEVEL_INTRO:
            if current_time - intro_start_ms >= INTRO_MS:
                state = STATE_PLAYING
                if current_level == 0:
                    Audio.play("game_start")
                else:
                    Audio.play("stage_start")

    screen.fill((0, 0, 0))
    update_and_draw_stars(screen)
    player.draw(screen)

    if twin_active:
        tx = twin_centerx_for_draw()
        twin_rect_draw = player.image.get_rect(center=(tx,player.rect.centery))
        screen.blit(player.image, twin_rect_draw)
    player.draw_lives(screen)
    bullet_group.draw(screen)
    enemy_bullet_group.draw(screen)

    #on dessine juste les vivants
    for enemy in enemy_group:
        if enemy.alive:
            screen.blit(enemy.image,enemy.rect)

    explosion_group.draw(screen)
    draw_score(screen,score)
    powerup_group.draw(screen)

    if state == STATE_LEVEL_SUMMARY and not game_over:
        draw_outline_text(screen, f"ENEMIES ELIMINATED : {str(level_kills)}", info_font,
                          (screen_width//2, screen_height//2 - 40), LBLUE, LBLUE, pad=1)
        if level_shots != 0:
            accuracy = str(round(((level_kills+level_kills_for_accuracy)/level_shots)*100,1))
        else:
            accuracy = str(round(0))
        draw_outline_text(screen, f"ACCURACY : {accuracy} %", info_font,
                          (screen_width//2, screen_height//2 + 40), LBLUE, LBLUE, pad=1)

    elif state == STATE_LEVEL_INTRO:
        draw_outline_text(screen, f"LEVEL : {current_level + 1}", title_font,
                          (screen_width//2, screen_height//2), LBLUE, LBLUE, pad=1)


    #gestion highscore et son affichage
    if game_over:
        screen.blit(overlay, (0, 0))

        with open("/home/fileux/Desktop/Galaga/highscore","r",encoding="utf-8") as f:
            mots = f.read().split()
        old_highscore_string = mots[0] if mots else None
        old_highscore = int(old_highscore_string)
        if score > old_highscore:
            flag_new_highscore = 1

        if flag_new_highscore == 1:
            new_highscore = str(score)
            with open("/home/fileux/Desktop/Galaga/highscore","w",encoding="utf-8") as f:
                f.write(new_highscore)
                new_highscore_text = new_highscore_font.render(f"New Highscore !",True,(255,215,0))
                new_highscore_rect = new_highscore_text.get_rect(center=((screen_width // 2), (screen_height // 2)+200))
                screen.blit(new_highscore_text, new_highscore_rect)

                new_highscore_text = new_highscore_font.render(f"{new_highscore}",True,(255,215,0))
                new_highscore_number_rect = new_highscore_text.get_rect(center=((screen_width // 2), (screen_height // 2)+260))
                screen.blit(new_highscore_text,new_highscore_number_rect)
        else: 
            old_highscore_text = new_highscore_font.render(f"Current Highscore",True,(255,215,0))
            old_highscore_rect = old_highscore_text.get_rect(center=((screen_width // 2), (screen_height // 2)+200))
            screen.blit(old_highscore_text, old_highscore_rect)

            old_highscore_text = new_highscore_font.render(f"{old_highscore}",True,(255,215,0))
            old_highscore_number_rect = old_highscore_text.get_rect(center=((screen_width // 2), (screen_height // 2)+260))
            screen.blit(old_highscore_text, old_highscore_number_rect)

        screen.blit(game_over_text, game_over_rect)
        draw_score(screen,score)
            
    pygame.display.update()
    clock.tick(180)
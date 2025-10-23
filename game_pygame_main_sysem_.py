import math, random, pygame
from pygame.locals import *

# ==== Embedded background (from backround.py) ====
# Colors
MOUNTAIN_LIGHT = (210, 190, 160)
MOUNTAIN_DARK = (70, 100, 150)
GRASS = (100, 150, 80)
TREE = (40, 90, 50)
GROUND = (90, 60, 40)
ROCK = (60, 70, 80)
CLOUD = (240, 245, 250)
SUN_COLOR = (255, 230, 150)
MOON_COLOR = (230, 230, 255)

# Clouds & stars state
clouds = [
    {"x": 50, "y": 80, "speed": 0.2, "size": 1.2},
    {"x": 220, "y": 60, "speed": 0.15, "size": 1.0},
    {"x": 450, "y": 100, "speed": 0.25, "size": 1.4},
    {"x": 680, "y": 70, "speed": 0.18, "size": 1.1},
    {"x": 900, "y": 90, "speed": 0.22, "size": 1.3},
]
stars = []

def ensure_bg_init(surface):
    global stars
    if not stars:
        W, H = surface.get_size()
        stars = [(random.randint(0, W), random.randint(0, H//2)) for _ in range(180)]

def lerp_color(c1, c2, t):
    return (int(c1[0] + (c2[0]-c1[0])*t),
            int(c1[1] + (c2[1]-c1[1])*t),
            int(c1[2] + (c2[2]-c1[2])*t))

def get_sky_color(t):
    # day-night blend
    day = (135, 206, 235)
    dusk= (255, 160, 122)
    night=(10, 15, 35)
    if t < 0.5:
        return lerp_color(day, dusk, t/0.5)
    else:
        return lerp_color(dusk, night, (t-0.5)/0.5)

bg_offset_x = 0.0  # updated every frame from camera offset

def draw_scene_bg(surface, sky_color, sun_y, moon_y, t_frac):
    ensure_bg_init(surface)
    global bg_offset_x
    W, H = surface.get_size()
    surface.fill(sky_color)

    # Sun & Moon (slight parallax)
    pygame.draw.circle(surface, SUN_COLOR, (int(W*0.2 - bg_offset_x*0.1), int(sun_y)), 28)
    pygame.draw.circle(surface, MOON_COLOR,(int(W*0.75 - bg_offset_x*0.1), int(moon_y)), 20, 2)

    # Stars at night
    if t_frac > 0.5:
        alpha = int(255 * (t_frac-0.5)/0.5)
        st = pygame.Surface((W,H), pygame.SRCALPHA)
        for sx, sy in stars:
            if sy < H*0.6:
                st.set_at((sx%W, sy), (255,255,255, alpha))
        surface.blit(st, (0,0))

    # Mountains layers (parallax)
    def _mx(x, fac):
        return x - bg_offset_x*fac
    pygame.draw.polygon(surface, MOUNTAIN_DARK, [(_mx(0,0.20), H*0.75), (_mx(W*0.25,0.20), H*0.55), (_mx(W*0.5,0.20), H*0.76), (_mx(W*0.8,0.20), H*0.6), (_mx(W,0.20), H*0.78), (_mx(W,0.20), H), (_mx(0,0.20), H)])
    pygame.draw.polygon(surface, MOUNTAIN_LIGHT,[(_mx(0,0.35), H*0.85), (_mx(W*0.25,0.35), H*0.65), (_mx(W*0.48,0.35), H*0.88), (_mx(W*0.7,0.35), H*0.7), (_mx(W,0.35), H*0.9), (_mx(W,0.35), H), (_mx(0,0.35), H)])

    # Ground (parallax)
    gx = int(-bg_offset_x*0.5) % W
    pygame.draw.rect(surface, GRASS, (gx - W, int(H*0.85), W, int(H*0.15)))
    pygame.draw.rect(surface, GRASS, (gx,     int(H*0.85), W, int(H*0.15)))

    # Trees (tuned v2) — canopy anchored to trunk top
    # Config
    TREE_SPACING   = 120
    TREE_MIN_H     = 36    # slightly taller minima for better trunk-canopy balance
    TREE_MAX_H     = 64
    TRUNK_W        = 10
    TRUNK_COLOR    = (70, 40, 25)
    CANOPY_COLOR_1 = TREE
    CANOPY_COLOR_2 = (50, 110, 65)
    CANOPY_COLOR_3 = (35, 80, 45)
    TRUNK_H_RATIO  = 0.5   # trunk is 50% of total tree height
    CANOPY_OVL     = 6     # small overlap into trunk to avoid gaps

    def _tree_jitter(i):
        # stable pseudo-random horizontal jitter
        return ((i * 37) % 91) - 45

    def _draw_canopy_triangle(surface, color, x, base_y, width, height):
        left  = (x - width//2, base_y)
        apex  = (x,            base_y - height)
        right = (x + width//2, base_y)
        pygame.draw.polygon(surface, color, [left, apex, right])

    def _draw_tree(surface, x, ground_y, total_h):
        # trunk
        trunk_h = max(12, int(total_h * TRUNK_H_RATIO))
        trunk_top = int(ground_y - trunk_h)
        pygame.draw.rect(surface, TRUNK_COLOR, (x - TRUNK_W//2, trunk_top, TRUNK_W, trunk_h))

        # canopy stack anchored at trunk top (no floating)
        canopy_h = max(12, total_h - trunk_h + CANOPY_OVL)
        base_y   = trunk_top + CANOPY_OVL  # overlap into trunk

        w1 = int(canopy_h * 1.10)
        w2 = int(canopy_h * 0.85)
        w3 = int(canopy_h * 0.60)
        h1 = int(canopy_h * 0.40)
        h2 = int(canopy_h * 0.55)
        h3 = int(canopy_h * 0.70)

        _draw_canopy_triangle(surface, CANOPY_COLOR_1, x, base_y, w1, h1)
        _draw_canopy_triangle(surface, CANOPY_COLOR_2, x, base_y - int(h1*0.35), w2, h2)
        _draw_canopy_triangle(surface, CANOPY_COLOR_3, x, base_y - int(h1*0.65) - int(h2*0.35), w3, h3)

    ground_y = int(H*0.85)
    # Place trees across a double-width strip for seamless wrap
    i = 0
    x = 0
    base_offset = int(-bg_offset_x*0.5)
    while x < W + TREE_SPACING:
        jitter = _tree_jitter(i)
        px = (x + 8 + jitter + base_offset) % (W + TREE_SPACING)
        h  = TREE_MIN_H + (abs(jitter) % (TREE_MAX_H - TREE_MIN_H + 1))
        _draw_tree(surface, int(px), ground_y, int(h))
        x += TREE_SPACING
        i += 1

# Clouds
    for c in clouds:
        cx = int((c["x"] - bg_offset_x*0.4) % (W+120)) - 60
        cy = int(c["y"])
        s  = c["size"]
        pygame.draw.ellipse(surface, CLOUD, (cx-30*s, cy-12*s, 60*s, 24*s))
        pygame.draw.ellipse(surface, CLOUD, (cx,       cy-16*s, 50*s, 30*s))
        pygame.draw.ellipse(surface, CLOUD, (cx+25*s,  cy-12*s, 60*s, 24*s))

def move_clouds_bg(surface):
    W, H = surface.get_size()
    for c in clouds:
        c["x"] += c["speed"]
        if c["x"] > W + 120:
            c["x"] = -120


# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 960, 640
FPS = 60
GRAVITY = 0.8
PLAYER_SPEED = 4.6
PLAYER_JUMP_POWER = 15
BULLET_SPEED = 20
ENEMY_SPEED = 1.9
ENEMY_COLLIDE_TICK_DAMAGE = 1
ATTACK_RANGE = 64
WHITE = (255,255,255)
BG = (18,18,24)

# Mouse→spine control (Bow Master feel)
LEAN_SENS = 0.06
LEAN_DECAY = 0.88
LEAN_CLAMP = 22
HEAD_BOB = 3

# Human proportions (px)
HEAD_H = 18
NECK_H = 4
TORSO_H = 20
PELVIS_H = 10
UP_ARM = 19
LO_ARM = 1
UP_LEG = 1
LO_LEG = 10

# IK/animation tuning
ARM_THICK = 5
LEG_THICK = 6
ARM_DAMP = 0.22
ARM_SWAY = 0.35
ARM_GRAVITY = 3.5
BOW_PULL = 8
SWORD_SWING_DEG = 26

WALK_FREQ = 10.0
WALK_AMP = 10.0

# Mount (horse) settings
HORSE_SPEED = 10
HORSE_JUMP = 18
MOUNT_RANGE = 120              # was 54 → make mounting easier
MOUNT_COOLDOWN_MS = 200        # a bit more responsive

# Enemy AI
RANGED_DIST = 750
MELEE_DIST = 750
ENEMY_SHOOT_CD = 750
ENEMY_SWING_CD = 750

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Human Enemies + Horse Mount (E fix) — dmg15")
clock = pygame.time.Clock()
font = pygame.font.SysFont("", 18)
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

def clamp(v, a, b):
    return max(a, min(b, v))

class Camera:
    def __init__(self,w,h):
        self.offset=pygame.Vector2(0,0); self.w=w; self.h=h
    def apply(self, r):
        return r.move(-self.offset.x,-self.offset.y)
    def update(self, t):
        self.offset.x = max(0, min(t.centerx - WIDTH//2, self.w - WIDTH))
        self.offset.y = max(0, min(t.centery - HEIGHT//2, self.h - HEIGHT))

class Platform(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h):
        super().__init__()
        self.image=pygame.Surface((w,h)); self.image.fill((40,40,55))
        self.rect=self.image.get_rect(topleft=(x,y))

class IKArm:
    def __init__(self, L1, L2, thick):
        self.L1=L1; self.L2=L2; self.thick=thick
        self.a1=0.0; self.a2=0.0
        self.hand=pygame.Vector2(0,0)
    def _solve(self, target):
        dist = target.length()
        mx = self.L1 + self.L2
        if dist > mx:
            target = target.normalize()*mx
            dist=mx
        c2 = clamp((dist*dist - self.L1*self.L1 - self.L2*self.L2)/(2*self.L1*self.L2), -1,1)
        t2 = math.acos(c2)
        k1 = self.L1 + self.L2*c2
        k2 = self.L2*math.sin(t2)
        t1 = math.atan2(target.y, target.x) - math.atan2(k2, k1)
        return t1, t2
    def update(self, shoulder_local, target_local, damp=0.22):
        t1,t2 = self._solve(target_local)
        self.a1 = (1-damp)*self.a1 + damp*t1
        self.a2 = (1-damp)*self.a2 + damp*t2
        x1 = self.L1*math.cos(self.a1); y1 = self.L1*math.sin(self.a1)
        x2 = x1 + self.L2*math.cos(self.a1+self.a2)
        y2 = y1 + self.L2*math.sin(self.a1+self.a2)
        self.hand.update(shoulder_local.x + x2, shoulder_local.y + y2)
    def _quad(self, a,b,th):
        d=b-a
        if d.length_squared()==0: n=pygame.Vector2(0,0)
        else: n = pygame.Vector2(-d.y,d.x).normalize()*(th/2)
        return [a+n,a-n,b-n,b+n]
    def draw(self, surf, shoulder_local, color=(210,180,120)):
        p0 = pygame.Vector2(shoulder_local.x, shoulder_local.y)
        p1 = pygame.Vector2(p0.x + self.L1*math.cos(self.a1),
                            p0.y + self.L1*math.sin(self.a1))
        p2 = pygame.Vector2(p1.x + self.L2*math.cos(self.a1+self.a2),
                            p1.y + self.L2*math.sin(self.a1+self.a2))
        pygame.draw.polygon(surf,color,self._quad(p0,p1,self.thick))
        pygame.draw.polygon(surf,color,self._quad(p1,p2,self.thick))
        j=2
        pygame.draw.rect(surf,(160,140,100),(p1.x-j,p1.y-j,2*j,2*j))
        pygame.draw.rect(surf,(230,210,160),(p2.x-j,p2.y-j,2*j,2*j))

class Horse(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((84, 54), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (120,90,60), (10,20,64,24))
        pygame.draw.rect(self.image, (120,90,60), (58,12,16,12))
        pygame.draw.rect(self.image, (90,70,50), (70,10,12,12))
        for lx in (18, 30, 58, 70):
            pygame.draw.rect(self.image, (90,70,50), (lx, 42, 6, 12))
        self.rect = self.image.get_rect(topleft=(x,y))
        self.base_image = self.image.copy()
        self.facing = 1
        self.vel = pygame.Vector2(0,0)
        self.on_ground = False
        self.rider = None

    def update(self, plats):
        self.vel.y = min(30, self.vel.y + GRAVITY)
        self.rect.x += int(self.vel.x)
        self._collide(self.vel.x, 0, plats)
        self.rect.y += int(self.vel.y)
        self.on_ground = False
        self._collide(0, self.vel.y, plats)
        # Face movement direction
        if self.vel.x > 0.1:
            self.facing = 1
        elif self.vel.x < -0.1:
            self.facing = -1
        self.image = self.base_image if self.facing == 1 else pygame.transform.flip(self.base_image, True, False)

    def _collide(self, vx, vy, plats):
        for p in plats:
            if self.rect.colliderect(p.rect):
                if vx > 0:
                    self.rect.right = p.rect.left
                if vx < 0:
                    self.rect.left = p.rect.right
                if vy > 0:
                    self.rect.bottom = p.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                if vy < 0:
                    self.rect.top = p.rect.bottom
                    self.vel.y = 0

    def seat_world(self):
        return pygame.Vector2(self.rect.left + 36, self.rect.top + 8)

class Humanoid(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.canvas = pygame.Surface((64,96), pygame.SRCALPHA)
        self.image = self.canvas.copy()
        self.rect = self.image.get_rect(topleft=(x,y))
        self.base_image = self.image.copy()
        self.facing = 1
        self.vel = pygame.Vector2(0,0)
        self.on_ground=False
        self.health=100
        self.facing=1
        self.weapon="sword"
        self.attack_cd=0
        self.shoot_cd=0
        self.attack_phase=0.0
        self.lean_vec=pygame.Vector2(0,0)
        self.spine_deg=0.0
        self.head_deg=0.0
        self.r_arm = IKArm(UP_ARM, LO_ARM, ARM_THICK)
        self.l_arm = IKArm(UP_ARM, LO_ARM, ARM_THICK)
        self.walk_t = 0.0
        self.mounted = False
        self.mount = None

    def _apply_mouse_lean(self, mouse_rel): pass
    def _aim_dir_from_lean(self):
        x=self.facing; y=-math.sin(math.radians(self.spine_deg))
        v=pygame.Vector2(x,y)
        return v if v.length()==0 else v.normalize()
    def _collide(self, vx, vy, plats):
        for p in plats:
            if self.rect.colliderect(p.rect):
                if vx>0: self.rect.right = p.rect.left
                if vx<0: self.rect.left  = p.rect.right
                if vy>0: self.rect.bottom= p.rect.top; self.vel.y=0; self.on_ground=True
                if vy<0: self.rect.top   = p.rect.bottom; self.vel.y=0
    def _pelvis_pos(self):
        torso_y = 16 + HEAD_H + NECK_H + int(-math.sin(math.radians(self.spine_deg))*1)
        pelvis_y = torso_y + TORSO_H
        return pygame.Vector2(32, pelvis_y)
    def _shoulders_pos(self):
        torso_y = 16 + HEAD_H + NECK_H + int(-math.sin(math.radians(self.spine_deg))*1)
        shoulder_y = torso_y + 6
        return pygame.Vector2(32, shoulder_y)
    def _head_center(self):
        y = 16 + HEAD_H//2 + int(-math.sin(math.radians(self.spine_deg))*HEAD_BOB)
        return pygame.Vector2(32 + int(self.lean_vec.x*1.0), y)
    def _update_arms(self, time_s, right_hand_target=None):
        if right_hand_target is None:
            dir = self._aim_dir_from_lean()
            dir_local = pygame.Vector2(dir.x*self.facing, dir.y)
            base_len = UP_ARM + LO_ARM - 4
            target_len_r = base_len + (BOW_PULL if self.weapon=="bow" else 0) + math.sin(time_s*6.0)*ARM_SWAY*4
            add = 0.0
            if self.weapon=="sword" and self.attack_phase>0:
                add = math.radians(SWORD_SWING_DEG)*math.sin(self.attack_phase*math.pi)
            tx = dir_local.x*target_len_r*math.cos(add) - dir_local.y*target_len_r*math.sin(add)
            ty = dir_local.x*target_len_r*math.sin(add) + dir_local.y*target_len_r*math.cos(add) + ARM_GRAVITY
        else:
            tx, ty = right_hand_target
        shoulders = self._shoulders_pos()
        r_shoulder = pygame.Vector2(shoulders.x + 8, shoulders.y)
        l_shoulder = pygame.Vector2(shoulders.x - 8, shoulders.y)
        self.r_arm.update(r_shoulder, pygame.Vector2(tx,ty), damp=ARM_DAMP)
        sway = math.sin(time_s*5.5 + self.walk_t*2.0)*8
        lx = -8 + sway*0.2
        ly = 6 + ARM_GRAVITY + abs(math.sin(self.walk_t*math.pi))*6
        if self.weapon=="sword" and getattr(self, "shield_active", False):
            tx, ty = (0, ARM_GRAVITY + 24)
            self.r_arm.update(r_shoulder, pygame.Vector2(tx, ty), damp=ARM_DAMP)
            lx = 18
            ly = ARM_GRAVITY + 6
            self.l_arm.update(l_shoulder, pygame.Vector2(lx, ly), damp=ARM_DAMP*0.8)
            return
        self.l_arm.update(l_shoulder, pygame.Vector2(lx,ly), damp=ARM_DAMP*0.8)
    def _hand_world(self):
        hand = self.r_arm.hand.copy()
        if self.facing<0: hand.x = self.image.get_width()-hand.x
        return pygame.Vector2(self.rect.left + hand.x, self.rect.top + hand.y)
    def _draw_leg(self, surf, hip, swing, knee_bend, color=(210,180,120)):
        a1 = swing - 0.2*math.sin(self.walk_t*math.pi*2)
        knee = pygame.Vector2(hip.x + UP_LEG*math.sin(a1),
                              hip.y + UP_LEG*math.cos(a1))
        a2 = a1 + knee_bend
        foot = pygame.Vector2(knee.x + LO_LEG*math.sin(a2),
                              knee.y + LO_LEG*math.cos(a2))
        def quad(a,b,th):
            d=b-a
            if d.length_squared()==0: n=pygame.Vector2(0,0)
            else: n=pygame.Vector2(-d.y,d.x).normalize()*(th/2)
            return [a+n,a-n,b-n,b+n]
        pygame.draw.polygon(surf, color, quad(hip, knee, LEG_THICK))
        pygame.draw.polygon(surf, color, quad(knee, foot, LEG_THICK))
        pygame.draw.rect(surf, (80,70,60), (foot.x-6, foot.y-2, 12, 6))
    def _build_image(self, time_s, tint=None):
        surf = pygame.Surface((64,96), pygame.SRCALPHA)
        pelvis = pygame.Surface((24, PELVIS_H), pygame.SRCALPHA); pelvis.fill((110,110,150) if tint is None else tint)
        torso  = pygame.Surface((28, TORSO_H),  pygame.SRCALPHA); torso.fill((130,130,180) if tint is None else tint)
        pelvis_pos = self._pelvis_pos()
        torso_y = pelvis_pos.y - TORSO_H
        surf.blit(torso, (32-14 + int(self.lean_vec.x*0.8), torso_y))
        surf.blit(pelvis,(32-12 + int(self.lean_vec.x*0.6), pelvis_pos.y))
        hip_r = pygame.Vector2(32+6, pelvis_pos.y+PELVIS_H-2)
        hip_l = pygame.Vector2(32-6, pelvis_pos.y+PELVIS_H-2)
        if not self.mounted:
            a = math.sin(self.walk_t*math.pi*2)*0.5
            knee_bend = 0.3 + 0.2*abs(math.sin(self.walk_t*math.pi*2))
            self._draw_leg(surf, hip_r, a,   knee_bend, color=(210,180,120))
            self._draw_leg(surf, hip_l, -a,  knee_bend, color=(195,170,115))
        else:
            pygame.draw.rect(surf,(210,180,120),(hip_r.x-2, hip_r.y+2, 4, 8))
            pygame.draw.rect(surf,(195,170,115),(hip_l.x-2, hip_l.y+2, 4, 8))
        shoulders = self._shoulders_pos()
        self.r_arm.draw(surf, pygame.Vector2(shoulders.x+8, shoulders.y))
        self.l_arm.draw(surf, pygame.Vector2(shoulders.x-8, shoulders.y))

        # Shield visual when active (sword only)
        if getattr(self, "shield_active", False) and self.weapon == "sword":
            lh = self.l_arm.hand
            shield_r = HEAD_H//2
            pygame.draw.circle(surf, (150, 100, 60), (int(lh.x), int(lh.y)), shield_r)
            pygame.draw.circle(surf, (200, 160, 120), (int(lh.x)-shield_r//3, int(lh.y)-shield_r//3), max(1, shield_r-9), 1)

        # --- draw weapon in hand (visual only) ---
        hand = self.r_arm.hand

        # Pixel-art helpers
        def _px_rect(surf, color, x, y, w, h):
            import pygame
            pygame.draw.rect(surf, color, (int(x), int(y), int(w), int(h)))

        def _draw_weapon_local(kind):
            import pygame, math
            hx, hy = int(hand.x), int(hand.y)
            if kind == "sword":
                # Vertical gray sword the size of the hand (visual only)
                blade_color = (180, 180, 185)   # саарал
                highlight   = (220, 220, 225)
                # approximate "hand-sized" blade: ~16px height, centered at hand
                length = 16
                thickness = 4
                top_y = hy - length//2
                # main blade
                pygame.draw.line(surf, blade_color, (hx, top_y), (hx, top_y + length), thickness)
                # subtle highlight along the left edge
                pygame.draw.line(surf, highlight, (hx-1, top_y+1), (hx-1, top_y + length - 1), 1)
            else:
                # Pixel bow: more rounded inward curve made of 2x2 "pixels"
                brown     = (150, 100, 60)
                accent    = (200, 160, 120)
                half_h    = 30           # total bow height ≈ 60px
                step_y    = 2
                max_off   = 10           # stronger curvature
                for yy in range(-half_h, half_h+1, step_y):
                    t = abs(yy) / half_h
                    off = int(max_off * (t**0.65))
                    _px_rect(surf, brown, hx - off, hy + yy, 2, 2)
                for yy in range(-half_h+4, half_h-3, step_y*2):
                    t = abs(yy) / half_h
                    off = int(max_off * (t**0.65))
                    _px_rect(surf, accent, hx - off + 2, hy + yy, 1, 1)

        _draw_weapon_local(self.weapon)
        neck = pygame.Surface((10, NECK_H), pygame.SRCALPHA); neck.fill((210,180,160))
        head = pygame.Surface((HEAD_H, HEAD_H), pygame.SRCALPHA); head.fill((225,180,180))
        head_c = self._head_center()
        surf.blit(neck, (32-5, head_c.y - HEAD_H//2 + HEAD_H + 2))
        eye_dx = 2*self.facing + int(self.lean_vec.x*0.4)
        eye_dy = -int(self.lean_vec.y*0.5)
        pygame.draw.rect(head,(10,10,10),(5+eye_dx, 6+eye_dy, 3,3))
        pygame.draw.rect(head,(10,10,10),(HEAD_H-8+eye_dx, 6+eye_dy, 3,3))
        head_rot = pygame.transform.rotate(head, -self.head_deg)
        hr = head_rot.get_rect(center=(head_c.x, head_c.y))
        surf.blit(head_rot, hr.topleft)
        if self.facing<0: surf = pygame.transform.flip(surf, True, False)
        self.image=surf

class Player(Humanoid):
    def __init__(self,x,y):
        super().__init__(x,y)
        self.health = 100
        self.shield_active = False
        # cooldown for touch-damage
        self.collide_cd = 0
    def _apply_mouse_lean(self, mouse_rel):
        dx,dy = mouse_rel
        if dx>0.5: self.facing=1
        elif dx<-0.5: self.facing=-1
        self.lean_vec.x += dx*LEAN_SENS
        self.lean_vec.y += -dy*LEAN_SENS
        self.lean_vec *= LEAN_DECAY
        self.spine_deg = clamp(self.lean_vec.y*30, -LEAN_CLAMP, LEAN_CLAMP)
        self.head_deg  = clamp(self.lean_vec.y*38, -LEAN_CLAMP*1.3, LEAN_CLAMP*1.3)
    def update(self, plats, bullets, enemies, mouse_rel, time_s, keys, mounts):
        self._apply_mouse_lean(mouse_rel)
        if self.mounted and self.mount:
            move = (keys[K_d] + keys[K_RIGHT]) - (keys[K_a] + keys[K_LEFT])
            self.mount.vel.x = move * HORSE_SPEED
            if (keys[K_w] or keys[K_UP] or keys[K_SPACE]) and self.mount.on_ground:
                self.mount.vel.y = -HORSE_JUMP
            self.vel.update(0,0)
            self.on_ground = self.mount.on_ground
        else:
            self.vel.x = (keys[K_d]-keys[K_a])*PLAYER_SPEED
            if keys[K_w] and self.on_ground:
                self.vel.y = -PLAYER_JUMP_POWER; self.on_ground=False
            self.vel.y = min(30, self.vel.y + GRAVITY)
            self.rect.x += int(self.vel.x); self._collide(self.vel.x,0,plats)
            self.rect.y += int(self.vel.y); self.on_ground=False; self._collide(0,self.vel.y,plats)
        if self.attack_cd>0:
            self.attack_cd-=1
            self.attack_phase = 1.0 - (self.attack_cd/20.0 if self.weapon=="sword" else self.attack_cd/10.0)
        else:
            self.attack_phase=0.0
        if self.shoot_cd>0: self.shoot_cd-=1

        # === Collision damage slow-down ===
        if self.collide_cd > 0:
            self.collide_cd -= 1
        for e in enemies:
            if self.rect.colliderect(e.rect) and self.collide_cd == 0:
                self.take_damage(ENEMY_COLLIDE_TICK_DAMAGE)
                self.collide_cd = FPS // 2  # only apply touch-damage twice per second

        speed = abs(self.mount.vel.x) if self.mounted and self.mount else abs(self.vel.x)
        if speed>0.1 and (self.on_ground or (self.mounted and self.mount.on_ground)):
            self.walk_t += (speed/(HORSE_SPEED if (self.mounted and self.mount) else PLAYER_SPEED))*WALK_FREQ*(1/FPS)
        else:
            self.walk_t *= 0.96
        self._update_arms(time_s)
        self._build_image(time_s)
    def sync_to_mount(self):
        if self.mounted and self.mount:
            seat = self.mount.seat_world()
            self.rect.midbottom = (int(seat.x), int(seat.y + 24))
    def attack(self, bullets, enemies):
        if self.attack_cd>0: return
        if self.weapon=="sword":
            for e in enemies:
                if abs(e.rect.centerx - self.rect.centerx) < ATTACK_RANGE and abs(e.rect.centery - self.rect.centery) < 56:
                    e.take_damage(40)
            self.attack_cd=20
        elif self.weapon=="bow" and self.shoot_cd<=0:
            dir = self._aim_dir_from_lean()
            pos = self._hand_world()
            bullets.add(Bullet(pos.x, pos.y, dir, is_enemy=False))
            self.shoot_cd=20; self.attack_cd=10
    def switch_weapon(self):
        self.weapon = "bow" if self.weapon=="sword" else "sword"
        if self.weapon != "sword":
            self.shield_active = False
    def take_damage(self,d):
        self.health=max(0,self.health-d)

class Bullet(pygame.sprite.Sprite):
    def __init__(self,x,y,dir,is_enemy=False):
        super().__init__()
        self.image=pygame.Surface((10,4)); self.image.fill((230,220,120) if not is_enemy else (240,120,120))
        self.rect=self.image.get_rect(center=(x,y))
        self.vel = dir*BULLET_SPEED
        self.life=90
        self.is_enemy = is_enemy
    def update(self, plats, enemies, player):
        self.rect.x += int(self.vel.x); self.rect.y += int(self.vel.y); self.life-=1
        if self.life<=0: self.kill()
        if self.is_enemy:
            if self.rect.colliderect(player.rect):
                if getattr(player, 'shield_active', False):
                    self.kill()
                else:
                    player.take_damage(2); self.kill()   # was 30 → 15
        else:
            hit = pygame.sprite.spritecollideany(self, enemies)
            if hit:
                hit.take_damage(28); self.kill()         # was 30 → 15
        for t in plats:
            if self.rect.colliderect(t.rect):
                self.kill()
                break

class Enemy(Humanoid):
    def __init__(self,x,y):
        super().__init__(x,y)
        self.health = 80
        self.weapon="bow"
        self.shoot_cd = random.randint(0, ENEMY_SHOOT_CD)
        self.attack_cd = 0
    def _aim_towards_player(self, player):
        dir_vec = pygame.Vector2(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
        if dir_vec.length() == 0: dir_vec.update(1,0)
        self.facing = 1 if dir_vec.x >= 0 else -1
        target_y = -dir_vec.normalize().y
        self.spine_deg = clamp(target_y*30, -LEAN_CLAMP, LEAN_CLAMP)
        self.head_deg  = clamp(target_y*38, -LEAN_CLAMP*1.3, LEAN_CLAMP*1.3)
    def update(self, plats, bullets, player, time_s):
        dx = player.rect.centerx - self.rect.centerx
        self.vel.x = ENEMY_SPEED * (1 if dx>10 else -1 if dx<-10 else 0)
        self.vel.y = min(30, self.vel.y + GRAVITY)
        self.rect.x += int(self.vel.x); self._collide(self.vel.x,0,plats)
        self.rect.y += int(self.vel.y); self.on_ground=False; self._collide(0,self.vel.y,plats)
        speed = abs(self.vel.x)
        if speed>0.1 and self.on_ground:
            self.walk_t += (speed/ENEMY_SPEED)*WALK_FREQ*(1/FPS)
        else:
            self.walk_t *= 0.96
        dist = pygame.Vector2(player.rect.center).distance_to(self.rect.center)
        if dist > RANGED_DIST: self.weapon = "bow"
        elif dist < MELEE_DIST: self.weapon = "sword"
        if self.weapon=="bow":
            if self.shoot_cd>0: self.shoot_cd-=1
            if self.shoot_cd<=0:
                self._aim_towards_player(player)
                dir_vec = pygame.Vector2(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
                if dir_vec.length() == 0: dir_vec.update(1,0)
                dir = dir_vec.normalize()
                pos = self._hand_world()
                bullets.add(Bullet(pos.x, pos.y, dir, is_enemy=True))
                self.shoot_cd = ENEMY_SHOOT_CD
                self.attack_phase = 0.5
        else:
            if self.attack_cd>0:
                self.attack_cd -= 1
                self.attack_phase = 1.0 - (self.attack_cd/20.0)
            else:
                if abs(player.rect.centerx - self.rect.centerx) < ATTACK_RANGE and abs(player.rect.centery - self.rect.centery) < 56:
                    player.take_damage(40) if not getattr(player, 'shield_active', False) else None
                    self.attack_cd = ENEMY_SWING_CD
                    self.attack_phase = 0.5
        self._aim_towards_player(player)
        self._update_arms(time_s)
        self._build_image(time_s, tint=(110, 150, 110))

    def take_damage(self, d):
        self.health = max(0, self.health - d)
        if self.health <= 0:
            self.kill()

# ----- level -----
LEVEL_W, LEVEL_H = 30000, 1200
plats = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
mounts = pygame.sprite.Group()

ground = Platform(0, LEVEL_H-80, LEVEL_W, 80); plats.add(ground); all_sprites.add(ground)
player = Player(120, LEVEL_H-320); all_sprites.add(player)

HORSE_START_X, HORSE_START_Y = 420, LEVEL_H-320
horse = Horse(HORSE_START_X, HORSE_START_Y)
mounts.add(horse); all_sprites.add(horse)

enemy_positions = [
    (600, LEVEL_H-256),(760, LEVEL_H-256),(920, LEVEL_H-256),
    (1150, LEVEL_H-256),(1350, LEVEL_H-256),
    (1600, LEVEL_H-256),(1800, LEVEL_H-256),
    (2050, LEVEL_H-256),(2300, LEVEL_H-256),(2500, LEVEL_H-256)
]
for pos in enemy_positions:
    e=Enemy(pos[0],pos[1]); enemies.add(e); all_sprites.add(e)

cam = Camera(LEVEL_W, LEVEL_H)

def nearest_mount_and_dist(player, mounts):
    best=None; best_d=1e9
    for h in mounts:
        seat = h.seat_world()
        d = pygame.Vector2(player.rect.center).distance_to(seat)
        if d<best_d: best_d=d; best=h
    return best, best_d

def can_mount(player, horse):
    seat = horse.seat_world()
    dist = pygame.Vector2(player.rect.center).distance_to(seat)
    near_rect = horse.rect.inflate(80,40).colliderect(player.rect)
    return dist <= MOUNT_RANGE or near_rect, dist

def draw_hud(surf, pl):
    bar_w=220; x,y=12,12
    pygame.draw.rect(surf,(60,60,70),(x-2,y-2,bar_w+4,24))
    pygame.draw.rect(surf,(120,30,30),(x,y,int(bar_w*(pl.health/100)),20))
    surf.blit(font.render(f"Health: {pl.health}",True,WHITE),(x+6,y+24))
    surf.blit(font.render(f"Weapon: {pl.weapon.title()}",True,WHITE),(x+6,y+48))

    # Mount hint (only when near a horse)
    mount_hint = ""
    near_any = False
    for h in mounts:
        ok, dist = can_mount(pl, h)
        if ok:
            mount_hint = f"Press E to mount horse (dist: {int(dist)})"
            near_any = True
            break
    if pl.mounted:
        mount_hint = "Mounted: Horse (E to dismount)"
        near_any = True
    if near_any:
        surf.blit(font.render(mount_hint,True,WHITE),(x+6,y+72))

running=True
last_switch=-1000; SWITCH_MS=120
last_mount_toggle=-1000
pygame.mouse.get_rel()

game_over = False

game_won = False

def draw_game_over_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    title_text = "game over, press enter button to start again"
    big = pygame.font.SysFont("", 36)
    small = pygame.font.SysFont("", 22)
    tsurf = big.render(title_text, True, (255,255,255))
    hint = small.render("Press ESC to quit", True, (200,200,200))
    overlay.blit(tsurf, (WIDTH//2 - tsurf.get_width()//2, HEIGHT//2 - tsurf.get_height()))
    overlay.blit(hint,  (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 24))
    screen.blit(overlay, (0,0))


def draw_win_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    big = pygame.font.SysFont("", 44)
    small = pygame.font.SysFont("", 22)
    tsurf = big.render("YOU WIN", True, (255, 255, 0))
    hint = small.render("Press ENTER to restart", True, (220,220,220))
    overlay.blit(tsurf, (WIDTH//2 - tsurf.get_width()//2, HEIGHT//2 - tsurf.get_height()))
    overlay.blit(hint,  (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 24))
    screen.blit(overlay, (0,0))

while running:
    dt=clock.tick(FPS); now=pygame.time.get_ticks(); t=now/1000.0
    mouse_rel=(0,0)
    keys = pygame.key.get_pressed()
    for ev in pygame.event.get():
        if ev.type==QUIT or (ev.type==KEYDOWN and ev.key==K_ESCAPE): running=False
        if not game_over and not game_won:
            if ev.type==MOUSEBUTTONDOWN and ev.button==1:
                player.shield_active = False
                player.attack(bullets,enemies)
            if ev.type==MOUSEBUTTONDOWN and ev.button in (2,3):
                if player.weapon == "sword":
                    player.shield_active = True
            if ev.type==MOUSEWHEEL:
                dy=getattr(ev,"precise_y",ev.y)
                if abs(dy)>0.02 and now-last_switch>SWITCH_MS: player.switch_weapon(); last_switch=now
            if ev.type==MOUSEMOTION: mouse_rel = ev.rel
            if ev.type==KEYDOWN and ev.key==K_e:
                if now - last_mount_toggle > MOUNT_COOLDOWN_MS:
                    if player.mounted:
                        player.mounted=False
                        if player.mount:
                            player.mount.rider=None
                            player.rect.midbottom = (player.mount.rect.centerx + (20 if player.facing>0 else -20),
                                                     player.mount.rect.bottom)
                            player.mount=None
                    else:
                        best, dist = nearest_mount_and_dist(player, mounts)
                        if best:
                            ok, _ = can_mount(player, best)
                            if ok:
                                player.mounted=True; player.mount=best; best.rider=player
                                seat = best.seat_world()
                                player.rect.midbottom = (int(seat.x), int(seat.y + 24))
                    last_mount_toggle = now
        else:
            if ev.type==KEYDOWN and ev.key==K_RETURN:
                game_over = False

                player.health = 100
                if player.mounted and player.mount:
                    player.mount.rider=None
                player.mounted=False; player.mount=None
                player.rect.topleft = (120, LEVEL_H-320)
                player.vel.update(0,0)
                # Reset horse
                for h in mounts:
                    h.rider = None
                    h.rect.topleft = (HORSE_START_X, HORSE_START_Y)
                    h.vel.update(0,0)
                    h.on_ground = False
                bullets.empty()
                for e in enemies: e.kill()
                for pos in enemy_positions:
                    e=Enemy(pos[0],pos[1]); enemies.add(e); all_sprites.add(e)
                pygame.mouse.get_rel()

    if mouse_rel==(0,0): mouse_rel = pygame.mouse.get_rel()

    if not game_over and not game_won:
        player.update(plats, bullets, enemies, mouse_rel, t, keys, mounts)
        for h in mounts: h.update(plats)
        player.sync_to_mount()
        bullets.update(plats, enemies, player)
        for e in enemies: e.update(plats, bullets, player, t)
        if player.health <= 0:
            game_over = True
        # Win check
        if not game_over and len(enemies) == 0:
            game_won = True

    follow_rect = player.mount.rect if (player.mounted and player.mount) else player.rect
    cam.update(follow_rect)

    # Draw animated background
    bg_offset_x = cam.offset.x

    time_angle = t * 0.35
    t_frac = (math.sin(time_angle) + 1) / 2
    sky_color = get_sky_color(t_frac)
    sun_y = HEIGHT*0.5 - math.sin(time_angle) * (HEIGHT*0.39)
    moon_y = HEIGHT*0.5 + math.sin(time_angle) * (HEIGHT*0.39)
    move_clouds_bg(screen)
    draw_scene_bg(screen, sky_color, sun_y, moon_y, t_frac)
    for s in all_sprites: screen.blit(s.image, cam.apply(s.rect))
    for b in bullets: screen.blit(b.image, cam.apply(b.rect))
    draw_hud(screen, player)
    if game_over: draw_game_over_overlay()
    if game_won: draw_win_overlay()
    pygame.display.flip()

pygame.quit()

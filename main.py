import pygame as pg
import random
import time
import asyncio

pg.init()
clock = pg.time.Clock()

# Window settings
WIN_WIDTH = 800
WIN_HEIGHT = 600
screen = pg.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pg.display.set_caption('Game')

font = pg.font.Font(None, 30)
font_small = pg.font.Font(None, 22)

# Player variablesff
player_size = 40
player_pos = [WIN_WIDTH / 2, WIN_HEIGHT - player_size]
player_image = pg.image.load('./assets/images/e1.png')
player_image = pg.transform.scale(player_image, (player_size, player_size))

player_speed = 7  # smaller for smooth movement
speeding = False
speed_cooldown_timer = 0

# Object variables
obj_size = 38
obj_data = []

# Load object image (Mario)
obj_image = pg.image.load('./assets/images/mario.png')

# Background
bg_image = pg.image.load('./assets/images/background.png')
bg_image = pg.transform.scale(bg_image, (WIN_WIDTH + 40, WIN_HEIGHT + 40))

# Boost cooldowns and durations (in frames at 30 FPS)
COOLDOWN_SPEED = 300         # 10 seconds
COOLDOWN_BOOM = 5400         # 3 minutes
COOLDOWN_SLOWMO = 3600       # 2 minutes
COOLDOWN_SHIELD = 3600       # 2 minutes
COOLDOWN_TELEPORT = 900      # 30 seconds
COOLDOWN_FREEZE = 3600       # 2 minutes
COOLDOWN_BULLET = 900        # 30 seconds

FREEZE_DURATION = 90         # 3 seconds freeze
SLOWMO_DURATION = 300        # 10 seconds slow motion
BOOM_DURATION = 30           # 1 second boom effect
SHIELD_DURATION = 150        # 5 seconds shield active (updated)
SPEED_DURATION = 150         # 5 seconds speed boost

# Timers
boom_cooldown_timer = 0
slowmo_cooldown_timer = 0
shield_cooldown_timer = 0
teleport_cooldown_timer = 0
freeze_cooldown_timer = 0
bullet_cooldown_timer = 0

# States
running = True
jumping = False
jump_velocity = 0
jump_max = 15

score = 0
slowmo_active = False
slowmo_timer = 0
boom_active = False
boom_timer = 0
shield_active = False
shield_timer = 0
freeze_active = False
freeze_timer = 0

bullets = []  # List of bullets: each bullet = [x, y, speed]
bullet_speed = 20

# Teleport fall variables
teleport_falling = False
teleport_fall_speed = 0
teleport_fall_pos = [0, 0]

# Functions
def create_object(obj_data):
    if len(obj_data) < 10 and random.random() < 0.1:
        x = random.randint(0, WIN_WIDTH - obj_size)
        y = 0
        size = random.randint(1, 69)
        image_scaled = pg.transform.scale(obj_image, (size, size))
        obj_data.append([x, y, image_scaled, size])

def update_objects(obj_data, speed):
    global score
    for obj in obj_data[:]:
        obj[1] += speed
        if obj[1] > WIN_HEIGHT:
            obj_data.remove(obj)
            score += 1
        else:
            screen.blit(obj[2], (obj[0], obj[1]))

def collision_check(obj_data, player_pos):
    global running, shield_active
    player_rect = pg.Rect(player_pos[0], player_pos[1], player_size, player_size)
    for obj in obj_data:
        obj_rect = pg.Rect(obj[0], obj[1], obj[3], obj[3])
        if player_rect.colliderect(obj_rect):
            if shield_active:
                obj_data.remove(obj)
            else:
                time.sleep(2)
                running = False
                break

def draw_cooldown_bar(x, y, width, height, cooldown_timer, max_cooldown, color, label):
    ratio = min(cooldown_timer / max_cooldown, 1)
    filled_width = int(width * (1 - ratio))
    pg.draw.rect(screen, (180, 180, 180), (x, y, width, height))  # BG bar
    pg.draw.rect(screen, color, (x, y, filled_width, height))
    text = font.render(label, True, (0, 0, 0))
    screen.blit(text, (x + width + 10, y))

def fire_bullets(player_pos):
    bullets_to_fire = []
    base_x = player_pos[0] + player_size // 2 - 15
    base_y = player_pos[1]
    for i in range(3):
        bullet_x = base_x + i * 15
        bullets_to_fire.append([bullet_x, base_y, bullet_speed])
    return bullets_to_fire

def update_bullets(bullets, obj_data):
    for bullet in bullets[:]:
        bullet[1] -= bullet[2]
        if bullet[1] < 0:
            bullets.remove(bullet)
            continue
        bullet_rect = pg.Rect(bullet[0], bullet[1], 5, 10)
        for obj in obj_data[:]:
            obj_rect = pg.Rect(obj[0], obj[1], obj[3], obj[3])
            if bullet_rect.colliderect(obj_rect):
                obj_data.remove(obj)
                if bullet in bullets:
                    bullets.remove(bullet)
                break
        else:
            pg.draw.rect(screen, (255, 255, 0), bullet_rect)

def teleport_player():
    # Teleport to random X, and high Y above screen to fall down smoothly
    new_x = random.randint(0, WIN_WIDTH - player_size)
    new_y = -player_size * 3  # Start above the screen for falling effect
    return [new_x, new_y]

# Controls info list
controls_info = [
    "Controls:",
    "Arrow Keys: Move",
    "UP: Jump",
    "SPACE: Speed Boost",
    "B: Boom Boost",
    "S: Slow-mo Boost",
    "L: Shield Boost",
    "T: Teleport",
    "Q: Freeze Enemies",
    "F: Fire Bullets (when frozen)",
]

# Main loop
async def main():

    global running, player_pos, obj_speed
    global teleport_pos, teleport_fall_pos, teleport_fall_speed, teleport_falling, teleport_cooldown_timer
    global jumping, jump_velocity
    global speeding, speed_cooldown_timer
    global boom_active, boom_cooldown_timer, boom_timer
    global slowmo_active, slowmo_cooldown_timer, slowmo_timer
    global shield_active, shield_cooldown_timer, shield_timer
    global freeze_active, freeze_cooldown_timer, freeze_timer
    global new_bullets, bullets, bullet_cooldown_timer

    while running:
        obj_speed = 2 if slowmo_active else 7

        keys = pg.key.get_pressed()

        x, y = player_pos

        # Smooth horizontal movement
        if keys[pg.K_LEFT]:
            x -= player_speed
        if keys[pg.K_RIGHT]:
            x += player_speed

        # Clamp horizontal position
        x = max(0, min(WIN_WIDTH - player_size, x))

        # Handle teleport fall if active
        if teleport_falling:
            teleport_fall_speed += 1  # gravity acceleration
            teleport_fall_pos[1] += teleport_fall_speed
            if teleport_fall_pos[1] >= WIN_HEIGHT - player_size:
                teleport_fall_pos[1] = WIN_HEIGHT - player_size
                teleport_falling = False
                player_pos = [teleport_fall_pos[0], teleport_fall_pos[1]]
            else:
                player_pos = [teleport_fall_pos[0], teleport_fall_pos[1]]
        else:
            # Jumping initiated on keydown event below (so we keep that logic)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP:
                        if not jumping and not teleport_falling:
                            jumping = True
                            jump_velocity = jump_max
                    elif event.key == pg.K_SPACE:
                        if speed_cooldown_timer <= 0:
                            speeding = True
                            speed_cooldown_timer = COOLDOWN_SPEED
                    elif event.key == pg.K_b:
                        if boom_cooldown_timer <= 0:
                            boom_active = True
                            boom_timer = BOOM_DURATION
                            boom_cooldown_timer = COOLDOWN_BOOM
                    elif event.key == pg.K_s:
                        if slowmo_cooldown_timer <= 0:
                            slowmo_active = True
                            slowmo_timer = SLOWMO_DURATION
                            slowmo_cooldown_timer = COOLDOWN_SLOWMO
                    elif event.key == pg.K_l:
                        if shield_cooldown_timer <= 0:
                            shield_active = True
                            shield_timer = SHIELD_DURATION
                            shield_cooldown_timer = COOLDOWN_SHIELD
                    elif event.key == pg.K_t:
                        if teleport_cooldown_timer <= 0:
                            # Begin teleport fall
                            teleport_pos = teleport_player()
                            teleport_fall_pos = teleport_pos.copy()
                            teleport_fall_speed = 0
                            teleport_falling = True
                            teleport_cooldown_timer = COOLDOWN_TELEPORT
                    elif event.key == pg.K_q:
                        if freeze_cooldown_timer <= 0:
                            freeze_active = True
                            freeze_timer = FREEZE_DURATION
                            freeze_cooldown_timer = COOLDOWN_FREEZE
                    elif event.key == pg.K_f:
                        if bullet_cooldown_timer <= 0 and freeze_active:
                            new_bullets = fire_bullets(player_pos)
                            bullets.extend(new_bullets)
                            bullet_cooldown_timer = COOLDOWN_BULLET

            # If not teleporting, update vertical movement with jumping
            if jumping:
                player_pos[1] -= jump_velocity
                jump_velocity -= 1
                if player_pos[1] >= WIN_HEIGHT - player_size:
                    player_pos[1] = WIN_HEIGHT - player_size
                    jumping = False

            # Update player x,y if not teleport falling
            player_pos[0] = x

        # Speed boost effect
        if speeding:
            player_speed = 14  # Increased speed but not crazy
        else:
            player_speed = 7

        # Boom boost effect: clear all enemies when active
        if boom_active:
            obj_data.clear()

        # Update timers
        if speed_cooldown_timer > 0:
            speed_cooldown_timer -= 1
            if speed_cooldown_timer <= COOLDOWN_SPEED - SPEED_DURATION:
                speeding = False

        if boom_cooldown_timer > 0:
            boom_cooldown_timer -= 1
        if boom_active:
            boom_timer -= 1
            if boom_timer <= 0:
                boom_active = False

        if slowmo_cooldown_timer > 0:
            slowmo_cooldown_timer -= 1
        if slowmo_active:
            slowmo_timer -= 1
            if slowmo_timer <= 0:
                slowmo_active = False

        if shield_cooldown_timer > 0:
            shield_cooldown_timer -= 1
        if shield_active:
            shield_timer -= 1
            if shield_timer <= 0:
                shield_active = False

        if teleport_cooldown_timer > 0:
            teleport_cooldown_timer -= 1

        if freeze_cooldown_timer > 0:
            freeze_cooldown_timer -= 1
        if freeze_active:
            freeze_timer -= 1
            if freeze_timer <= 0:
                freeze_active = False

        if bullet_cooldown_timer > 0:
            bullet_cooldown_timer -= 1

        # Fill background
        screen.blit(bg_image, (-10, -30))

        # Draw score
        score_text = font.render(f"Score: {score}", True, (0, 0, 0))
        screen.blit(score_text, (WIN_WIDTH - 150, WIN_HEIGHT - 40))

        # Create and update objects
        if not freeze_active:
            create_object(obj_data)
        update_objects(obj_data, 2 if slowmo_active else 7 if not freeze_active else 0)

        # Collision
        if not boom_active and not freeze_active:
            collision_check(obj_data, player_pos)

        # Draw player with shield effect
        screen.blit(player_image, (player_pos[0], player_pos[1]))
        if shield_active:
            # Draw shield circle
            pg.draw.circle(screen, (0, 255, 255), (int(player_pos[0] + player_size / 2), int(player_pos[1] + player_size / 2)), player_size, 4)

        # Update bullets
        update_bullets(bullets, obj_data)

        # Draw cooldown bars
        bar_x = 20
        bar_y = 20
        bar_w = 150
        bar_h = 20

        draw_cooldown_bar(bar_x, bar_y, bar_w, bar_h, speed_cooldown_timer, COOLDOWN_SPEED, (0, 255, 0), "Speed")
        draw_cooldown_bar(bar_x, bar_y + 30, bar_w, bar_h, boom_cooldown_timer, COOLDOWN_BOOM, (255, 0, 0), "Boom")
        draw_cooldown_bar(bar_x, bar_y + 60, bar_w, bar_h, slowmo_cooldown_timer, COOLDOWN_SLOWMO, (0, 0, 255), "Slow-mo")
        draw_cooldown_bar(bar_x, bar_y + 90, bar_w, bar_h, shield_cooldown_timer, COOLDOWN_SHIELD, (0, 255, 255), "Shield")
        draw_cooldown_bar(bar_x, bar_y + 120, bar_w, bar_h, teleport_cooldown_timer, COOLDOWN_TELEPORT, (255, 255, 0), "Teleport")
        draw_cooldown_bar(bar_x, bar_y + 150, bar_w, bar_h, freeze_cooldown_timer, COOLDOWN_FREEZE, (255, 0, 255), "Freeze")
        draw_cooldown_bar(bar_x, bar_y + 180, bar_w, bar_h, bullet_cooldown_timer, COOLDOWN_BULLET, (255, 165, 0), "Bullets")

        # Draw controls panel on right side
        controls_x = WIN_WIDTH - 220
        controls_y = 20
        pg.draw.rect(screen, (220, 220, 220), (controls_x - 10, controls_y - 10, 210, 210))
        for i, line in enumerate(controls_info):
            txt = font_small.render(line, True, (0, 0, 0))
            screen.blit(txt, (controls_x, controls_y + i * 22))

        clock.tick(30)
        pg.display.flip()
        await asyncio.sleep(0)

    pg.quit()


asyncio.run(main())
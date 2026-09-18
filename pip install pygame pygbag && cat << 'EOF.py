import pygame
import pygame
import sys
import random
import asyncio

# Initialize Pygame
pygame.init()
pygame.font.init()

# Game Window
WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fishing Simulator 2D")
clock = pygame.time.Clock()
FPS = 60

# Colors
SKY_BLUE = (135, 206, 235)
WATER_BLUE = (30, 120, 200)
SHORE_BROWN = (139, 69, 19)
GREEN = (40, 180, 40)
RED = (220, 40, 40)
YELLOW = (255, 215, 0)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK_GRAY = (40, 40, 40)
BROWN = (100, 50, 10)

# Fonts
font_title = pygame.font.SysFont("Arial", 36, bold=True)
font_med = pygame.font.SysFont("Arial", 22, bold=True)
font_small = pygame.font.SysFont("Arial", 16)

# Data
FISH_SPECIES = [
    {"name": "Bluegill", "min_w": 0.3, "max_w": 1.2, "val_per_kg": 25, "stamina": 30, "pull": 20, "min_lvl": 1},
    {"name": "Crappie", "min_w": 0.6, "max_w": 2.0, "val_per_kg": 35, "stamina": 45, "pull": 30, "min_lvl": 1},
    {"name": "Largemouth Bass", "min_w": 1.5, "max_w": 6.0, "val_per_kg": 50, "stamina": 80, "pull": 55, "min_lvl": 1},
    {"name": "Channel Catfish", "min_w": 3.0, "max_w": 12.0, "val_per_kg": 65, "stamina": 120, "pull": 80, "min_lvl": 2},
    {"name": "Northern Pike", "min_w": 4.5, "max_w": 15.0, "val_per_kg": 85, "stamina": 170, "pull": 110, "min_lvl": 3},
    {"name": "Trophy Rainbow Trout", "min_w": 6.0, "max_w": 18.0, "val_per_kg": 120, "stamina": 230, "pull": 150, "min_lvl": 4},
]

RODS = [
    {"name": "Basic TeleRod 200", "price": 0, "power": 30, "unlocked": True},
    {"name": "ValueCast 240", "price": 150, "power": 65, "unlocked": False},
    {"name": "OmniStrike 300", "price": 450, "power": 120, "unlocked": False},
]

REELS = [
    {"name": "ElementSpin 1000", "price": 0, "drag_max": 30, "unlocked": True},
    {"name": "CalistoMG 2500", "price": 120, "drag_max": 70, "unlocked": False},
    {"name": "ThunderSpool 4000", "price": 400, "drag_max": 140, "unlocked": False},
]

player = {
    "cash": 100,
    "xp": 0,
    "level": 1,
    "rod": RODS[0],
    "reel": REELS[0],
    "drag": 5,
    "keepnet": []
}

state = "HUB"
cast_power = 0
cast_direction = 1
cast_distance = 0
bite_timer = 0
active_fish = None
fish_distance = 0
fish_stamina = 0
max_fish_stamina = 0
line_tension = 0
fish_surge_timer = 0
fish_pulling = False
result_message = ""
result_color = WHITE

def get_required_xp(level):
    return level * 150

def check_level_up():
    req = get_required_xp(player["level"])
    if player["xp"] >= req:
        player["xp"] -= req
        player["level"] += 1

def start_cast():
    global state, cast_power, cast_direction
    state = "CASTING"
    cast_power = 0
    cast_direction = 1

def perform_cast():
    global state, cast_distance, bite_timer
    state = "WAITING"
    cast_distance = (cast_power / 100) * 40 + 10
    bite_timer = random.randint(120, 300)

def hook_fish():
    global state, active_fish, fish_distance, fish_stamina, max_fish_stamina, line_tension
    state = "FIGHTING"
    available = [f for f in FISH_SPECIES if f["min_lvl"] <= player["level"]]
    species = random.choice(available)
    weight = round(random.uniform(species["min_w"], species["max_w"]), 2)
    active_fish = {
        "name": species["name"],
        "weight": weight,
        "value": int(weight * species["val_per_kg"]),
        "xp": int(weight * species["val_per_kg"] * 1.2),
        "pull": species["pull"],
        "stamina": species["stamina"] * weight
    }
    fish_distance = cast_distance
    fish_stamina = active_fish["stamina"]
    max_fish_stamina = fish_stamina
    line_tension = 20.0

def update_fight():
    global state, line_tension, fish_distance, fish_stamina, fish_surge_timer, fish_pulling, result_message, result_color
    
    keys = pygame.key.get_pressed()
    reeling = keys[pygame.K_SPACE]
    
    fish_surge_timer -= 1
    if fish_surge_timer <= 0:
        fish_pulling = not fish_pulling
        fish_surge_timer = random.randint(40, 100)
    
    max_drag = player["reel"]["drag_max"]
    current_drag = (player["drag"] / 10.0) * max_drag
    fish_pull_force = active_fish["pull"] * (fish_stamina / max_fish_stamina + 0.3) if fish_pulling else 5
    rod_power = player["rod"]["power"]
    
    if reeling:
        tension_increase = (current_drag * 0.4) + (fish_pull_force * 0.5) - (rod_power * 0.2)
        line_tension += max(1.0, tension_increase * 0.15)
        if current_drag > fish_pull_force * 0.5:
            fish_distance -= 0.12 * (current_drag / 20.0)
    else:
        line_tension -= 1.2
        
    if fish_pulling:
        line_tension += (fish_pull_force * 0.1)
        fish_distance += 0.05 * (fish_pull_force / current_drag if current_drag > 0 else 2)
        fish_stamina -= 0.25 * (current_drag / 10.0)
    
    line_tension = max(0, line_tension)
    fish_stamina = max(0, fish_stamina)
    
    if line_tension >= 100:
        state = "RESULT"
        result_message = "LINE SNAPPED! The fish got away."
        result_color = RED
    elif line_tension <= 0 and reeling:
        state = "RESULT"
        result_message = "SLACK LINE! The hook slipped out."
        result_color = RED
    elif fish_distance <= 2.0:
        state = "RESULT"
        result_message = f"CAUGHT: {active_fish['name']} ({active_fish['weight']} kg)!"
        result_color = GREEN
        player["cash"] += active_fish["value"]
        player["xp"] += active_fish["xp"]
        check_level_up()
        player["keepnet"].append(active_fish)

def draw_hud():
    pygame.draw.rect(screen, DARK_GRAY, (0, 0, WIDTH, 50))
    cash_txt = font_med.render(f"Cash: ${player['cash']}", True, YELLOW)
    lvl_txt = font_med.render(f"Level: {player['level']} (XP: {player['xp']}/{get_required_xp(player['level'])})", True, WHITE)
    rod_txt = font_small.render(f"Rod: {player['rod']['name']}", True, WHITE)
    reel_txt = font_small.render(f"Reel: {player['reel']['name']}", True, WHITE)
    screen.blit(cash_txt, (20, 12))
    screen.blit(lvl_txt, (200, 12))
    screen.blit(rod_txt, (550, 8))
    screen.blit(reel_txt, (550, 26))

def draw_scene():
    pygame.draw.rect(screen, SKY_BLUE, (0, 50, WIDTH, 200))
    pygame.draw.rect(screen, WATER_BLUE, (0, 250, WIDTH, HEIGHT - 250))
    pygame.draw.polygon(screen, SHORE_BROWN, [(0, 220), (180, 250), (180, HEIGHT), (0, HEIGHT)])
    pygame.draw.polygon(screen, GREEN, [(0, 210), (190, 245), (150, 270), (0, 240)])
    pygame.draw.line(screen, BLACK, (90, 210), (90, 170), 5)
    pygame.draw.circle(screen, BLACK, (90, 162), 8)
    pygame.draw.line(screen, BROWN, (90, 185), (140, 150), 4)

def draw_tension_meter(x, y, width, height, value):
    pygame.draw.rect(screen, DARK_GRAY, (x, y, width, height))
    fill_h = int((value / 100.0) * height)
    fill_h = min(height, max(0, fill_h))
    color = GREEN
    if value > 60: color = YELLOW
    if value > 85: color = RED
    pygame.draw.rect(screen, color, (x, y + (height - fill_h), width, fill_h))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
    lbl = font_small.render("TENSION", True, WHITE)
    screen.blit(lbl, (x - 10, y - 22))

async def main():
    global state, cast_power, cast_direction, bite_timer, running
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if state == "HUB":
                    if event.key == pygame.K_SPACE:
                        start_cast()
                    elif event.key == pygame.K_1 and not RODS[1]["unlocked"] and player["cash"] >= RODS[1]["price"]:
                        player["cash"] -= RODS[1]["price"]
                        RODS[1]["unlocked"] = True
                        player["rod"] = RODS[1]
                    elif event.key == pygame.K_2 and not REELS[1]["unlocked"] and player["cash"] >= REELS[1]["price"]:
                        player["cash"] -= REELS[1]["price"]
                        REELS[1]["unlocked"] = True
                        player["reel"] = REELS[1]
                elif state == "CASTING":
                    if event.key == pygame.K_SPACE:
                        perform_cast()
                elif state == "FIGHTING":
                    if event.key == pygame.K_UP and player["drag"] < 10:
                        player["drag"] += 1
                    elif event.key == pygame.K_DOWN and player["drag"] > 1:
                        player["drag"] -= 1
                elif state == "RESULT":
                    if event.key == pygame.K_SPACE:
                        state = "HUB"

        if state == "CASTING":
            cast_power += cast_direction * 2
            if cast_power >= 100 or cast_power <= 0:
                cast_direction *= -1
        elif state == "WAITING":
            bite_timer -= 1
            if bite_timer <= 0:
                hook_fish()
        elif state == "FIGHTING":
            update_fight()

        draw_scene()
        draw_hud()
        
        if state == "HUB":
            msg = font_title.render("PRESS [SPACE] TO CAST YOUR LINE", True, WHITE)
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 100))
            pygame.draw.rect(screen, DARK_GRAY, (200, 320, 500, 260))
            pygame.draw.rect(screen, WHITE, (200, 320, 500, 260), 2)
            shop_title = font_med.render("TACKLE SHOP & UPGRADES", True, YELLOW)
            screen.blit(shop_title, (220, 330))
            r1_status = "EQUIPPED" if player["rod"] == RODS[1] else ("Press [1] Buy $150" if not RODS[1]["unlocked"] else "OWNED")
            r2_status = "EQUIPPED" if player["reel"] == REELS[1] else ("Press [2] Buy $120" if not REELS[1]["unlocked"] else "OWNED")
            screen.blit(font_small.render(f"Rod 2: {RODS[1]['name']} - {r1_status}", True, WHITE), (220, 380))
            screen.blit(font_small.render(f"Reel 2: {REELS[1]['name']} - {r2_status}", True, WHITE), (220, 420))
            ctrl = font_small.render("Controls: [SPACE] Reel/Cast | [UP/DOWN] Adjust Drag", True, WHITE)
            screen.blit(ctrl, (220, 530))

        elif state == "CASTING":
            pygame.draw.rect(screen, DARK_GRAY, (300, 120, 300, 30))
            pygame.draw.rect(screen, GREEN, (300, 120, cast_power * 3, 30))
            pygame.draw.rect(screen, WHITE, (300, 120, 300, 30), 2)
            lbl = font_med.render("Press [SPACE] to Lock Power!", True, WHITE)
            screen.blit(lbl, (WIDTH//2 - lbl.get_width()//2, 80))

        elif state == "WAITING":
            lbl = font_title.render("Waiting for a bite...", True, YELLOW)
            screen.blit(lbl, (WIDTH//2 - lbl.get_width()//2, 100))
            pygame.draw.circle(screen, RED, (350, 350), 6)
            pygame.draw.circle(screen, WHITE, (350, 348), 6)

        elif state == "FIGHTING":
            draw_tension_meter(820, 150, 30, 350, line_tension)
            dist_txt = font_med.render(f"Distance: {fish_distance:.1f} m", True, WHITE)
            drag_txt = font_med.render(f"Reel Drag: {player['drag']}/10 ([UP]/[DOWN])", True, YELLOW)
            reel_hint = font_small.render("HOLD [SPACE] TO REEL", True, GREEN if pygame.key.get_pressed()[pygame.K_SPACE] else WHITE)
            screen.blit(dist_txt, (300, 70))
            screen.blit(drag_txt, (300, 100))
            screen.blit(reel_hint, (300, 130))
            water_x = 180 + min(600, fish_distance * 12)
            pygame.draw.line(screen, WHITE, (140, 150), (water_x, 380), 1)
            pygame.draw.circle(screen, RED, (int(water_x), 380), 5)

        elif state == "RESULT":
            pygame.draw.rect(screen, DARK_GRAY, (200, 200, 500, 200))
            pygame.draw.rect(screen, WHITE, (200, 200, 500, 200), 2)
            res_txt = font_med.render(result_message, True, result_color)
            cont_txt = font_small.render("Press [SPACE] to return to hub", True, WHITE)
            screen.blit(res_txt, (WIDTH//2 - res_txt.get_width()//2, 260))
            screen.blit(cont_txt, (WIDTH//2 - cont_txt.get_width()//2, 330))

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())


import os
import random
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()

pygame.display.set_caption("Falfula Cart")
WIDTH, HEIGHT = 1000, 800

FPS = 60 
PLAYER_VEL = 3
window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []

        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size,size), pygame.SRCALPHA,32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0,0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters","Falfula", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.update_sprite()  


    def jump(self):
        if self.jump_count < 2:
            self.y_vel = -self.GRAVITY * 8
            self.animation_count = 0
            self.jump_count += 1
            if self.jump_count == 1:
                self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
            # Hit effect lasts 1 second
            if self.hit_count > fps:
                self.hit = False
                self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        # Keep the player's position by preserving midbottom (feet) position
        self.rect = self.sprite.get_rect(midbottom=self.rect.midbottom)
        self.mask = pygame.mask.from_surface(self.sprite)


    def draw(self, win, offset_x):
        sprite_rect = self.sprite.get_rect(midbottom=(self.rect.midbottom[0] - offset_x, self.rect.midbottom[1]))
        win.blit(self.sprite, sprite_rect)

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self ,win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 2
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        if "off" in self.fire and len(self.fire["off"]) > 0:
            self.image = self.fire["off"][0]
        else:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire.get(self.animation_name, [])
        if sprites:
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.image = sprites[sprite_index]
            self.animation_count += 1

            self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
            self.mask = pygame.mask.from_surface(self.image)
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class MovingPlatform(Object):
    def __init__(self, x, y, width, height, path, speed=2):
        super().__init__(x, y, width, height, "platform")
        self.path = path  # list of points [(x1, y1), (x2, y2)]
        self.speed = speed
        self.current_point = 0
        self.direction = 1  # 1 or -1

        # simple platform visual: grey rectangle
        self.image.fill((100, 100, 100))
        self.mask = pygame.mask.from_surface(self.image)

    def loop(self):
        target = self.path[self.current_point]
        dx = target[0] - self.rect.x
        dy = target[1] - self.rect.y

        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist < self.speed:
            self.rect.x, self.rect.y = target
            self.current_point += self.direction
            if self.current_point >= len(self.path):
                self.current_point = len(self.path) - 2
                self.direction = -1
            elif self.current_point < 0:
                self.current_point = 1
                self.direction = 1
        else:
            self.rect.x += self.speed * dx / dist
            self.rect.y += self.speed * dy / dist

        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Seed(Object):
    def __init__(self, x, y):
        size = 32
        super().__init__(x, y, size, size, "seed")
        self.seed_sprites = load_sprite_sheets("coins", "", size, size)
        if len(self.seed_sprites) > 0:
            # Just pick first available animation (or sprite) key
            first_key = list(self.seed_sprites.keys())[0]
            self.image = self.seed_sprites[first_key][0]
        else:
            self.image.fill((255, 255, 0))
        self.mask = pygame.mask.from_surface(self.image)

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    __, __, width, height = image.get_rect()
    tiles = []
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = [i * width, j * height]
            tiles.append(pos)
    return tiles, image

def draw(window, background, bg_image, player, objects, offset_x, seeds_collected, hits):
    for tile in background:
        window.blit(bg_image, tuple(tile))
    for obj in objects:
        obj.draw(window, offset_x)
    player.draw(window, offset_x)

    # Draw HUD: top left corner
    font = pygame.font.SysFont("comicsans", 30)
    text_seeds = font.render(f"Seeds collected: {seeds_collected}", True, (255, 255, 255))
    text_hits = font.render(f"Hits: {hits}", True, (255, 0, 0))
    window.blit(text_seeds, (10, 10))
    window.blit(text_hits, (10, 40))

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
            collided_objects.append(obj)
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects, platforms):
    keys = pygame.key.get_pressed()

    player.x_vel = 0

    Collide_left = collide(player, objects, -PLAYER_VEL * 2)
    Collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not Collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not Collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [Collide_left, Collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

def generate_level():
    block_size = 96
    floor_y = HEIGHT - block_size

    floor = [Block(i * block_size, floor_y, block_size) for i in range(-5, 25)]
    objects = floor[:]

    # 2nd layer (one block_size higher than floor, so player can jump up)
    second_layer_y = floor_y - block_size  # 1 layer above floor
    for i in range(5, 20, 2):  # every 2 blocks to create gaps
        objects.append(Block(i * block_size, second_layer_y, block_size))

    # 3rd layer (another block_size above the 2nd layer)
    third_layer_y = second_layer_y - block_size  # 2 layers above floor
    for i in range(7, 22, 3):  # fewer blocks, spaced more widely
        objects.append(Block(i * block_size, third_layer_y, block_size))


    fire_width, fire_height = 16, 32
    fire_width, fire_height = 16, 32

    fire_positions = [7,10, 13, 15,17,20, 22,35,24]

    fires = []
    for pos in fire_positions:
        # Find all blocks in this column (x-position)
        blocks_in_column = [b for b in objects if isinstance(b, Block) and b.rect.x == pos * block_size]

        if blocks_in_column:
            # Get the top block (lowest y)
            top_block = min(blocks_in_column, key=lambda b: b.rect.top)

            # Calculate fire position: center on block, bottom aligned with block top
            fire_x = top_block.rect.x + (block_size - fire_width) // 2
            fire_y = top_block.rect.top - (2*fire_height)  # place fire *above* block

            fire = Fire(fire_x, fire_y, fire_width, fire_height)
            fire.on()
            fires.append(fire)

    objects.extend(fires)


    # Moving platforms: horizontal moving platforms between two points
    platforms = [
        MovingPlatform(10 * block_size, HEIGHT - block_size * 7, block_size * 2, 20,
                       [(10 * block_size, HEIGHT - block_size * 7),
                        (15 * block_size, HEIGHT - block_size * 7)], speed=2),
        MovingPlatform(23 * block_size, HEIGHT - block_size * 4, block_size * 3, 20,
                       [(23 * block_size, HEIGHT - block_size * 4),
                        (28 * block_size, HEIGHT - block_size * 4)], speed=3)
    ]
    objects.extend(platforms)

    # Seeds scattered randomly on platforms and floor
    seeds = []
    seed_positions = []
    for _ in range(15):
        # Random x somewhere between 0 and 28 blocks wide
        x_block = random.randint(0, 28)
        # Y either on floor or on platforms/blocks
        possible_ys = [HEIGHT - block_size]  # floor
        for block in floor:
            possible_ys.append(block.rect.top - 200)
        for platform in platforms:
            possible_ys.append(platform.rect.top - 48)
        y = random.choice(possible_ys)
        x = x_block * block_size + random.randint(0, block_size - 48)
        # Avoid duplicates too close
        if any(abs(x - px) < 32 and abs(y - py) < 32 for px, py in seed_positions):
            continue
        seed_positions.append((x, y))
        seed = Seed(x, y)
        seeds.append(seed)
    objects.extend(seeds)

    return objects, platforms, fires, seeds

def main():
    run = True
    clock = pygame.time.Clock()

    background, bg_image = get_background("Purple.png")

    player = Player(100, HEIGHT - 96 * 2, 32, 64)
    objects, platforms, fires, seeds = generate_level()

    seeds_collected = 0
    hits = 0
    offset_x = 0

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()

        handle_move(player, objects, platforms)

        # Update moving platforms
        for platform in platforms:
            platform.loop()

        # Move player with platform if standing on one
        player_on_platform = False
        for platform in platforms:
            if player.rect.bottom == platform.rect.top and \
                player.rect.right > platform.rect.left and \
                player.rect.left < platform.rect.right:
                    # Move player horizontally with the platform
                    player.rect.x += platform.speed * platform.direction
                    # Reset jump count since player is standing on platform
                    player.landed()
                    player_on_platform = True


        # Player physics update
        player.loop(FPS)
        
        for fire in fires:
            fire.loop()

        # Collision with seeds: collect from any side
        for seed in seeds[:]:
            if pygame.sprite.collide_mask(player, seed):
                seeds_collected += 1
                seeds.remove(seed)
                if seed in objects:
                    objects.remove(seed)
                # No hit on seed collection

        # Player hit counter
        if player.hit:
            hits += 1
            player.hit = False  # reset hit so not double-counted
            player.hit_count = 0

        # Scroll left and right with player, clamp offset_x
        offset_x = player.rect.centerx - WIDTH // 2
        max_offset = 28 * 96 - WIDTH
        if offset_x < 0:
            offset_x = 0
        elif offset_x > max_offset:
            offset_x = max_offset

        draw(window, background, bg_image, player, objects, offset_x, seeds_collected, hits)

    pygame.quit()

if __name__ == "__main__":
    main()

import math
import random
import pygame
from sys import exit

from pygame.mixer_music import set_volume

pygame.init()
clock = pygame.time.Clock()

# Window
w_height = 720
w_width = 550
window = pygame.display.set_mode((w_width, w_height))

# Images
bird_images = [pygame.transform.scale(pygame.image.load("assets/birddown.png"), (70, 50)),
               pygame.transform.scale(pygame.image.load("assets/birdmid.png"), (70, 50)),
               pygame.transform.scale(pygame.image.load("assets/birdup.png"), (70, 50))]
skyline_image = pygame.transform.scale(pygame.image.load("assets/bg.png"), (550, 750))
ground_image = pygame.transform.scale(pygame.image.load("assets/ground.png"), (550, 450))
topPipe_image = pygame.image.load("assets/topPipe.png")
bottomPipe_image = pygame.image.load("assets/bottomPipe.png")
game_over_image = pygame.image.load("assets/gameover.png")
start_image = pygame.image.load("assets/start.png")

#Sound
try:
    pygame.mixer.music.load("assets/bgmusic.mp3")
    pygame.mixer.music.set_volume(0.35)
    score_sound = pygame.mixer.Sound("assets/scoresound.mp3")
    score_sound.set_volume(0.5)
    flap_sound = pygame.mixer.Sound("assets/flapsound.mp3")
    flap_sound.set_volume(0.1)
    hit_sound = pygame.mixer.Sound("assets/hitsound.mp3")
    hit_sound,set_volume(0.5)
except pygame.error:
    print("Sound files not found. Game will run without audio.")
    score_sound = None
    flap_sound = None
    hit_sound = None


# Game
scroll_speed = 1
bird_startpos = (100, 250)
font = pygame.font.SysFont('Times New Roman', 26, bold=True)
quit_game = True

class Raindrop:
    def __init__(self):
        self.x = random.randint(0,w_width)
        self.y = random.randint(-50, -10)
        self.speed = random.randint(3, 8)
        self.length = random.randint(10, 20)
        self.width = random.randint(1, 3)

    def update(self):
        self.y += self.speed
        if self.y > w_height:
            self.x = random.randint(0, w_width)
            self.y = random.randint(-50, -10)
            self.speed = random.randint(3, 8)

    def draw(self, surface):
        pygame.draw.line(surface, (100, 150, 255),
                         (self.x, self.y),
                         (self.x, self.y + self.length),
                         self.width)

class Bird(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = bird_images[0]
        self.rect = self.image.get_rect()
        self.rect.center = bird_startpos
        self.image_index = 0
        self.vel = 0
        self.flap = False
        self.alive = True

    def update(self, user_input):
        # Animate bird
        if self.alive:
            self.image_index += 1
        if self.image_index >= 30:
            self.image_index = 0
        self.image = bird_images[self.image_index // 10]

        # Gravity and flap
        self.vel += 0.5
        if self.vel > 7:
            self.vel = 7
        if self.rect.y < 600:
            self.rect.y += int(self.vel)
        if self.vel == 0:  # At max point
            self.flap = False

        # Rotate bird
        self.image = pygame.transform.rotate(self.image, self.vel * -3)

        # User Input
        if user_input[pygame.K_SPACE] and not self.flap and self.rect.y > 0 and self.alive:
            self.flap = True
            self.vel = -7
            # Play flap sound
            if flap_sound:
                flap_sound.play()


class Pipes(pygame.sprite.Sprite):
    def __init__(self, x, y, image, pipe_type):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.enter, self.exit, self.passed = False, False, False
        self.pipe_type = pipe_type

        # Oscillation parameters
        self.base_y = y
        self.oscillation_amplitude = random.randint(10, 30)  # Max up/down movement
        self.oscillation_speed = random.uniform(0.005, 0.001)  # Speed of oscillation

    def update(self):
        global score, scroll_speed

        # Move pipe
        self.rect.x -= scroll_speed
        self.rect.y = self.base_y + self.oscillation_amplitude * math.sin(
            pygame.time.get_ticks() * self.oscillation_speed + self.rect.x * 0.01)

        if self.rect.x <= -w_width:
            self.kill()

        # Score
        if self.pipe_type == 'bottom':
            if bird_startpos[0] > self.rect.topleft[0] and not self.passed:
                self.enter = True
            if bird_startpos[0] > self.rect.topright[0] and not self.passed:
                self.exit = True
            if self.enter and self.exit and not self.passed:
                self.passed = True
                score += 1
                scroll_speed += 0.2  # Increase speed by 0.2 after each point
                if scroll_speed == 5: #Max
                    scroll_speed = 5
                # Play score sound
                if score_sound:
                    score_sound.play()


class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = ground_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def update(self):
        # Move ground
        self.rect.x -= scroll_speed
        if self.rect.x <= -w_width:
            self.kill()


# Exit game
def quit_game():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()


# Main Game method
def main():
    global score, scroll_speed
    score = 0
    scroll_speed = 1  # Reset scroll speed when starting a new game
    rain_active = False
    rain_start_time = 0
    last_rain_time = pygame.time.get_ticks()
    rain_interval = 15000  # every 15 seconds
    rain_duration = random.randint(6000,10000)  # how long rain lasts
    raindrops = [Raindrop() for _ in range(120)]

    # Instantiate bird
    bird = pygame.sprite.GroupSingle()  # Manage 1 sprite
    bird.add(Bird())

    # Initialise pipes
    pipe_timer = 0
    pipes = pygame.sprite.Group()

    # Instantiate initial ground - spawn multiple pieces to ensure coverage
    x_posground, y_posground = 0, 470
    ground = pygame.sprite.Group()
    ground.add(Ground(x_posground, y_posground))
    ground.add(Ground(w_width, y_posground))  # Add a second ground piece

    run = True
    while run:
        quit_game()  # Quit

        window.fill((255, 0, 200))  # Reset frame - black rgb
        background = pygame.image.load("assets/ground.png").convert()
        window.blit(background, (0, 0))

        # User input
        user_input = pygame.key.get_pressed()

        # Draw bg
        window.blit(skyline_image, (0, 0))

        # Spawn ground - improved logic to prevent gaps
        rightmost_x = 0
        for ground_piece in ground:
            if ground_piece.rect.right > rightmost_x:
                rightmost_x = ground_piece.rect.right

        # Spawn new ground when the rightmost piece is close to the screen edge
        if rightmost_x < w_width + (scroll_speed * 60):  # 60 frames buffer
            ground.add(Ground(rightmost_x, y_posground))

        # Draw pipes, ground, bird
        pipes.draw(window)
        ground.draw(window)
        bird.draw(window)

        # Display score
        score_text = font.render('Score : ' + str(score), True, pygame.Color('pink'))
        window.blit(score_text, (20, 20))

        #Display rain
        current_time = pygame.time.get_ticks()

        # Start rain every 5 seconds
        if current_time - last_rain_time >= rain_interval:
            rain_active = True
            rain_start_time = current_time
            last_rain_time = current_time

        # Stop rain after duration
        if rain_active and current_time - rain_start_time >= rain_duration:
            rain_active = False

        # Update pipes, ground, bird
        if bird.sprite.alive:
            pipes.update()
            ground.update()
        bird.update(user_input)

        # Collision detection - using mask collision for pixel-perfect detection
        col_pipes = pygame.sprite.spritecollide(bird.sprites()[0], pipes, False, pygame.sprite.collide_mask)
        col_ground = pygame.sprite.spritecollide(bird.sprites()[0], ground, False, pygame.sprite.collide_mask)
        if col_pipes or col_ground:
            if bird.sprite.alive: #Only play collision sound once
                if hit_sound:
                    hit_sound.play()
                # Stop background music when game over
                pygame.mixer.music.stop()
            bird.sprite.alive = False
            if col_ground:
                window.blit(game_over_image, (w_width // 2 - game_over_image.get_width() // 2,
                                              w_height // 2 - game_over_image.get_height() // 2))
                if user_input[pygame.K_ESCAPE]:  # reset
                    score = 0
                    break

        # Spawn pipes
        adjusted_pipe_interval = max(200, int(1 / scroll_speed))
        if  score > 8:
            adjusted_pipe_interval = max(50, int(1 / scroll_speed))
        if pipe_timer <= 0 and bird.sprite.alive:
            xtop, xbottom = 550, 550
            ytop = random.randint(-600, -480)
            ybottom = ytop + random.randint(160, 220) + bottomPipe_image.get_height()
            pipes.add(Pipes(xtop, ytop, topPipe_image, 'top'))
            pipes.add(Pipes(xbottom, ybottom, bottomPipe_image, 'bottom'))
            pipe_timer = adjusted_pipe_interval
        pipe_timer -= 1

        # Draw rain overlay
        if rain_active:
            for drop in raindrops:
                drop.update()
                drop.draw(window)

        clock.tick(60)
        pygame.display.update()


# Menu
def menu():
    global quit_game
    while quit_game:
        quit_game()

        # Draw menu
        window.fill((255, 0, 158))
        window.blit(skyline_image, (0, 0))
        window.blit(ground_image, (0, 470))
        window.blit(bird_images[0], (100, 125))
        window.blit(start_image, (w_width // 2 - start_image.get_width() // 2,
                                  w_height // 2 - start_image.get_height() // 2))

        # User input
        user_input = pygame.key.get_pressed()
        if user_input[pygame.K_SPACE]:
            # Start background music when game begins
            try:
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            except pygame.error:
                pass  # Continue without music if file not found
            main()

        pygame.display.update()


menu()
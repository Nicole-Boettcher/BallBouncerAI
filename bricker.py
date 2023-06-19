# current bugs: board lights up inconsistently

import os
import random
import math
import time

import neat
import numpy
import pygame
from os import listdir
from os.path import isfile, join
pygame.font.init()  # init font

generation = 0
opening_screen = True
BIG_FONT = pygame.font.SysFont("comicsans", 40)
SMALL_FONT = pygame.font.SysFont("comicsans", 15)
BG_COLOR = pygame.Color(80, 60, 70)

WIDTH, HEIGHT = 900, 700
FPS = 60

# goal is to make brick breaker, have a user version and an AI version. The AI should work first and then be presentable
# need a board to slide along the bottom, and a ball to bounce around the screen

pygame.init()

pygame.display.set_caption("Brick Breaker")
title = BIG_FONT.render("NEAT algorithm learns to bounce ball!", False, (255, 255, 255))
stats = ["Statistics:",
             "Inputs: Board x position, Ball x position, Ball y position, Ball x speed, Ball y speed",
             "Output: Board movement",
             "Activation function: Relu",
             "Population size: 80",
             "",
             "Fitness function depends on how long the board stays alive and how far the board is from the ball when it dies"
             ]
rendered_stats = []
for line in stats:
    rendered_stats.append(SMALL_FONT.render(line, False, (255,255,255)))
continue_text = SMALL_FONT.render("Press ENTER to begin training", False, (255, 255, 255))


screen = pygame.display.set_mode((WIDTH, HEIGHT))

BOARD_SCALE = 4
BALL_SCALE = 1

def load_sprite(object_width, object_height, name, scale):
    path = join("Images", name)
    sprite_sheet = pygame.image.load(path).convert_alpha()  # load that png

    animation = []
    for i in range(sprite_sheet.get_width() // object_width):
        surface = pygame.Surface((object_width, object_height), pygame.SRCALPHA,
                                 32)  # create a surface the size of the image we want
        rect = pygame.Rect(i * object_width, 0, object_width, object_height)
        surface.blit(sprite_sheet, (0, 0), rect)
        animation.append(pygame.transform.scale(surface, (32*scale, 32*scale)))

    return animation

def draw_all(screen, boards, balls, generation):
    screen.fill(BG_COLOR)
    position = 50
    score_label = BIG_FONT.render("Generation: " + str(generation) + "  Paddles Left: " + str(len(boards)), False, (255, 255, 255))
    screen.blit(score_label, (0, 0))
    for board, ball in zip(boards, balls):
        screen.blit(board.current_image, (board.rect.x, board.rect.y))
        screen.blit(ball.current_image, (ball.rect.x, ball.rect.y))
        pygame.draw.line(screen, (255, 0, 0), (board.rect.centerx, board.rect.bottom-30), (ball.rect.centerx, ball.rect.y +16), 1)
        if len(boards) < 25:
            score_label = SMALL_FONT.render("ID: " + str(board.iden) + "   Fitness: " + str(round(board.SCORE)), False, (255, 255, 255))
            screen.blit(score_label, (0, position))
            position += 20

def ready_screen(screen):
    screen.fill(BG_COLOR)
    title_x = (WIDTH - title.get_width()) // 2
    screen.blit(title, (title_x, HEIGHT/7))
    for i, line in enumerate(rendered_stats):
        screen.blit(line, ((WIDTH - line.get_width())//2, HEIGHT//4 + (i*25)))

    screen.blit(continue_text, ((WIDTH-continue_text.get_width())//2, HEIGHT-50))
    pygame.display.update()


class Board(pygame.sprite.Sprite):
    ANIMATION_DELAY = 20
    SCORE = 0

    def __init__(self, iden):
        super().__init__()
        self.iden = iden
        self.x_vel = 5
        self.animation_count = 0
        self.board_animation = load_sprite(32, 32, "Board.png", BOARD_SCALE)
        self.current_image = self.board_animation[0]
        self.rect = pygame.Rect(WIDTH/2, HEIGHT - 32*BOARD_SCALE, 32*BOARD_SCALE, 32*BOARD_SCALE)
        self.mask = pygame.mask.from_surface(self.current_image)
        self.hit = False

    def move_right(self):

        if self.rect.x < WIDTH - 32*BOARD_SCALE:
            self.rect.x += self.x_vel
        #print("current x pos: ", self.rect.x)

    def move_left(self):

        if self.rect.x > 0:
            self.rect.x += self.x_vel * -1
        #print("current x pos: ", self.rect.x)

    def update_animation(self, index):
        # sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.board_animation)
        # should toggle between the two images
        self.current_image = self.board_animation[index]
        self.animation_count += 1
        #print("count: ", self.animation_count)
        #print("sprite index: ", index)

    def update(self):
        # self.rect = self.current_image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.rect = self.current_image.get_rect(topleft=(self.rect.x, self.rect.y))

        self.mask = pygame.mask.from_surface(self.current_image)
        # window.blit(self.current_image, (self.rect.x, self.rect.y))
        #print(self.rect.x, self.rect.y)

    def loop(self):
        if self.hit:
            # self.SCORE += 5
            self.update_animation(1)
        else:
            self.update_animation(0)

        #print("animation count: ", self.animation_count)

        # print("SCORE: ", self.SCORE)
        self.update()

class Ball(pygame.sprite.Sprite):
    ANIMATION_DELAY = 20


    def __init__(self):
        super().__init__()
        self.x_vel = 5
        self.y_vel = -5
        self.animation_count = 0
        self.board_animation = load_sprite(32, 32, "Ball.png", BALL_SCALE)
        self.current_image = self.board_animation[0]
        random_x = random.randint(10, WIDTH-32)
        self.rect = pygame.Rect(random_x, HEIGHT/2, 32*BALL_SCALE, 32*BALL_SCALE)
        self.mask = pygame.mask.from_surface(self.current_image)

    def wall_collide(self):
        if self.rect.x <= 0 or self.rect.x >= WIDTH - 32*BALL_SCALE - 2: # hit left wall
            self.x_vel *= -1.01
        if self.rect.y < 0:
            self.y_vel *= -1.01

        if self.rect.y >= HEIGHT - 32*BALL_SCALE:
            return self

    def move(self):
        self.rect.x += self.x_vel
        self.rect.y += self.y_vel
        #print("current x pos: ", self.rect.x)

    def update_animation(self):
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.board_animation)
        # should toggle between the two images
        self.current_image = self.board_animation[sprite_index]
        self.animation_count += 1
        # print(self.current_image)

    def update(self):
        # self.rect = self.current_image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.rect = self.current_image.get_rect(topleft=(self.rect.x, self.rect.y))

        self.mask = pygame.mask.from_surface(self.current_image)
        # window.blit(self.current_image, (self.rect.x, self.rect.y))
        #print(self.rect.x, self.rect.y)

    def loop(self):
        if self.wall_collide() is None:
            self.move()
            self.update_animation()
            self.update()
            return False
        else:
            return True


def collide(ball, board):

    collided_obj = None
    #for obj in objects:
    if pygame.sprite.collide_mask(ball, board):
        collided_obj = board


    return collided_obj

# need to use collide for ball collide with board and ball collide with bricks and need to know which brick

def board_movement(board):

    keys_pressed = pygame.key.get_pressed()
    if keys_pressed[pygame.K_LEFT] and board.rect.x > 0:

        board.move(-1)
    elif keys_pressed[pygame.K_RIGHT] and board.rect.x < WIDTH - 32*BOARD_SCALE:
        board.move(1)

def eval_genomes(genomes, config):

    global generation
    global opening_screen

    generation += 1
    clock = pygame.time.Clock()

    nets = []
    ge = []
    boards = []
    balls = []
    iden = 1
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        boards.append(Board(iden))
        balls.append(Ball())
        g.fitness = 0
        ge.append(g)
        iden += 1

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            elif opening_screen is True:
                ready_screen(screen)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        opening_screen = False

        if opening_screen is False:
            for i, board in enumerate(boards):
                #distance = numpy.sqrt((balls[i].rect.centerx - boards[i].rect.centerx) ** 2 + (balls[i].rect.y - HEIGHT) ** 2)
                #print(board.iden, ", distance: ", distance)
                output = nets[i].activate((board.rect.centerx, balls[i].rect.centerx, balls[i].rect.centery, balls[i].x_vel, balls[i].y_vel))
                #print(output)
                if output[0] > 0.5:
                    board.move_left()
                else:
                    board.move_right()

            current_index = 0
            count = 0
            print(balls[0].x_vel)
            #for board in boards:
                #print(board.iden, " score: ", board.SCORE)
            for count in range(len(boards)):
                #print("count: ", count)
                #print(current_index, ": ", boards[current_index].iden)
                # board_movement(boards[i])
                collided_object = collide(balls[current_index], boards[current_index])
                if collided_object == boards[current_index]:
                    boards[current_index].hit = True
                    balls[current_index].rect.bottom = boards[current_index].rect.bottom-30
                    balls[current_index].y_vel *= -1
                    boards[current_index].SCORE += 50
                    ge[current_index].fitness += 50
                else:
                    boards[current_index].hit = False

                boards[current_index].loop()
                ball_lost = balls[current_index].loop()
                if ball_lost is True:
                    print(current_index, " DEAD")
                    print("before death fitness: ", ge[current_index].fitness)
                    distance = abs(boards[current_index].rect.centerx - balls[current_index].rect.centerx)
                    ge[current_index].fitness -= distance/15
                    print("after death fitness: ", ge[current_index].fitness)
                    print("------------------------------------------------")
                    balls.pop(current_index)
                    boards.pop(current_index)
                    nets.pop(current_index)
                    ge.pop(current_index)
                else:
                    boards[current_index].SCORE += 0.1
                    ge[current_index].fitness += 0.1
                    current_index += 1

                count += 1



            if len(boards) <= 0:
                run = False
                break

            draw_all(screen, boards, balls, generation)
            pygame.display.update()


def run_neat(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(eval_genomes, config)

if __name__ == "__main__":
    #main(window)  # so it only runs when run directly , not if imported?
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run_neat(config_path)



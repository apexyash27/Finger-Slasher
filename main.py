import pygame
import cv2
import mediapipe as mp
from random import randint
import os

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

cam = cv2.VideoCapture(0)

pygame.init()
pygame.mixer.init()  
fruits_list = []
myfont = pygame.font.SysFont("monospace", 32)

# Load sounds
pygame.mixer.music.load('./sounds/MainTheme.wav')
pygame.mixer.music.play(-1)  
pygame.mixer.music.set_volume(0.3) 

fruit_slice_sound = pygame.mixer.Sound('./sounds/FruitSlice.wav')
fruit_slice_sound.set_volume(0.7)  

# Game window
GAME_WIDTH = 1000
GAME_HEIGHT = 600
win = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))

os.environ['SDL_VIDEO_WINDOW_POS'] = '400,100'  

# Load images
bg = pygame.image.load('./images/bg.png')
bg = pygame.transform.scale(bg, (GAME_WIDTH, GAME_HEIGHT))

FRUIT_SIZE = (80, 80) 
BANANA_PIECE_SIZE = (200, 200) 
STAR_SIZE = (100, 100)   

watermelon_temp = [pygame.image.load('./images/Watermelon.png'), 
                   pygame.image.load('./images/Watermelon1.png'),
                   pygame.image.load('./images/Watermelon2.png')]
watermelon = [pygame.transform.scale(img, FRUIT_SIZE) for img in watermelon_temp]

banana_temp = [pygame.image.load('./images/Banana.png'), 
               pygame.image.load('./images/Banana1.png'),
               pygame.image.load('./images/Banana2.png')]
banana = [pygame.transform.scale(banana_temp[0], FRUIT_SIZE),
          pygame.transform.scale(banana_temp[1], BANANA_PIECE_SIZE),
          pygame.transform.scale(banana_temp[2], BANANA_PIECE_SIZE)] 

orange_temp = [pygame.image.load('./images/Orange.png'), 
               pygame.image.load('./images/Orange1.png'),
               pygame.image.load('./images/Orange2.png')]
orange = [pygame.transform.scale(img, FRUIT_SIZE) for img in orange_temp]

star_temp = pygame.image.load('./images/star1.png')
star = pygame.transform.scale(star_temp, STAR_SIZE)

pygame.display.set_caption("Finger Slasher")
clock = pygame.time.Clock()

class Fruit:
    def __init__(self, x, y, pic, vel_x=0, vel_y=15, gravity=0.5, is_banana_piece=False):
        self.x = float(x)
        self.y = float(y)
        self.pic = pic
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.gravity = gravity
        self.angle = 0
        self.rotation_speed = randint(-5, 5)
        self.initial_x = x
        self.is_banana_piece = is_banana_piece 
        
    def update(self):
        self.y -= self.vel_y
        self.vel_y -= self.gravity
        
        if self.initial_x <= GAME_WIDTH // 2:
            self.x += 1.5
        else:
            self.x -= 1.5
            
        self.angle += self.rotation_speed
        if self.angle >= 360:
            self.angle = 0
        elif self.angle < 0:
            self.angle = 359
            
    def draw(self):
        rotated_img = pygame.transform.rotate(self.pic, self.angle)
        rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
        win.blit(rotated_img, rect)
        
    def get_rect(self):
        if self.is_banana_piece:
            size = BANANA_PIECE_SIZE
        else:
            size = FRUIT_SIZE
            
        return pygame.Rect(int(self.x - size[0]//2), 
                          int(self.y - size[1]//2), 
                          size[0], size[1])

win.blit(bg, (0, 0))
pygame.display.update()

# Game variables
cursor_x = 0
cursor_y = 0
run = True
score = 0
spawn_timer = 0
spawn_delay = 60 

while run:
    ret, frame = cam.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = hands.process(rgb_frame)
    
    finger_detected = False
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            finger_tip = hand_landmarks.landmark[8]
            h, w, c = frame.shape
            finger_tip_x = int(finger_tip.x * w)
            finger_tip_y = int(finger_tip.y * h)
            
            cv2.circle(frame, (finger_tip_x, finger_tip_y), 10, (0, 0, 255), -1)
            
            cursor_y = int((finger_tip_y / h) * GAME_HEIGHT)
            cursor_x = int((finger_tip_x / w) * GAME_WIDTH)
            finger_detected = True
    
    small_frame = cv2.resize(frame, (320, 240))
    cv2.namedWindow("Finger Tracking", cv2.WINDOW_NORMAL)
    cv2.moveWindow("Finger Tracking", 50, 100) 
    cv2.imshow("Finger Tracking", small_frame)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    
    # Clear screen
    win.blit(bg, (0, 0))
    
    # Spawn fruits
    spawn_timer += 1
    if spawn_timer >= spawn_delay:
        spawn_timer = 0
        num_fruits = randint(1, 3)
        
        for _ in range(num_fruits):
            pos_x = randint(100, GAME_WIDTH - 100)
            pos_y = GAME_HEIGHT + 50 
            fruit_type = randint(0, 2)
            
            if fruit_type == 0:
                fruit_img = watermelon[0]
            elif fruit_type == 1:
                fruit_img = banana[0]
            else:
                fruit_img = orange[0]
                
            vel_y = randint(18, 25)
            fruits_list.append(Fruit(pos_x, pos_y, fruit_img, vel_y=vel_y))
    
    for fruit in fruits_list[:]: 
        fruit.update()
        fruit.draw()
        
        # Check collision with cursor (finger)
        if finger_detected:
            cursor_rect = pygame.Rect(cursor_x - STAR_SIZE[0]//2, 
                                    cursor_y - STAR_SIZE[1]//2, 
                                    STAR_SIZE[0], STAR_SIZE[1])
            
            if fruit.get_rect().colliderect(cursor_rect):
                # Only slice whole fruits (not already sliced pieces)
                if (fruit.pic == watermelon[0] or fruit.pic == banana[0] or fruit.pic == orange[0]):
                    score += 1
                    
                    # Play fruit slice sound
                    fruit_slice_sound.play()
                    
                    # Create sliced fruit pieces
                    if fruit.pic == watermelon[0]:
                        piece1 = Fruit(fruit.x - 20, fruit.y - 10, watermelon[1], 
                                     vel_x=-3, vel_y=fruit.vel_y)
                        piece2 = Fruit(fruit.x + 20, fruit.y + 10, watermelon[2], 
                                     vel_x=3, vel_y=fruit.vel_y)
                    elif fruit.pic == banana[0]:
                        piece1 = Fruit(fruit.x - 20, fruit.y - 10, banana[1], 
                                     vel_x=-3, vel_y=fruit.vel_y, is_banana_piece=True)
                        piece2 = Fruit(fruit.x + 20, fruit.y + 10, banana[2], 
                                     vel_x=3, vel_y=fruit.vel_y, is_banana_piece=True)
                    else: 
                        piece1 = Fruit(fruit.x - 20, fruit.y - 10, orange[1], 
                                     vel_x=-3, vel_y=fruit.vel_y)
                        piece2 = Fruit(fruit.x + 20, fruit.y + 10, orange[2], 
                                     vel_x=3, vel_y=fruit.vel_y)
                    
                    fruits_list.extend([piece1, piece2])
                    fruits_list.remove(fruit)
        
        if fruit.y > GAME_HEIGHT + 100:
            fruits_list.remove(fruit)
    
    # Draw cursor (star) at finger position
    if finger_detected:
        win.blit(star, (cursor_x - STAR_SIZE[0]//2, cursor_y - STAR_SIZE[1]//2))
    
    # Display score
    scoretext = myfont.render("Score: " + str(score), True, (255, 255, 255))
    win.blit(scoretext, (20, 20))
    
    # Display FPS for performance monitoring
    fps = int(clock.get_fps())
    fps_text = myfont.render("FPS: " + str(fps), True, (255, 255, 255))
    win.blit(fps_text, (GAME_WIDTH - 170, 20))
    
    pygame.display.flip()
    clock.tick(60) 
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cam.release()
hands.close()

pygame.mixer.quit() 
pygame.quit()

cv2.destroyAllWindows()
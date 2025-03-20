# I2C Setup for my particular screen (ssd1306) taken from Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-ssd1306-oled-micropython/
# Uses Adafruit ssd1306 driver

from machine import Pin, SoftI2C
import ssd1306
import time
import random

target_framerate = 10
ticks_per_second = int(1000 / target_framerate)

# You can choose any other combination of I2C pins
i2c = SoftI2C(scl=Pin(5), sda=Pin(4))

oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Conway's Game of Life

# Rules:
# 1. Live cell with fewer than 2 live neighbours dies
# 2. Any cell with 3 live neighbours survives
# 3. Any cell with more than 3 neighbours dies
# 4. Any dead cell with exactly 3 neighbours becomes live

cell_size = 2 # width and height of cells when drawn on the display. 1 is very slow!
cells_w = int(oled_width / cell_size)
cells_h = int(oled_height / cell_size)
prev_states = [0] * (cells_w * cells_h)
curr_states = [0] * (cells_w * cells_h)

prev_living = 0
stable_generations = 0
stable_generation_limit = 20


def fill_random_states(states):
    global prev_living
    
    prev_living = 0
    for i in range(len(states)):
        states[i] = random.getrandbits(1) # returns a random number with 1 bit, so 0 or 1
        prev_living += states[i]

# Will be switched to prev_states on first iteration
fill_random_states(curr_states)


# Everything merged into one function gives the best performance
def update():
    global cells_w, cells_h, cell_size
    global prev_states, curr_states
    global prev_living, stable_generations
    
    # Reset if things have gotten too stable
    if stable_generations > stable_generation_limit:
        print("Reached stable generation limit ({}). Resetting.".format(stable_generation_limit))
        fill_random_states(curr_states)
        stable_generations = 0
    
    # Swap current and previous generations
    temp_states = prev_states
    prev_states = curr_states
    curr_states = temp_states
    
    # For inlining get_live_neighbour_count
    w = cells_w
    h = cells_h
    size = w * h
    states = prev_states
    
    # Clear the oled
    oled.fill(0)
    
    # Update and overwrite states
    curr_living = 0
    for y in range(h):
        for x in range(w):
            i = y * w + x
            
            # Putting this code inline seems to give a minor performance uplift vs a separate function
            # Currently it takes about 150ms for the inlined version and 230ms for the function call version
            lofs = -1 if x > 0 else w-1
            rofs = 1 if x < w-1 else -w+1
            tofs = -w if y > 0 else size-w
            bofs = w if y < h-1 else -size+w

            # Calculate neighbours
            count = 0
            count += states[i + tofs + lofs] # 1: Top Left
            count += states[i + tofs]        # 2: Top
            count += states[i + tofs + rofs] # 3: Top Right
            count += states[i + lofs]        # 4: Left
            count += states[i + rofs]        # 5: Right
            count += states[i + bofs + lofs] # 6: Bottom Left
            count += states[i + bofs]        # 7: Bottom
            count += states[i + bofs + rofs] # 8: Bottom Right
            
            state = prev_states[i]
            if count == 3:
                state = 1
            elif count != 2:
                state = 0
            curr_states[i] = state
            curr_living += state
            
            # Draw the current cell if it is alive
            if state == 1:
                for cy in range(cell_size):
                    for cx in range(cell_size):
                        oled.pixel(x * cell_size + cx, y * cell_size + cy, 1)
    
    oled.show()
            
    # This technique is not infallible, but should generally reset when things get too stable
    if abs(curr_living - prev_living) < 4:
        stable_generations += 1
    else:
        prev_living = curr_living


def refresh():
    update()


# Main loop
while True:
    ticks = time.ticks_ms()
    
    refresh()
    
    # Currently I'm not even hitting 10fps, so perhaps this is not very useful!
    # This time keeping code sucks anyway...
    tick_delta = time.ticks_diff(time.ticks_ms(), ticks)
    #time.sleep_ms(ticks_per_second - tick_delta)
    #print(tick_delta)


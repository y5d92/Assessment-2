# I acknowledge the use of Gemini (version Flash 2.5, Google, https://gemini.google.com/)
# to co-create this code for the Spacewaves Defender game.

import tkinter as tk
import random
import time

# --- Game Constants ---
# Use these as the reference resolution for scaling
INITIAL_CANVAS_WIDTH = 600
INITIAL_CANVAS_HEIGHT = 700

# Initial sizes for proportional scaling
PLAYER_SIZE_BASE = 30 
ENEMY_HEIGHT_BASE = 30

PLAYER_SPEED = 15
ENEMY_SPEED_INITIAL = 3
ENEMY_SPAWN_INTERVAL = 1500  # milliseconds
GAME_LOOP_DELAY = 30  # milliseconds (approx 33 FPS)

class SpacewavesGame:
    """
    A simple 2D arcade game using Tkinter canvas.
    Player dodges waves of enemies coming from the top.
    """
    def __init__(self, master):
        self.master = master
        master.title("Spacewaves Defender")
        
        # Allow resizing
        master.resizable(True, True) 
        
        # Current dimensions state (starts with initial values)
        self.canvas_width = INITIAL_CANVAS_WIDTH
        self.canvas_height = INITIAL_CANVAS_HEIGHT
        self.scale_factor = 1.0
        self.current_player_size = PLAYER_SIZE_BASE
        
        # High Score persists across multiple games in the same session
        self.high_score = 0 
        
        # Setup Canvas (Initial size). Use fill=tk.BOTH and expand=True for responsiveness
        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="#000022")
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True) 
        
        # Bind the Configure event to the canvas to handle resizing
        self.canvas.bind('<Configure>', self.on_resize)
        
        self.game_paused = True # Game starts paused
        self.start_text_id = None
        
        self.init_game_objects()
        
        # Start the game loop which immediately hits the pause check
        self.game_loop()
        
    def get_scaled_font(self, base_size):
        """Returns a font tuple scaled by the current scale factor, ensuring minimum readability."""
        new_size = max(10, int(base_size * self.scale_factor))
        return ('Inter', new_size, 'bold')

    def on_resize(self, event):
        """Handle canvas resizing and update internal dimensions and UI."""
        # Update current dimensions
        self.canvas_width = event.width
        self.canvas_height = event.height
        
        # Calculate scaling factor based on height (to keep vertical elements readable)
        self.scale_factor = self.canvas_height / INITIAL_CANVAS_HEIGHT
        
        # Update player size and position based on new dimensions
        self.reposition_player()
        
        # Reposition and re-scale static UI elements
        self.reposition_ui()
        
    def init_game_objects(self):
        """Initializes or resets all game elements and state."""
        # Clear the canvas of all existing items
        self.canvas.delete(tk.ALL)
        
        # Reset current dimensions/scale based on current window size
        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()
        if self.canvas_height == 1: # Avoid division by zero if not fully drawn yet
             self.canvas_height = INITIAL_CANVAS_HEIGHT
        self.scale_factor = self.canvas_height / INITIAL_CANVAS_HEIGHT
        self.current_player_size = int(PLAYER_SIZE_BASE * self.scale_factor)
        
        # Game State (High score is NOT reset here)
        self.game_running = True
        self.score = 0
        self.enemies = []
        self.enemy_speed = ENEMY_SPEED_INITIAL
        self.last_spawn_time = time.time() * 1000
        self.score_popups = [] 

        # Player setup
        self.player_x = self.canvas_width // 2
        self.player_y = self.canvas_height - (50 * self.scale_factor)
        self.player_vel_x = 0
        self.player_shape = self.canvas.create_polygon(
            self.get_player_coords(self.player_x, self.player_y),
            fill="#00FFC0", 
            outline="#00AA80"
        )

        # Score Label
        self.score_text = self.canvas.create_text(
            10, 10, anchor=tk.NW, 
            text=f"Score: {self.score} | High Score: {self.high_score}", 
            fill="#FFFFFF", font=self.get_scaled_font(16)
        )

        # Show initial 'Press SPACE to Start' screen
        if self.game_paused:
            self.start_text_id = self.canvas.create_text(
                self.canvas_width // 2, self.canvas_height // 2, 
                text="PRESS SPACE TO START", 
                fill="#00FFC0", font=self.get_scaled_font(28),
                tag="pause_text"
            )

        # Bind initial controls
        self.bind_controls()

    def bind_controls(self):
        """Binds the movement controls, pause key, and unbinds retry key."""
        # Movement controls remain the same, though the resulting change in x is applied to scaled player
        self.master.bind('<Left>', lambda event: self.set_player_velocity(-PLAYER_SPEED))
        self.master.bind('<Right>', lambda event: self.set_player_velocity(PLAYER_SPEED))
        self.master.bind('<KeyRelease-Left>', lambda event: self.stop_player_velocity('Left'))
        self.master.bind('<KeyRelease-Right>', lambda event: self.stop_player_velocity('Right'))
        self.master.bind('<space>', self.toggle_pause) 
        
        self.master.unbind('<Return>')

    def unbind_controls(self):
        """Unbinds all movement and pause controls."""
        self.master.unbind('<Left>')
        self.master.unbind('<Right>')
        self.master.unbind('<KeyRelease-Left>')
        self.master.unbind('<KeyRelease-Right>')
        self.master.unbind('<space>')

    def toggle_pause(self, event=None):
        """Toggles the game state between running and paused."""
        if not self.game_running:
            return 

        self.game_paused = not self.game_paused
        
        if self.game_paused:
            # Show pause text, ensuring it uses the current scale/position
            self.canvas.delete("pause_text")
            self.start_text_id = self.canvas.create_text(
                self.canvas_width // 2, self.canvas_height // 2, 
                text="PAUSED", 
                fill="#FFFF00", font=self.get_scaled_font(28),
                tag="pause_text"
            )
        else:
            self.canvas.delete("pause_text")
            self.master.after(GAME_LOOP_DELAY, self.game_loop)
            
    def reposition_ui(self):
        """Repositions all static UI elements (score, pause, game over) based on the new canvas size."""
        # Update score text font
        self.canvas.itemconfigure(self.score_text, font=self.get_scaled_font(16))
        
        # Reposition pause text/start text if it exists
        if self.game_paused and self.game_running:
            pause_items = self.canvas.find_withtag("pause_text")
            if pause_items:
                self.canvas.coords(
                    pause_items[0], 
                    self.canvas_width // 2, 
                    self.canvas_height // 2
                )
                self.canvas.itemconfigure(pause_items[0], font=self.get_scaled_font(28))
        
        # If game over, redraw game over screen
        if not self.game_running:
            self.draw_game_over_screen()


    def get_player_coords(self, x, y):
        """Calculates the coordinates for the player's triangle shape using the scaled size."""
        # Use current calculated size
        size = self.current_player_size
        return [
            x, y - size,  # Top point
            x - size // 2, y + size // 2,  # Bottom-left
            x + size // 2, y + size // 2   # Bottom-right
        ]
        
    def reposition_player(self):
        """Updates player size and Y offset based on new canvas size."""
        self.current_player_size = int(PLAYER_SIZE_BASE * self.scale_factor)
        
        # Player Y position should be relative to the bottom
        self.player_y = self.canvas_height - (50 * self.scale_factor)
        
        # Boundary check and adjustment
        min_x = self.current_player_size // 2
        max_x = self.canvas_width - self.current_player_size // 2
        
        if self.player_x > max_x:
            self.player_x = max_x
        if self.player_x < min_x:
            self.player_x = min_x
            
        # Update the shape's coordinates immediately after resizing/repositioning
        if self.player_shape:
            self.canvas.coords(self.player_shape, self.get_player_coords(self.player_x, self.player_y))


    def set_player_velocity(self, speed):
        """Sets the player's horizontal movement speed."""
        self.player_vel_x = speed

    def stop_player_velocity(self, key):
        """Stops the player's movement only if the released key matches the current direction."""
        if (key == 'Left' and self.player_vel_x < 0) or \
           (key == 'Right' and self.player_vel_x > 0):
            self.player_vel_x = 0

    def move_player(self):
        """Updates the player's position based on velocity and boundary checks using current size."""
        if self.player_vel_x != 0:
            new_x = self.player_x + self.player_vel_x
            
            size = self.current_player_size
            # Keep player within the canvas bounds (using current/scaled size)
            min_x = size // 2
            max_x = self.canvas_width - size // 2
            
            if min_x < new_x < max_x:
                self.player_x = new_x
                self.canvas.coords(self.player_shape, self.get_player_coords(self.player_x, self.player_y))
            elif new_x <= min_x:
                self.player_x = min_x + 1 
                self.player_vel_x = 0
            elif new_x >= max_x:
                self.player_x = max_x - 1 
                self.player_vel_x = 0
    
    def spawn_enemies(self):
        """Spawns a new wave of enemy blocks, responsive to current canvas width and scale."""
        now = time.time() * 1000
        # Increase enemy speed over time for progressive difficulty
        self.enemy_speed = ENEMY_SPEED_INITIAL + self.score // 100 
        
        # Enemy block height also scales slightly
        scaled_enemy_height = int(ENEMY_HEIGHT_BASE * self.scale_factor)

        if now - self.last_spawn_time > ENEMY_SPAWN_INTERVAL / (1 + self.score / 500):
            num_blocks = random.randint(2, 5)  # 2 to 5 blocks per wave
            block_width = self.canvas_width // 10 # Uses current canvas width
            
            # Create a set of occupied horizontal slots
            occupied_slots = random.sample(range(10), k=num_blocks)

            for slot in occupied_slots:
                # Calculate coordinates for a block
                x1 = slot * block_width
                y1 = 0
                x2 = (slot + 1) * block_width
                y2 = scaled_enemy_height # Scaled block height
                
                # Create a rectangle enemy
                enemy_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2, 
                    fill="#FF4444", 
                    outline="#FF8888",
                    width=2
                )
                self.enemies.append(enemy_id)
            
            self.last_spawn_time = now

    def move_enemies(self):
        """Moves all existing enemies down the screen, using current canvas height for despawn check."""
        enemies_to_remove = []
        for enemy_id in self.enemies:
            # Move the enemy down by the current speed
            self.canvas.move(enemy_id, 0, self.enemy_speed)
            
            # Get current bounding box (x1, y1, x2, y2)
            coords = self.canvas.coords(enemy_id)
            if coords and coords[3] > self.canvas_height: # Uses current canvas height for despawn
                enemies_to_remove.append(enemy_id)
                self.score += 10 # Reward for dodging a block
                
                # INTERACTIVITY: Create score pop-up
                x = (coords[0] + coords[2]) // 2
                y = coords[3] - 15
                popup_id = self.canvas.create_text(
                    x, y, text="+10", fill="#00AAFF", 
                    font=self.get_scaled_font(12), anchor=tk.CENTER
                )
                self.score_popups.append((popup_id, 30)) # Store ID and countdown (30 frames)
        
        # Clean up enemies that went off-screen
        for enemy_id in enemies_to_remove:
            self.canvas.delete(enemy_id)
            self.enemies.remove(enemy_id)

    def update_score_popups(self):
        """Updates the position and visibility of score pop-up texts."""
        popups_to_remove = []
        for i, (text_id, countdown) in enumerate(self.score_popups):
            # Move text up (fade out effect)
            self.canvas.move(text_id, 0, -1)
            
            # Decrease countdown
            self.score_popups[i] = (text_id, countdown - 1)
            
            if countdown <= 0:
                self.canvas.delete(text_id)
                popups_to_remove.append(i)
        
        # Remove deleted popups from the list (in reverse order to avoid index issues)
        for index in sorted(popups_to_remove, reverse=True):
            del self.score_popups[index]

    def check_collisions(self):
        """Checks if the player has collided with any enemy."""
        # Get player bounding box (approximate for the triangle)
        player_bbox = self.canvas.bbox(self.player_shape)
        if not player_bbox: return False

        px1, py1, px2, py2 = player_bbox

        for enemy_id in self.enemies:
            enemy_bbox = self.canvas.bbox(enemy_id)
            if not enemy_bbox: continue

            ex1, ey1, ex2, ey2 = enemy_bbox

            # Simple AABB (Axis-Aligned Bounding Box) collision check
            x_overlap = max(px1, ex1) < min(px2, ex2)
            y_overlap = max(py1, ey1) < min(py2, ey2)

            if x_overlap and y_overlap:
                self.game_running = False
                return True
        return False

    def update_score(self):
        """Updates the score display."""
        # Display current score and high score with scaled font
        display_text = f"Score: {self.score} | High Score: {self.high_score}"
        self.canvas.itemconfigure(self.score_text, text=display_text, font=self.get_scaled_font(16))

    def game_over(self):
        """Handles game over state and draws the responsive game over screen."""
        self.unbind_controls()
        
        # Check and update High Score
        if self.score > self.high_score:
            self.high_score = self.score
            
        # Clear all floating score popups
        for text_id, _ in self.score_popups:
            self.canvas.delete(text_id)
        self.score_popups = []

        self.draw_game_over_screen()
        
        # Bind the Return/Enter key to the reset method
        self.master.bind('<Return>', lambda event: self.reset_game())
        
    def draw_game_over_screen(self):
        """Draws the game over UI using current dimensions and scale factor."""
        # Clear previous game over UI if it exists
        self.canvas.delete("game_over_ui") 
        
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        
        # Scaled box width and vertical offsets
        box_width = 150 * self.scale_factor
        
        # Game Over Box 
        self.canvas.create_rectangle(
            center_x - box_width, center_y - (50 * self.scale_factor),
            center_x + box_width, center_y + (105 * self.scale_factor), 
            fill="#333333", outline="#FFD700", width=3,
            tags="game_over_ui"
        )
        
        # Text elements, all using scaled fonts and positions
        self.canvas.create_text(
            center_x, center_y - (20 * self.scale_factor), 
            text="GAME OVER", fill="#FF4444", font=self.get_scaled_font(24),
            tags="game_over_ui"
        )
        self.canvas.create_text(
            center_x, center_y + (15 * self.scale_factor), 
            text=f"Final Score: {self.score}", fill="#FFFFFF", font=self.get_scaled_font(18),
            tags="game_over_ui"
        )
        
        is_new_high_score = (self.score == self.high_score and self.score > 0)
        high_score_color = "#00FFC0" if is_new_high_score else "#CCCCCC"
        high_score_label = "NEW HIGH SCORE!" if is_new_high_score else "High Score:"
        
        self.canvas.create_text(
            center_x, center_y + (50 * self.scale_factor), 
            text=f"{high_score_label} {self.high_score}", 
            fill=high_score_color, font=self.get_scaled_font(16),
            tags="game_over_ui"
        )
        
        # Retry Prompt
        self.canvas.create_text(
            center_x, center_y + (85 * self.scale_factor), 
            text="Press ENTER to Play Again", fill="#00FFC0", font=self.get_scaled_font(14),
            tags="game_over_ui"
        )


    def reset_game(self):
        """Resets all game state and restarts the game loop."""
        self.game_paused = False 
        self.init_game_objects()
        self.game_loop()

    def game_loop(self):
        """The main update loop for the game."""
        # Stop execution if game is over or paused, and wait for input
        if not self.game_running or self.game_paused:
            return 
            
        self.move_player()
        self.spawn_enemies()
        self.move_enemies()
        self.update_score_popups() 
        self.update_score()
        
        if self.check_collisions():
            self.game_over()
        else:
            # Schedule the next call to game_loop
            self.master.after(GAME_LOOP_DELAY, self.game_loop)

if __name__ == '__main__':
    root = tk.Tk()
    game = SpacewavesGame(root)
    root.mainloop()
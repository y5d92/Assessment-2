# I acknowledge the use of Gemini (version Flash 2.5, Google, https://gemini.google.com/)
# to co-create this code for the Spacewaves Defender game.

import tkinter as tk
import random
import time

# --- Game Constants ---
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 700
PLAYER_SIZE = 30
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
        master.resizable(False, False)
        
        # High Score persists across multiple games in the same session
        self.high_score = 0 
        
        # Setup Canvas (created once)
        self.canvas = tk.Canvas(master, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="#000022")
        self.canvas.pack(padx=10, pady=10)
        
        # Initialize all game objects and state
        self.game_paused = True # Game starts paused
        self.start_text_id = None
        
        self.init_game_objects()
        
        # Start the game loop which immediately hits the pause check
        self.game_loop()

    def init_game_objects(self):
        """Initializes or resets all game elements and state."""
        # Clear the canvas of all existing items (enemies, player, previous game over text)
        self.canvas.delete(tk.ALL)
        
        # Game State (High score is NOT reset here)
        self.game_running = True
        self.score = 0
        self.enemies = []
        self.enemy_speed = ENEMY_SPEED_INITIAL
        self.last_spawn_time = time.time() * 1000
        self.score_popups = [] # New list for temporary score texts

        # Player setup
        self.player_x = CANVAS_WIDTH // 2
        self.player_y = CANVAS_HEIGHT - 50
        self.player_vel_x = 0
        self.player_shape = self.canvas.create_polygon(
            self.get_player_coords(self.player_x, self.player_y),
            fill="#00FFC0", 
            outline="#00AA80"
        )

        # Score Label
        self.score_text = self.canvas.create_text(
            10, 10, anchor=tk.NW, text=f"Score: {self.score} | High Score: {self.high_score}", 
            fill="#FFFFFF", font=('Inter', 16, 'bold')
        )

        # Show initial 'Press SPACE to Start' screen
        if self.game_paused:
            self.start_text_id = self.canvas.create_text(
                CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2, 
                text="PRESS SPACE TO START", 
                fill="#00FFC0", font=('Inter', 28, 'bold'),
                tag="pause_text"
            )

        # Bind initial controls
        self.bind_controls()

    def bind_controls(self):
        """Binds the movement controls, pause key, and unbinds retry key."""
        self.master.bind('<Left>', lambda event: self.set_player_velocity(-PLAYER_SPEED))
        self.master.bind('<Right>', lambda event: self.set_player_velocity(PLAYER_SPEED))
        self.master.bind('<KeyRelease-Left>', lambda event: self.stop_player_velocity('Left'))
        self.master.bind('<KeyRelease-Right>', lambda event: self.stop_player_velocity('Right'))
        self.master.bind('<space>', self.toggle_pause) # New: Pause/Start binding
        
        # Ensure the retry key is unbound during active gameplay
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
            return # Don't pause if the game is over

        self.game_paused = not self.game_paused
        
        if self.game_paused:
            # Show pause text
            self.start_text_id = self.canvas.create_text(
                CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2, 
                text="PAUSED", 
                fill="#FFFF00", font=('Inter', 28, 'bold'),
                tag="pause_text"
            )
        else:
            # Remove pause text and resume loop immediately
            self.canvas.delete("pause_text")
            # Immediately call game_loop to resume animation
            self.master.after(GAME_LOOP_DELAY, self.game_loop)

    def get_player_coords(self, x, y):
        """Calculates the coordinates for the player's triangle shape."""
        # A simple upward-pointing triangle
        return [
            x, y - PLAYER_SIZE,  # Top point
            x - PLAYER_SIZE // 2, y + PLAYER_SIZE // 2,  # Bottom-left
            x + PLAYER_SIZE // 2, y + PLAYER_SIZE // 2   # Bottom-right
        ]

    def set_player_velocity(self, speed):
        """Sets the player's horizontal movement speed."""
        self.player_vel_x = speed

    def stop_player_velocity(self, key):
        """Stops the player's movement only if the released key matches the current direction."""
        if (key == 'Left' and self.player_vel_x < 0) or \
           (key == 'Right' and self.player_vel_x > 0):
            self.player_vel_x = 0

    def move_player(self):
        """Updates the player's position based on velocity and boundary checks."""
        if self.player_vel_x != 0:
            new_x = self.player_x + self.player_vel_x
            
            # Keep player within the canvas bounds
            min_x = PLAYER_SIZE // 2
            max_x = CANVAS_WIDTH - PLAYER_SIZE // 2
            
            if min_x < new_x < max_x:
                self.player_x = new_x
                # Update the shape's coordinates
                self.canvas.coords(self.player_shape, self.get_player_coords(self.player_x, self.player_y))
            elif new_x <= min_x:
                self.player_x = min_x + 1 # Bounce off slightly
                self.player_vel_x = 0
            elif new_x >= max_x:
                self.player_x = max_x - 1 # Bounce off slightly
                self.player_vel_x = 0
    
    def spawn_enemies(self):
        """Spawns a new wave of enemy blocks."""
        now = time.time() * 1000
        # Increase enemy speed over time for progressive difficulty
        self.enemy_speed = ENEMY_SPEED_INITIAL + self.score // 100 

        if now - self.last_spawn_time > ENEMY_SPAWN_INTERVAL / (1 + self.score / 500):
            num_blocks = random.randint(2, 5)  # 2 to 5 blocks per wave
            block_width = CANVAS_WIDTH // 10
            
            # Create a set of occupied horizontal slots
            occupied_slots = random.sample(range(10), k=num_blocks)

            for slot in occupied_slots:
                # Calculate coordinates for a block
                x1 = slot * block_width
                y1 = 0
                x2 = (slot + 1) * block_width
                y2 = 30 # Enemy block height
                
                # Create a rectangle enemy
                enemy_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2, 
                    fill="#FF4444", 
                    outline="#FF8888",
                    width=2
                )
                # Store the enemy ID and its bounding box coords
                self.enemies.append(enemy_id)
            
            self.last_spawn_time = now

    def move_enemies(self):
        """Moves all existing enemies down the screen."""
        enemies_to_remove = []
        for enemy_id in self.enemies:
            # Move the enemy down by the current speed
            self.canvas.move(enemy_id, 0, self.enemy_speed)
            
            # Get current bounding box (x1, y1, x2, y2)
            coords = self.canvas.coords(enemy_id)
            if coords and coords[3] > CANVAS_HEIGHT:
                enemies_to_remove.append(enemy_id)
                self.score += 10 # Reward for dodging a block
                
                # INTERACTIVITY: Create score pop-up
                x = (coords[0] + coords[2]) // 2
                y = coords[3] - 15
                popup_id = self.canvas.create_text(
                    x, y, text="+10", fill="#00AAFF", 
                    font=('Inter', 12, 'bold'), anchor=tk.CENTER
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
        # Display current score and high score
        display_text = f"Score: {self.score} | High Score: {self.high_score}"
        self.canvas.itemconfigure(self.score_text, text=display_text)

    def game_over(self):
        """Displays the Game Over screen and a retry option, including High Score logic."""
        # Unbind movement and pause controls
        self.unbind_controls()
        
        # Check and update High Score
        is_new_high_score = False
        if self.score > self.high_score:
            self.high_score = self.score
            is_new_high_score = True
            
        # Clear all floating score popups
        for text_id, _ in self.score_popups:
            self.canvas.delete(text_id)
        self.score_popups = []

        # Game Over Box 
        self.canvas.create_rectangle(
            CANVAS_WIDTH // 2 - 150, CANVAS_HEIGHT // 2 - 50,
            CANVAS_WIDTH // 2 + 150, CANVAS_HEIGHT // 2 + 105, 
            fill="#333333", outline="#FFD700", width=3
        )
        self.canvas.create_text(
            CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2 - 20, 
            text="GAME OVER", fill="#FF4444", font=('Inter', 24, 'bold')
        )
        self.canvas.create_text(
            CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2 + 15, 
            text=f"Final Score: {self.score}", fill="#FFFFFF", font=('Inter', 18)
        )
        
        # Display High Score on Game Over screen
        high_score_color = "#00FFC0" if is_new_high_score else "#CCCCCC"
        high_score_label = "NEW HIGH SCORE!" if is_new_high_score else "High Score:"
        
        self.canvas.create_text(
            CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2 + 50, 
            text=f"{high_score_label} {self.high_score}", 
            fill=high_score_color, font=('Inter', 16, 'bold')
        )
        
        # Retry Prompt
        self.canvas.create_text(
            CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2 + 85, 
            text="Press ENTER to Play Again", fill="#00FFC0", font=('Inter', 14, 'bold')
        )
        
        # Bind the Return/Enter key to the reset method
        self.master.bind('<Return>', lambda event: self.reset_game())

    def reset_game(self):
        """Resets all game state and restarts the game loop."""
        self.game_paused = False # Start game immediately after reset
        self.init_game_objects()
        # The game_loop will now continue since self.game_running is True and self.game_paused is False
        self.game_loop()

    def game_loop(self):
        """The main update loop for the game."""
        # Stop execution if game is over or paused, and wait for input
        if not self.game_running or self.game_paused:
            return 
            
        self.move_player()
        self.spawn_enemies()
        self.move_enemies()
        self.update_score_popups() # New: Update and move score popups
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
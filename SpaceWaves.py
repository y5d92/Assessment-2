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
        
        # Game State
        self.game_running = True
        self.score = 0
        self.enemies = []
        self.enemy_speed = ENEMY_SPEED_INITIAL
        self.last_spawn_time = time.time() * 1000

        # Setup Canvas
        self.canvas = tk.Canvas(master, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="#000022")
        self.canvas.pack(padx=10, pady=10)

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
            10, 10, anchor=tk.NW, text=f"Score: {self.score}", 
            fill="#FFFFFF", font=('Inter', 16, 'bold')
        )

        # Bind controls
        master.bind('<Left>', lambda event: self.set_player_velocity(-PLAYER_SPEED))
        master.bind('<Right>', lambda event: self.set_player_velocity(PLAYER_SPEED))
        master.bind('<KeyRelease-Left>', lambda event: self.stop_player_velocity('Left'))
        master.bind('<KeyRelease-Right>', lambda event: self.stop_player_velocity('Right'))

        # Start the game loop
        self.game_loop()

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
        
        # Clean up enemies that went off-screen
        for enemy_id in enemies_to_remove:
            self.canvas.delete(enemy_id)
            self.enemies.remove(enemy_id)

    def check_collisions(self):
        """Checks if the player has collided with any enemy."""
        # Get player bounding box (approximate for the triangle)
        # Use the bottom-most coordinate for collision calculation
        player_bbox = self.canvas.bbox(self.player_shape)
        if not player_bbox: return False

        px1, py1, px2, py2 = player_bbox

        for enemy_id in self.enemies:
            enemy_bbox = self.canvas.bbox(enemy_id)
            if not enemy_bbox: continue

            ex1, ey1, ex2, ey2 = enemy_bbox

            # Simple AABB (Axis-Aligned Bounding Box) collision check
            # Check for overlap in X and Y axes
            x_overlap = max(px1, ex1) < min(px2, ex2)
            y_overlap = max(py1, ey1) < min(py2, ey2)

            if x_overlap and y_overlap:
                self.game_running = False
                return True
        return False

    def update_score(self):
        """Updates the score display."""
        self.canvas.itemconfigure(self.score_text, text=f"Score: {self.score}")

    def game_over(self):
        """Displays the Game Over screen."""
        self.canvas.create_rectangle(
            CANVAS_WIDTH // 2 - 150, CANVAS_HEIGHT // 2 - 50,
            CANVAS_WIDTH // 2 + 150, CANVAS_HEIGHT // 2 + 50,
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
        
        # Unbind controls to stop input
        self.master.unbind('<Left>')
        self.master.unbind('<Right>')
        self.master.unbind('<KeyRelease-Left>')
        self.master.unbind('<KeyRelease-Right>')

    def game_loop(self):
        """The main update loop for the game."""
        if self.game_running:
            self.move_player()
            self.spawn_enemies()
            self.move_enemies()
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
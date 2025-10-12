from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen
import random

class SnakeGameOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Make it a child widget that fills the parent
        self.setParent(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Game constants
        self.cell_size = 48  # Diameter of each segment
        self.snake_radius = 22
        self.speed = 150  # milliseconds per move
        
        # Colors
        self.snake_color = QColor(70, 70, 70, 200)
        self.apple_color = QColor(150, 150, 150, 200)
        
        # Game state variables (initialized but not set up yet)
        self.snake = []
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.apple = (0, 0)
        self.game_over = False
        self.score = 0
        self.grid_width = 0
        self.grid_height = 0
        
        # Timer for game loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        
    def reset_game(self):
        """Initialize/reset game state"""
        # Calculate grid dimensions
        self.grid_width = self.width() // self.cell_size
        self.grid_height = self.height() // self.cell_size
        
        # Snake starts in the middle
        start_x = self.grid_width // 2
        start_y = self.grid_height // 2
        self.snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        
        # Initial direction (moving right)
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        
        # Spawn first apple
        self.apple = self.spawn_apple()
        
        # Game state
        self.game_over = False
        self.score = 0
        
    def spawn_apple(self):
        """Spawn apple at random position not occupied by snake"""
        # Ensure grid has valid dimensions
        if self.grid_width <= 0 or self.grid_height <= 0:
            return (0, 0)
            
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if (x, y) not in self.snake:
                return (x, y)
    
    def start_game(self):
        """Start the game"""
        if self.parent():
            # Fill the entire parent widget
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
            self.raise_()  # Bring to front
        
        # Now that widget is sized, initialize the game
        self.reset_game()
        self.timer.start(self.speed)
        self.show()
        self.setFocus()
        
    def game_loop(self):
        """Main game loop called by timer"""
        if self.game_over:
            return
            
        # Update direction
        self.direction = self.next_direction
        
        # Calculate new head position
        head_x, head_y = self.snake[0]
        new_head = (
            (head_x + self.direction[0]) % self.grid_width,
            (head_y + self.direction[1]) % self.grid_height
        )
        
        # Check self collision
        if new_head in self.snake:
            self.game_over = True
            self.timer.stop()
            self.close()
            return
        
        # Move snake
        self.snake.insert(0, new_head)
        
        # Check apple collision
        if new_head == self.apple:
            self.score += 1
            self.apple = self.spawn_apple()
            # Speed up slightly
            if self.speed > 50:
                self.speed = max(50, self.speed - 2)
                self.timer.setInterval(self.speed)
        else:
            # Remove tail if no apple eaten
            self.snake.pop()
        
        self.update()
    
    def keyPressEvent(self, event):
        """Handle keyboard input"""
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            self.timer.stop()
            self.close()
            return
        
        # Prevent 180-degree turns
        dx, dy = self.direction
        
        if key == Qt.Key.Key_Up and dy == 0:
            self.next_direction = (0, -1)
        elif key == Qt.Key.Key_Down and dy == 0:
            self.next_direction = (0, 1)
        elif key == Qt.Key.Key_Left and dx == 0:
            self.next_direction = (-1, 0)
        elif key == Qt.Key.Key_Right and dx == 0:
            self.next_direction = (1, 0)
    
    def paintEvent(self, event):
        """Draw the game"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw snake
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.snake_color)
        
        for i, segment in enumerate(self.snake):
            x = segment[0] * self.cell_size + self.snake_radius
            y = segment[1] * self.cell_size + self.snake_radius
            painter.drawEllipse(QPointF(x, y), self.snake_radius, self.snake_radius)
            
            # Draw "A" on snake head
            if i == 0:
                painter.setPen(QColor(255, 255, 255, 180))
                font = painter.font()
                font.setPointSize(16)
                font.setBold(True)
                painter.setFont(font)
                
                # Get text metrics for centering
                metrics = painter.fontMetrics()
                text_width = metrics.horizontalAdvance("A")
                text_height = metrics.height()
                
                # Center the text
                text_x = x - text_width / 2
                text_y = y + text_height / 4
                
                painter.drawText(int(text_x), int(text_y), "A")
                painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw apple
        painter.setBrush(self.apple_color)
        apple_x = self.apple[0] * self.cell_size + self.snake_radius
        apple_y = self.apple[1] * self.cell_size + self.snake_radius
        painter.drawEllipse(QPointF(apple_x, apple_y), self.snake_radius, self.snake_radius)
        
        # Draw "B" on apple
        painter.setPen(QColor(255, 255, 255, 180))
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance("B")
        text_height = metrics.height()
        
        text_x = apple_x - text_width / 2
        text_y = apple_y + text_height / 4
        
        painter.drawText(int(text_x), int(text_y), "B")
        
        # Draw score
        painter.setPen(QPen(QColor(200, 200, 200, 180), 2))
        painter.drawText(10, 30, f"Score: {self.score}")
        
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        if self.timer.isActive():
            # Recalculate grid if window is resized during game
            self.grid_width = self.width() // self.cell_size
            self.grid_height = self.height() // self.cell_size


# Modify your BBL_GAME function to launch the game:
from theme.fonts import font_icons as ic

BBL_GAME_CONFIG = {"symbol": ic.ICON_SPEED_SNAIL}
def BBL_GAME(self, position):
    print("start")
    # Create and start the snake game overlay
    if not hasattr(self, 'snake_game'):
        self.snake_game = SnakeGameOverlay(self)
    self.snake_game.start_game()
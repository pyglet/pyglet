import pyglet

from game import util, load

# Set up a window
game_window = pyglet.window.Window(800, 600)

# Set up the two top labels
score_label = pyglet.text.Label(text="Score: 0", x=10, y=575)
level_label = pyglet.text.Label(text="Version 1: Static Graphics",
                                x=400, y=575, anchor_x='center')

# Initialize the player sprite
player_ship = pyglet.sprite.Sprite(img=util.load_centered('player.png'), x=400, y=300)

# Make three asteroids so we have something to shoot at
asteroids = load.asteroids(num_asteroids=3, player_position=player_ship.position)


@game_window.event
def on_draw():
    game_window.clear()

    player_ship.draw()
    for asteroid in asteroids:
        asteroid.draw()

    level_label.draw()
    score_label.draw()


if __name__ == "__main__":
    # Enter into the event loop:
    pyglet.app.run()

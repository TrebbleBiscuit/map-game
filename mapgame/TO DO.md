# TO DO

- refactor game so that it can sit idle and you progress by issuing commands as arguments to a function

game state is stored by state variables instead of where you are in the big block of code or smth idk


when you play():
get an inital command for `map` or `portal`
- `portal` calls portal_into_another_dimension()
- `map` tries map_turn(command) until it returns True

having a look at map_turn():
- you move a direction
    - move there, print flavor text, progress time, done
- or do a room-specific action
    - only available under some conditions
- or debug commands


What are our constraints?
- updating the screen necessitates calling gui methods
- can't wait for user input, have to instead wait for on_input_submitted()
- or can we??
    Perhaps we could manually wait for user input by checking what exists in the input field?
    Can grab what the user has typed with `OutputWindow.render()`
    Buut idk how to tell when they hit enter
    so no i think not

So, we need to store the game state and have one method that gets called over and over again to "progress"


Things that currently get input
- combat()
- map_turn()
- play()

let's totally axe combat for now.
play() decides between `portal` and `map` but `portal` is more of a debug command anyway
that leaves map_turn()

As a temporary measure let's do this
- wire `GUIWrapper.on_input_submitted()` into `Game.map_turn()`
- sanitize its input a bit first


OKAY NOW THAT WE'VE CLEARED ALL THAT UP TIME FOR THE GRAND MASTER LIST OF TASKS FOR RIGHT NOW

- [x] wire `GUIWrapper.on_input_submitted()` into `Game.map_turn()`
- [x] replace all WindowManager references with GUIWrapper elements
- [x] make input field clear after submitting
- [x] replace `print_stdscr(` with `self.gui.main_out.add_line(`
- [x] wire the whole map up
- [x] add turn_prompt()
- [x] fix bug where dimension 1 (the second one) is deja vu

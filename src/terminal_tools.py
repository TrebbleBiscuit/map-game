import curses
import logging

logger = logging.getLogger(__name__)

MAP_WIN_LEN = 40

class WindowManager:
    def __init__(self, stdscr):
        self._stdscr = stdscr
        logger.info(f"stdscr class: {self._stdscr.__class__}")
        logger.info(f"type: {type(stdscr)}")
        self.height, self.width = self._stdscr.getmaxyx()
        logger.debug(f"Height, width: {(self.height, self.width)}")
        # First make a slightly larger window just to put a border around it
        b_stdscr = curses.newwin(15, self.width - MAP_WIN_LEN, 0, 0)
        b_stdscr.border()
        b_stdscr.refresh()
        # Standard screen
        stdscr = curses.newwin(13, self.width - MAP_WIN_LEN - 2, 1, 1)
        # stdscr.addstr(1, 1, "Normal ol' output goes here")
        # stdscr.border()
        stdscr.refresh()
        # stdscr.getch()
        stdscr.scrollok(True)
        stdscr.idlok(True)
        self.stdscr = stdscr
        logger.info(f"window class: {self.stdscr.__class__}")

        # Map
        b_mapscr = curses.newwin(15, MAP_WIN_LEN, 0, self.width - MAP_WIN_LEN)
        b_mapscr.border()
        b_mapscr.refresh()
        mapscr = curses.newwin(13, MAP_WIN_LEN-2, 1, self.width - MAP_WIN_LEN+1)
        # mapscr.addstr(1, 1, "Map goes here")
        # mapscr.border()
        mapscr.refresh()
        # mapscr.getch()
        self.mapscr = mapscr

        # Input screen
        b_input_scr = curses.newwin(7, self.width, self.height-7, 0)
        b_input_scr.border()
        b_input_scr.refresh()
        input_scr = curses.newwin(5, self.width-2, self.height-6, 1)
        # input_scr.addstr(1, 1, "Hello, world!")
        # input_scr.border()
        input_scr.scrollok(True)
        input_scr.idlok(True)
        input_scr.refresh()
        # input_scr.getch()
        self.input_scr = input_scr
    
    @staticmethod
    def printline(screen, to_print):
        screen.addstr(to_print)
        WindowManager.newline(screen)
    
    @staticmethod
    def newline(screen):
        y, x = screen.getyx()
        try:
            screen.move(y+1, 0)
        except:
            logger.exception(f"y is {y}")
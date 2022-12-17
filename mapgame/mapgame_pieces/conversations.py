import random


class Conversation:
    def __init__(self, player):
        self.player = player
        self.gui = player.gui
        self.can_leave = False

    def exit_conversation(self):
        if not self.can_leave:
            self.gui.main_out.add_line("You are not allowed to leave!")
        else:
            self.gui.main_out.add_line("Not sure how to exit a conversation yet")

    def prompt(self):
        ...

    def respond(self):
        ...


class TestConversation(Conversation):
    def __init__(self, player):
        super().__init__(player)
        self.stage = 0

    def prompt(self):
        if self.stage == 0:
            self.gui.main_out.add_line("Just say something!")
        elif self.stage == 1:
            self.gui.main_out.add_line("Thanks for saying something!")
        else:
            self.gui.main_out.add_line("Yeah we get it.")

    def respond(self, to_say: str):
        if self.stage == 0:
            if to_say:
                self.gui.main_out.add_line("You said it!")
                self.stage += 1
            else:
                self.gui.main_out.add_line("Well, go on, say something!")
        elif self.stage == 1:
            resp = random.choice(
                ["Uh-huh...", "I see...", "Wow...", "Cool...", "Neat..."]
            )
            self.gui.main_out.add_line(resp)

    def exit_conversation(self):
        self.gui.main_out.add_line("Not sure how to exit a conversation yet")


class RiddleConvo(Conversation):
    def __init__(self, player):
        super().__init__(player)
        self.answered = False
        self.answered_correctly = False
        self.correct_answer = "cat"

    def prompt(self):
        RIDDLE_TXT = "What has four paws and rhymes with 'rat'?"
        if not self.answered:
            self.gui.main_out.add_line(RIDDLE_TXT)
        elif self.answered_correctly:
            self.gui.main_out.add_line("Thanks for answering my riddle!")
        else:
            self.gui.main_out.add_line(f"Try my riddle again! {RIDDLE_TXT}")

    def respond(self, to_say: str):
        if not to_say:
            return
        if to_say == self.correct_answer:
            self.gui.main_out.add_line("You got my riddle right!")
            self.answered_correctly = True
        else:
            self.gui.main_out.add_line("That's not the right answer!")

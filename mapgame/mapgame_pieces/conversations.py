import random


class Conversation:
    def __init__(self, player):
        self.player = player
        self.gui = player.gui
        self.can_leave = True
        self.has_ended = False

    def exit_conversation(self):
        if not self.can_leave:
            self.gui.main_out.add_line("You can't leave this conversation yet!")
        else:
            self.has_ended = True

    def prompt(self):
        ...

    def quote_to_out(self, quote: str):
        """Wrap in quotes and print to main_out"""
        quote = f'"{quote}"'
        self.gui.main_out.add_line(quote)

    def respond(self):
        ...


class TestConversation(Conversation):
    def __init__(self, player):
        super().__init__(player)
        self.stage = 0

    def prompt(self):
        if self.stage == 0:
            self.quote_to_out("Just say something!")
        elif self.stage == 1:
            self.quote_to_out("Thanks for saying something!")
        else:
            self.quote_to_out("Yeah we get it.")

    def respond(self, to_say: str):
        if self.stage == 0:
            if to_say:
                self.quote_to_out("You said it!")
                self.stage += 1
            else:
                self.quote_to_out("Well, go on, say something!")
        elif self.stage == 1:
            resp = random.choice(
                ["Uh-huh...", "I see...", "Wow...", "Cool...", "Neat..."]
            )
            self.quote_to_out(resp)
        else:
            self.quote_to_out("aight imma head out")
            self.exit_conversation = True


class RiddleConvo(Conversation):
    def __init__(self, player):
        super().__init__(player)
        self.can_leave = False
        self.answered = False
        self.answered_correctly = False
        self.riddle_text = "What has four paws and rhymes with 'rat'?"
        self.correct_answer = "cat"

    def prompt(self):
        if not self.answered:
            self.quote_to_out(
                f"Ho ho ho, traveler! I won't let you through until you answer my riddle! {self.riddle_text}"
            )
        elif self.answered_correctly:
            self.quote_to_out("Thanks for answering my riddle!")
        else:
            self.quote_to_out(f"Try my riddle again! {self.riddle_text}")

    def respond(self, to_say: str):
        if not to_say:
            return
        self.answered = True
        if to_say == self.correct_answer:
            self.quote_to_out("You got my riddle right!")
            self.gui.main_out.add_line("They step aside to let you pass.")
            self.answered_correctly = True
            self.can_leave = True
            self.exit_conversation()
        elif self.answered_correctly:
            self.quote_to_out("No no, you had it before!")
        else:
            self.quote_to_out("That's not the right answer!")

import random

LEAVE_OPTIONS = ["leave", "exit"]


class Conversation:
    def __init__(self, npc):
        self.npc = npc
        self.can_leave = True
        self.has_ended = False

    def exit_conversation(self) -> bool:
        if not self.can_leave:
            return False
        else:
            self.has_ended = True
            return True

    def prompt(self) -> str:
        ...

    def wrap_in_quotes(self, quote: str) -> str:
        """Wrap in quotes and print to main_out"""
        return f'"{quote}"'

    def respond(self, player: "Player", to_say: str) -> str:
        ...


class TestConversation(Conversation):
    def __init__(self, npc):
        super().__init__(npc)
        self.stage = 0

    def prompt(self) -> str:
        if self.stage == 0:
            return self.wrap_in_quotes("Just say something!")
        elif self.stage == 1:
            return ""
        elif self.stage == 2:
            return self.wrap_in_quotes("Thanks for saying something!")
        else:
            return self.wrap_in_quotes("Yeah I get it.")

    def respond(self, player: "Player", to_say: str) -> str:
        if to_say in LEAVE_OPTIONS:
            if self.exit_conversation():
                return self.wrap_in_quotes("Hey, where are you going?")
            else:
                return "You can't leave this conversation yet!"
        if self.stage == 0:
            if to_say:
                self.stage += 1
                player.grant_xp(10)
                return self.wrap_in_quotes("You said it!")
            else:
                return self.wrap_in_quotes("Well, go on, say something!")
        elif self.stage < 3:
            if to_say:
                self.stage += 1
                resp = random.choice(
                    ["Uh-huh...", "I see...", "Wow...", "Cool...", "Neat..."]
                )
                return self.wrap_in_quotes(resp)
            else:
                return self.wrap_in_quotes("...")
        else:
            self.exit_conversation()
            return self.wrap_in_quotes("Alright I've heard enough.")


class RiddleConvo(Conversation):
    def __init__(self, npc, riddle_text: str, correct_answers: set[str]):
        super().__init__(npc)
        self.can_leave = False
        self.answered = False
        self.answered_correctly = False
        self.riddle_text = riddle_text
        self.correct_answers = correct_answers
        self.guess_number = 0

    def prompt(self) -> str:
        if not self.answered:
            return self.wrap_in_quotes(
                f"Ho ho ho, traveler! I won't let you through until you answer my riddle! {self.riddle_text}"
            )
        elif self.answered_correctly:
            return self.wrap_in_quotes("Thanks for answering my riddle!")
        else:
            return self.wrap_in_quotes(f"Try my riddle again! {self.riddle_text}")

    def respond(self, player: "Player", to_say: str) -> str:
        if not to_say:
            return ""
        elif to_say in LEAVE_OPTIONS:
            self.exit_conversation()
            return self.wrap_in_quotes("Goodbye then!")
        self.answered = True
        self.guess_number += 1
        if to_say in self.correct_answers:
            if not self.answered_correctly:
                xp_amount = max(16 - (2 * self.guess_number), 6)
                player.grant_xp(xp_amount)
            self.answered_correctly = True
            self.can_leave = True
            self.exit_conversation()
            quote = f"You got my riddle right on the {self.number_suffix(self.guess_number)} guess!"
            return (
                self.wrap_in_quotes(quote)
                + "\n"
                + f"The {self.npc.name} steps aside to let you pass."
            )
        elif self.answered_correctly:
            return self.wrap_in_quotes("No no, you had it before!")
        else:
            return self.wrap_in_quotes("That's not the right answer!")

    @staticmethod
    def number_suffix(num: int):
        if num % 10 == 1 and num % 100 != 11:
            return f"{num}st"
        elif num % 10 == 2 and num % 100 != 12:
            return f"{num}nd"
        elif num % 10 == 3 and num % 100 != 13:
            return f"{num}rd"
        else:
            return f"{num}th"

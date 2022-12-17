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
    def __init__(self, npc):
        super().__init__(npc)
        self.can_leave = False
        self.answered = False
        self.answered_correctly = False
        self.riddle_text = "What has four paws and rhymes with 'rat'?"
        self.correct_answer = "cat"

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
        self.answered = True
        if to_say == self.correct_answer:
            if not self.answered_correctly:
                player.grant_xp(15)
            self.answered_correctly = True
            self.can_leave = True
            self.exit_conversation()
            return (
                self.wrap_in_quotes("You got my riddle right!")
                + "\n"
                + f"The {self.npc.name} steps aside to let you pass."
            )
        elif to_say in LEAVE_OPTIONS:
            self.exit_conversation()
            return self.wrap_in_quotes("Goodbye then!")
        elif self.answered_correctly:
            return self.wrap_in_quotes("No no, you had it before!")
        else:
            return self.wrap_in_quotes("That's not the right answer!")

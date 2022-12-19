import random
import logging

logger = logging.getLogger(__name__)
LEAVE_OPTIONS = ["leave", "exit", "l"]


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


class NoConversation(Conversation):
    def __init(self, npc):
        super().__init__(npc)
        self.has_ended = True


class WisdomConvo(Conversation):
    def __init__(self, npc, custom_wisdom: str = ""):
        super().__init__(npc)
        self.given_wisdom = 0
        self.custom_wisdom = custom_wisdom
        self.can_leave = False

    def prompt(self) -> str:
        if self.given_wisdom == 0:
            return self.wrap_in_quotes(
                "Behold, adventurer! I am here to bestow upon you wisdom."
            )
        else:
            return self.wrap_in_quotes("Be careful out there!")

    def respond(self, player: "Player", to_say: str) -> str:
        if to_say in LEAVE_OPTIONS or self.given_wisdom:
            if self.exit_conversation():
                return self.wrap_in_quotes("Good luck on your journey.")
            else:
                return self.wrap_in_quotes("Wait, let me bestow my wisdom first!")

        self.given_wisdom += 1
        self.can_leave = True
        self.exit_conversation()

        if self.custom_wisdom:
            return self.wrap_in_quotes(self.custom_wisdom)

        possible_wisdom = ["xp"]
        if player.humanity < 85:
            possible_wisdom.append("humanity")
        if not player.abilities.passive_heal_double:
            possible_wisdom.append("passive_heal_double")
        if not player.abilities.reduced_humanity_loss:
            possible_wisdom.append("reduced_humanity_loss")

        out_msg = f"The {self.npc.name}'s wisdom "
        match random.choice(possible_wisdom):
            case "xp":
                player.grant_xp(player.level * 4 + 10)
                return out_msg + "gives you a sense of experience!"
            case "humanity":
                player.humanity += 15
                return out_msg + "makes you feel more clearheaded!"
            case "passive_heal_double":
                player.grant_ability("passive_heal_double")
                return out_msg + "teaches you to passively heal twice as fast!! Wow!"
            case "reduced_humanity_loss":
                player.grant_ability("reduced_humanity_loss")
                return out_msg + "teaches you to reduce your humanity losses!! Wow!"
            case _ as another:
                logger.error(
                    f"{self.npc.name} attempted to bestow the following unhandled wisdom type: {another}"
                )
                return f"{another} shouldnt be in possible wisdom rip PLS REPORT THIS"


class BuffConvo(Conversation):
    def __init__(self, npc):
        super().__init__(npc)
        self.given_buff = 0

    def prompt(self) -> str:
        if self.given_buff == 0:
            return self.wrap_in_quotes(
                "Hello, traveler! You look like you could use a hand."
            )
        else:
            return self.wrap_in_quotes("That should help you out. Good luck out there.")

    def respond(self, player: "Player", to_say: str) -> str:
        if to_say in LEAVE_OPTIONS or self.given_buff:
            if self.exit_conversation():
                if to_say in THANKS:
                    bye = "Happy to be of service! Be safe!"
                else:
                    bye = "Be safe!"
                return self.wrap_in_quotes(bye)
            else:
                return self.wrap_in_quotes(
                    "Wait, don't leave just yet! I've got something for you."
                )

        self.given_buff += 1
        self.can_leave = True

        possible_buffs = ["bless_res"]
        if player.humanity < 85:
            possible_buffs.append("humanity")
        elif player.max_hp - player.hp > 20:
            possible_buffs.append("heal")

        out_msg = f"The {self.npc.name} chants in a low voice in a strange language. "
        match random.choice(possible_buffs):
            case "bless_res":
                player.flags.blessed_revive += 1
                return (
                    out_msg
                    + "You feel a surge of confidence, like someone is looking out for you!"
                )
            case "humanity":
                # TODO
                player.humanity += 15
                return out_msg + "Your mind suddenly clears and you feel more focused!"
            case "heal":
                player.hp += 20
                return (
                    out_msg
                    + "Some of your wounds miraculously stitch themselves together!"
                )
            case _ as another:
                logger.error(
                    f"{self.npc.name} attempted to bestow the following unhandled buff: {another}"
                )
                return f"{another} shouldnt be in possible buffs rip PLS REPORT THIS"


class IntroConvo(Conversation):
    def __init__(self, npc):
        super().__init__(npc)
        self.stage = 0

    def prompt(self) -> str:
        if self.stage == 0:
            return self.wrap_in_quotes(
                "Hey, you! Glad to see a friendly face around here."
            )
        elif self.stage == 1:
            return self.wrap_in_quotes(
                "I woke up here one day - I'm trying to escape and get back home."
            )
        elif self.stage == 2:
            return self.wrap_in_quotes(
                "The only way out is through a portal to the east, but it only seems to lead deeper..."
            )
        elif self.stage == 3:
            return self.wrap_in_quotes(
                "Let me know if you find another way out, will you?"
            )
        elif self.stage == 4:
            return self.wrap_in_quotes(
                "Oh, just so you know, you can type `leave` or `exit` to prematurely end most conversations."
            )
        elif self.stage == 5:
            return self.wrap_in_quotes("Anyway, take care!")

    def respond(self, player: "Player", to_say: str) -> str:
        if to_say in LEAVE_OPTIONS:
            if self.exit_conversation():
                return self.wrap_in_quotes("Be safe out there.")
        if self.stage < 5:
            self.stage += 1
        else:
            self.exit_conversation()
            return self.wrap_in_quotes("Be safe out there.")
        return ""


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

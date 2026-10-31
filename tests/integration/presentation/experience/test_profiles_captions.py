"""Profile actions never mutate the running policy; captions never expose unheard actions."""

from dataclasses import replace

import pygame

from echo_heist.core.contracts.autonomy.policy import Navigation, PolicySelection
from echo_heist.core.contracts.environment.presentation import EnvironmentCue, EnvironmentCueKind
from echo_heist.core.contracts.events import EventKind, GameEvent, HeardCue
from echo_heist.ui.presenters.captions import CaptionStream
from echo_heist.ui.scenes.experience.profiles import PROFILE_ACTIONS, ProfilePanel
from echo_heist.ui.scenes.flow import GameFlow
from tests.fixtures.experience.gateway import MemoryGateway


def key(code: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=code)


def test_save_load_delete_confirmation_and_failure_keep_the_draft_safe() -> None:
    pygame.font.init()
    gateway = MemoryGateway()
    panel = ProfilePanel(gateway)
    panel.show()
    chosen = PolicySelection(navigation=Navigation.SAFEST)
    panel.handle(
        [
            key(pygame.K_n),
            pygame.event.Event(pygame.TEXTINPUT, text="Stealth"),
            key(pygame.K_RETURN),
            key(pygame.K_s),
        ],
        chosen,
    )
    assert gateway.saved[-1].policy == chosen
    panel.selected = 1
    assert panel.handle([key(pygame.K_l)], PolicySelection()) == chosen
    panel.handle([key(pygame.K_DELETE), key(pygame.K_ESCAPE)], chosen)
    assert len(gateway.saved) == 2
    panel.handle([key(pygame.K_DELETE), key(pygame.K_RETURN)], chosen)
    assert len(gateway.saved) == 1
    gateway.fail = True
    panel.name = "Retry"
    panel.handle([key(pygame.K_s)], chosen)
    assert "unavailable" in panel.notice and panel.name == "Retry"
    assert (
        panel.handle(
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=PROFILE_ACTIONS[-1].center)],
            chosen,
        )
        is None
    )
    assert not panel.open


def test_default_profile_browser_is_honest_and_does_not_save_anything() -> None:
    pygame.font.init()
    panel = ProfilePanel(None)
    panel.show()
    assert not panel.profiles and "unavailable" in panel.notice
    panel.name = "Example"
    panel.handle([key(pygame.K_s)], PolicySelection())
    assert not panel.profiles


def test_captions_require_legitimate_hearing_and_deduplicate_without_extending_lifetime() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720), security_enabled=False)
    flow._start_run()
    assert flow.session
    observation = replace(flow.session.simulation.observe(flow.session.observer_id), tick=20)
    hidden = EnvironmentCue(
        "break", 20, EnvironmentCueKind.GLASS, "glass", (0, 0), "foreign", "sound", True
    )
    captions = CaptionStream(30)
    captions.observe(observation, (), (hidden,))
    assert captions.at(observation) == ""
    heard = replace(observation, heard_events=(HeardCue("sound", "GLASS", (1, 1), 20),))
    captions.observe(heard, (), (hidden,))
    assert captions.at(heard) == "[Glass breaks]"
    captions.observe(replace(heard, tick=40), (), (hidden,))
    assert captions.until == 80
    assert captions.at(replace(heard, tick=81)) == ""
    own = GameEvent("own-tool", 82, EventKind.TOOL_USED, observation.agent_id, (("tool", "EMP"),))
    captions.observe(replace(heard, tick=82), (own,), ())
    assert captions.at(replace(heard, tick=82)) == "[EMP burst]"
    for i in range(400):
        captions.observe(
            replace(heard, tick=100 + i), (replace(own, event_id=str(i), tick=100 + i),), ()
        )
    assert len(captions.seen) == 256

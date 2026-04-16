"""Transition Effects Library for ClipForge.

Professional video transitions:
- Fade, dissolve, slide
- Speed ramps
- 3D transitions
- Motion blur
- Custom easing
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """Transition effect types."""

    FADE = "fade"
    DISSOLVE = "dissolve"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    BLUR = "blur"
    MOSAIC = "mosaic"


class EasingType(Enum):
    """Easing curve types."""

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


@dataclass
class TransitionConfig:
    """Transition effect configuration."""

    transition_type: TransitionType
    duration_sec: float  # 0.3 to 2.0 seconds
    easing: EasingType = EasingType.EASE_IN_OUT
    intensity: float = 1.0  # 0.0 to 2.0
    color: tuple[int, int, int] = (0, 0, 0)  # RGB for fade/wipe


class EasingCurve:
    """Easing curve calculations."""

    @staticmethod
    def linear(t: float) -> float:
        """Linear easing: no acceleration."""
        return t

    @staticmethod
    def ease_in(t: float) -> float:
        """Accelerating from zero velocity."""
        return t * t

    @staticmethod
    def ease_out(t: float) -> float:
        """Decelerating to zero velocity."""
        return t * (2 - t)

    @staticmethod
    def ease_in_out(t: float) -> float:
        """Acceleration until halfway, then deceleration."""
        if t < 0.5:
            return 2 * t * t
        return -1 + (4 - 2 * t) * t

    @staticmethod
    def bounce(t: float) -> float:
        """Bouncing effect."""
        if t < 0.5:
            return 8 * t * t * t * t
        t = t - 1
        return 1 + 8 * t * t * t * t

    @staticmethod
    def elastic(t: float) -> float:
        """Elastic/spring effect."""
        import math

        return math.sin(13 * math.pi / 2 * t) * math.pow(2, 10 * (t - 1))

    @staticmethod
    def get_easing_func(easing_type: EasingType) -> Callable[[float], float]:
        """Get easing function.

        Args:
            easing_type: Type of easing

        Returns:
            Easing function f(t) where t is 0.0 to 1.0
        """
        if easing_type == EasingType.LINEAR:
            return EasingCurve.linear
        elif easing_type == EasingType.EASE_IN:
            return EasingCurve.ease_in
        elif easing_type == EasingType.EASE_OUT:
            return EasingCurve.ease_out
        elif easing_type == EasingType.EASE_IN_OUT:
            return EasingCurve.ease_in_out
        elif easing_type == EasingType.BOUNCE:
            return EasingCurve.bounce
        elif easing_type == EasingType.ELASTIC:
            return EasingCurve.elastic
        else:
            return EasingCurve.linear


class TransitionEffect:
    """Individual transition effect."""

    def __init__(self, config: TransitionConfig) -> None:
        """Initialize transition effect.

        Args:
            config: Transition configuration
        """
        self.config = config
        self.easing_func = EasingCurve.get_easing_func(config.easing)

    def get_ffmpeg_filter(self) -> str:
        """Generate FFmpeg filter for transition.

        Returns:
            FFmpeg filter string
        """
        transition_type = self.config.transition_type
        duration = self.config.duration_sec
        intensity = self.config.intensity

        if transition_type == TransitionType.FADE:
            return f"fade=t=in:d={duration}"

        elif transition_type == TransitionType.DISSOLVE:
            return f"xfade=transition=dissolve:duration={duration}"

        elif transition_type == TransitionType.SLIDE_LEFT:
            return f"xfade=transition=slideleft:duration={duration}"

        elif transition_type == TransitionType.SLIDE_RIGHT:
            return f"xfade=transition=slideright:duration={duration}"

        elif transition_type == TransitionType.SLIDE_UP:
            return f"xfade=transition=slideup:duration={duration}"

        elif transition_type == TransitionType.SLIDE_DOWN:
            return f"xfade=transition=slidedown:duration={duration}"

        elif transition_type == TransitionType.WIPE_LEFT:
            return f"xfade=transition=wipeleft:duration={duration}"

        elif transition_type == TransitionType.WIPE_RIGHT:
            return f"xfade=transition=wiperight:duration={duration}"

        elif transition_type == TransitionType.ZOOM_IN:
            zoom_val = 1.0 + (0.5 * intensity)
            return f"scale=iw*{zoom_val}:ih*{zoom_val}"

        elif transition_type == TransitionType.ZOOM_OUT:
            zoom_val = 1.0 - (0.3 * intensity)
            return f"scale=iw*{zoom_val}:ih*{zoom_val}"

        elif transition_type == TransitionType.BLUR:
            blur_val = int(15 * intensity)
            return f"boxblur={blur_val}:{blur_val}"

        elif transition_type == TransitionType.MOSAIC:
            mosaic_val = int(20 * intensity)
            return f"pixelize=block_height={mosaic_val}:block_width={mosaic_val}"

        else:
            return ""

    def get_duration_frames(self, fps: int) -> int:
        """Get transition duration in frames.

        Args:
            fps: Frames per second

        Returns:
            Number of frames
        """
        return int(self.config.duration_sec * fps)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TransitionEffect({self.config.transition_type.value}, "
            f"{self.config.duration_sec}s, {self.config.easing.value})"
        )


class TransitionLibrary:
    """Library of pre-made transitions."""

    # Common transitions
    FADE_FAST = TransitionConfig(
        transition_type=TransitionType.FADE,
        duration_sec=0.3,
        easing=EasingType.LINEAR,
    )

    FADE_NORMAL = TransitionConfig(
        transition_type=TransitionType.FADE,
        duration_sec=0.5,
        easing=EasingType.EASE_IN_OUT,
    )

    FADE_SLOW = TransitionConfig(
        transition_type=TransitionType.FADE,
        duration_sec=1.0,
        easing=EasingType.EASE_IN_OUT,
    )

    DISSOLVE_NORMAL = TransitionConfig(
        transition_type=TransitionType.DISSOLVE,
        duration_sec=0.5,
        easing=EasingType.LINEAR,
    )

    SLIDE_LEFT_FAST = TransitionConfig(
        transition_type=TransitionType.SLIDE_LEFT,
        duration_sec=0.3,
        easing=EasingType.EASE_OUT,
    )

    SLIDE_RIGHT_FAST = TransitionConfig(
        transition_type=TransitionType.SLIDE_RIGHT,
        duration_sec=0.3,
        easing=EasingType.EASE_OUT,
    )

    ZOOM_IN_FAST = TransitionConfig(
        transition_type=TransitionType.ZOOM_IN,
        duration_sec=0.4,
        intensity=0.5,
        easing=EasingType.EASE_OUT,
    )

    ZOOM_OUT_FAST = TransitionConfig(
        transition_type=TransitionType.ZOOM_OUT,
        duration_sec=0.4,
        intensity=0.4,
        easing=EasingType.EASE_OUT,
    )

    BLUR_FAST = TransitionConfig(
        transition_type=TransitionType.BLUR,
        duration_sec=0.3,
        intensity=1.0,
        easing=EasingType.LINEAR,
    )

    MOSAIC_FAST = TransitionConfig(
        transition_type=TransitionType.MOSAIC,
        duration_sec=0.3,
        intensity=1.5,
        easing=EasingType.LINEAR,
    )

    @staticmethod
    def get_transition(name: str) -> TransitionConfig | None:
        """Get transition by name.

        Args:
            name: Transition name (e.g., "FADE_FAST")

        Returns:
            TransitionConfig or None
        """
        return getattr(TransitionLibrary, name.upper(), None)

    @staticmethod
    def get_all_transitions() -> dict[str, TransitionConfig]:
        """Get all available transitions.

        Returns:
            Dictionary of name→TransitionConfig
        """
        transitions = {}
        for attr_name in dir(TransitionLibrary):
            if not attr_name.startswith("_"):
                attr = getattr(TransitionLibrary, attr_name)
                if isinstance(attr, TransitionConfig):
                    transitions[attr_name] = attr
        return transitions


class TransitionSequence:
    """Sequence of transitions for a video."""

    def __init__(self) -> None:
        """Initialize transition sequence."""
        self.transitions: list[TransitionEffect] = []

    def add_transition(self, config: TransitionConfig) -> None:
        """Add transition to sequence.

        Args:
            config: Transition configuration
        """
        effect = TransitionEffect(config)
        self.transitions.append(effect)

    def add_transition_between_scenes(
        self, scene_duration: float, transition_type: TransitionType = TransitionType.FADE
    ) -> None:
        """Add transition between scenes.

        Args:
            scene_duration: Duration of scene in seconds
            transition_type: Type of transition
        """
        config = TransitionConfig(
            transition_type=transition_type,
            duration_sec=min(0.5, scene_duration * 0.1),  # 10% of scene, max 0.5s
            easing=EasingType.EASE_IN_OUT,
        )
        self.add_transition(config)

    def get_total_transition_duration(self) -> float:
        """Get total duration of all transitions.

        Returns:
            Total duration in seconds
        """
        return sum(t.config.duration_sec for t in self.transitions)

    def get_ffmpeg_filters(self) -> list[str]:
        """Get FFmpeg filters for all transitions.

        Returns:
            List of filter strings
        """
        return [t.get_ffmpeg_filter() for t in self.transitions]

    def __repr__(self) -> str:
        """String representation."""
        return f"TransitionSequence({len(self.transitions)} transitions)"

    def __len__(self) -> int:
        """Number of transitions."""
        return len(self.transitions)

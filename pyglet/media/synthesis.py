from __future__ import annotations

import math as _math
import struct as _struct

from typing import TYPE_CHECKING
from random import uniform as _uniform
from dataclasses import dataclass

from pyglet.media.codecs.base import AudioData, AudioFormat, Source

if TYPE_CHECKING:
    from typing import Generator, Sequence


# Envelope classes:

class Envelope:
    """Base class for SynthesisSource amplitude envelopes.

    Custom Envelopes need only provide a single `get_generator`
    method that takes the sample rate, and duration as arguments.
    """

    def get_generator(self, sample_rate: float, duration: float) -> Generator[float]:
        """Get a generator instance.

        Args:
            sample_rate:
                The sample rate of the Source this will be applied to.
            duration:
                The duration of the Source. This is used to calculate
                the number of bytes for some Envelopes.
        """
        raise NotImplementedError


class FlatEnvelope(Envelope):
    """A flat envelope, providing basic amplitude setting.

    Args:
        amplitude:
            The amplitude (volume) of the wave, from 0.0 to 1.0.
            Values outside this range will be clamped.
    """

    def __init__(self, amplitude: float = 0.5):
        self.amplitude = max(min(1.0, amplitude), 0)

    def get_generator(self, sample_rate: float | None = None, duration: float | None = None) -> Generator[float]:
        amplitude = self.amplitude
        while True:
            yield amplitude


class LinearDecayEnvelope(Envelope):
    """A linearly decaying envelope.

    This envelope linearly decays the amplitude from the peak value
    to 0, over the length of the waveform.

    Args:
        peak:
            The Initial peak value of the envelope, from 0.0 to 1.0.
            Values outside this range will be clamped.
    """

    def __init__(self, peak: float = 1.0):
        self.peak = max(min(1.0, peak), 0)

    def get_generator(self, sample_rate: float, duration: float) -> Generator[float]:
        peak = self.peak
        total_bytes = int(sample_rate * duration)
        for i in range(total_bytes):
            yield (total_bytes - i) / total_bytes * peak
        while True:
            yield 0


class ADSREnvelope(Envelope):
    """A four-part Attack, Decay, Suspend, Release envelope.

    This is a four part ADSR envelope. The attack, decay, and release
    parameters should be provided in seconds. For example, a value of
    0.1 would be 100ms. The sustain_amplitude parameter affects the
    sustain volume. This defaults to a value of 0.5, but can be provided
    on a scale from 0.0 to 1.0.

    Args:
        attack:
            The attack time, in seconds.
        decay:
            The decay time, in seconds.
        release:
            The release time, in seconds.
        sustain_amplitude:
            The sustain amplitude (volume), from 0.0 to 1.0.
    """

    def __init__(self, attack: float, decay: float, release: float, sustain_amplitude: float = 0.5):
        self.attack = attack
        self.decay = decay
        self.release = release
        self.sustain_amplitude = max(min(1.0, sustain_amplitude), 0)

    def get_generator(self, sample_rate: float, duration: float) -> Generator[float]:
        sustain_amplitude = self.sustain_amplitude
        total_bytes = int(sample_rate * duration)
        attack_bytes = int(sample_rate * self.attack)
        decay_bytes = int(sample_rate * self.decay)
        release_bytes = int(sample_rate * self.release)
        sustain_bytes = total_bytes - attack_bytes - decay_bytes - release_bytes
        decay_step = (1 - sustain_amplitude) / decay_bytes
        release_step = sustain_amplitude / release_bytes
        for i in range(1, attack_bytes + 1):
            yield i / attack_bytes
        for i in range(1, decay_bytes + 1):
            yield 1 - (i * decay_step)
        for i in range(1, sustain_bytes + 1):
            yield sustain_amplitude
        for i in range(1, release_bytes + 1):
            yield sustain_amplitude - (i * release_step)
        while True:
            yield 0


class TremoloEnvelope(Envelope):
    """A tremolo envelope, for modulation amplitude.

    A tremolo envelope that modulates the amplitude of the
    waveform with a sinusoidal pattern. The depth and rate
    of modulation can be specified. Depth is calculated as
    a percentage of the maximum amplitude. For example:
    a depth of 0.2 and amplitude of 0.5 will fluctuate
    the amplitude between 0.4 an 0.5.

    Args:
        depth:
            The amount of fluctuation, from 0.0 to 1.0.
        rate:
            The fluctuation frequency, in seconds.
        amplitude:
            The peak amplitude (volume), from 0.0 to 1.0.
    """

    def __init__(self, depth: float, rate: float, amplitude: float = 0.5):
        self.depth = max(min(1.0, depth), 0)
        self.rate = rate
        self.amplitude = max(min(1.0, amplitude), 0)

    def get_generator(self, sample_rate: float, duration: float) -> Generator[float]:
        total_bytes = int(sample_rate * duration)
        period = total_bytes / duration
        max_amplitude = self.amplitude
        min_amplitude = max(0.0, (1.0 - self.depth) * self.amplitude)
        step = (_math.pi * 2) / period / self.rate
        for i in range(total_bytes):
            value = _math.sin(step * i)
            yield value * (max_amplitude - min_amplitude) + min_amplitude
        while True:
            yield 0


# Waveform generators

def silence_generator(frequency: float, sample_rate: float) -> Generator[float]:
    while True:
        yield 0.0


def noise_generator(frequency: float, sample_rate: float) -> Generator[float]:
    while True:
        yield _uniform(-1.0, 1.0)


def sine_generator(frequency: float, sample_rate: float) -> Generator[float]:
    step = 2.0 * _math.pi * frequency / sample_rate
    i = 0.0
    while True:
        yield _math.sin(i * step)
        i += 1.0


def triangle_generator(frequency: float, sample_rate: float) -> Generator[float]:
    step = 4.0 * frequency / sample_rate
    value = 0.0
    while True:
        if value > 1.0:
            value = 1.0 - (value - 1.0)
            step = -step
        if value < -1.0:
            value = -1.0 - (value - -1.0)
            step = -step
        yield value
        value += step


def sawtooth_generator(frequency: float, sample_rate: float) -> Generator[float]:
    period_length = int(sample_rate / frequency)
    step = 2.0 * frequency / sample_rate
    i = 0.0
    while True:
        yield step * (i % period_length) - 1.0
        i += 1.0


def pulse_generator(frequency: float, sample_rate: float, duty_cycle: float = 50.0) -> Generator[float]:
    period_length = int(sample_rate / frequency)
    duty_cycle = int(duty_cycle * period_length / 100)
    i = 0.0
    while True:
        yield int(i % period_length < duty_cycle) * 2.0 - 1.0
        i += 1.0


# Source classes:

class SynthesisSource(Source):
    """Base class for synthesized waveforms.

    Args:
        generator:
            A waveform generator that produces a stream of floats from (-1.0, 1.0)
        duration:
            The length, in seconds, of audio that you wish to generate.
        sample_rate:
            Audio samples per second. (CD quality is 44100).
        envelope:
            An optional Envelope to apply to the waveform.
    """
    def __init__(self, generator: Generator, duration: float, sample_rate: int = 44800, envelope: Envelope | None = None):
        self._generator = generator
        self._duration = duration
        self.audio_format = AudioFormat(channels=1, sample_size=16, sample_rate=sample_rate)

        self._envelope = envelope or FlatEnvelope(amplitude=1.0)
        self._envelope_generator = self._envelope.get_generator(sample_rate, duration)

        # Two bytes per sample (16-bit):
        self._bytes_per_second = sample_rate * 2
        # Maximum offset, aligned to sample:
        self._max_offset = int(self._bytes_per_second * duration) & 0xfffffffe
        self._offset = 0

    def get_audio_data(self, num_bytes: int) -> AudioData | None:
        """Return ``num_bytes`` bytes of audio data."""
        num_bytes = min(num_bytes, self._max_offset - self._offset)
        if num_bytes <= 0:
            return None

        self._offset += num_bytes

        # Generate bytes:
        samples = num_bytes >> 1
        generator = self._generator
        envelope = self._envelope_generator
        sample_data = (int(next(generator) * next(envelope) * 0x7fff) for _ in range(samples))
        data = _struct.pack(f"{samples}h", *sample_data)

        return AudioData(data, num_bytes)

    def seek(self, timestamp: float) -> None:
        # Bound within duration & align to sample:
        offset = int(timestamp * self._bytes_per_second)
        self._offset = min(max(offset, 0), self._max_offset) & 0xfffffffe
        self._envelope_generator = self._envelope.get_generator(self.audio_format.sample_rate, self._duration)

    def is_precise(self) -> bool:
        return True


class Silence(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a Silent waveform."""
        super().__init__(silence_generator(frequency, sample_rate), duration, sample_rate, envelope)


class WhiteNoise(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a random white noise waveform."""
        super().__init__(noise_generator(frequency, sample_rate), duration, sample_rate, envelope)


class Sine(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a sinusoid (sine) waveform."""
        super().__init__(sine_generator(frequency, sample_rate), duration, sample_rate, envelope)


class Square(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a Square (pulse) waveform."""
        super().__init__(pulse_generator(frequency, sample_rate), duration, sample_rate, envelope)


class Triangle(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a Triangle waveform."""
        super().__init__(triangle_generator(frequency, sample_rate), duration, sample_rate, envelope)


class Sawtooth(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a Sawtooth waveform."""
        super().__init__(sawtooth_generator(frequency, sample_rate), duration, sample_rate, envelope)


#############################################
#   Experimental multi-operator FM synthesis:
#############################################

@dataclass(frozen=True, slots=True)
class Modulation:
    source: int
    target: int


@dataclass(frozen=True, slots=True)
class Algorithm:
    """4-operator FM routing. Indices are 0-based (0=Op1 … 3=Op4)."""
    name: str
    carriers: tuple[int, ...]
    modulations: tuple[Modulation, ...]
    feedback: int | None = 0

    def __post_init__(self) -> None:
        ops = set(self.carriers)
        for m in self.modulations:
            ops.add(m.source)
            ops.add(m.target)
        if self.feedback is not None:
            ops.add(self.feedback)
        if any(not 0 <= i <= 3 for i in ops):
            raise ValueError("Operator indices must be in 0..3")


ALGO_0 = Algorithm(   # 1 → 2 → 3 → 4
    name="Algorithm 0",
    carriers=(3,),
    modulations=(
        Modulation(0, 1),
        Modulation(1, 2),
        Modulation(2, 3),
    ),
    feedback=0,
)

ALGO_1 = Algorithm(   # (1 + 2) → 3 → 4
    name="Algorithm 1",
    carriers=(3,),
    modulations=(
        Modulation(0, 2),
        Modulation(1, 2),
        Modulation(2, 3),
    ),
    feedback=0,
)

ALGO_2 = Algorithm(   # 1 → 3 → 4,  2 → 4
    name="Algorithm 2",
    carriers=(3,),
    modulations=(
        Modulation(0, 2),
        Modulation(2, 3),
        Modulation(1, 3),
    ),
    feedback=0,
)

ALGO_3 = Algorithm(   # 1 → 2 → 4,  3 → 4
    name="Algorithm 3",
    carriers=(3,),
    modulations=(
        Modulation(0, 1),
        Modulation(1, 3),
        Modulation(2, 3),
    ),
    feedback=0,
)

ALGO_4 = Algorithm(   # 1 → 2  and  3 → 4
    name="Algorithm 4",
    carriers=(1, 3),
    modulations=(
        Modulation(0, 1),
        Modulation(2, 3),
    ),
    feedback=0,
)

ALGO_5 = Algorithm(   # 1 modulates 2, 3 and 4
    name="Algorithm 5",
    carriers=(1, 2, 3),
    modulations=(
        Modulation(0, 1),
        Modulation(0, 2),
        Modulation(0, 3),
    ),
    feedback=0,
)

ALGO_6 = Algorithm(   # 1 → 2,  3 and 4 are carriers
    name="Algorithm 6",
    carriers=(1, 2, 3),
    modulations=(
        Modulation(0, 1),
    ),
    feedback=0,
)

ALGO_7 = Algorithm(   # four parallel carriers
    name="Algorithm 7",
    carriers=(0, 1, 2, 3),
    modulations=(),
    feedback=0,
)

ALGORITHMS = {
    0: ALGO_0,
    1: ALGO_1,
    2: ALGO_2,
    3: ALGO_3,
    4: ALGO_4,
    5: ALGO_5,
    6: ALGO_6,
    7: ALGO_7,
}


class Operator:
    """Single FM operator with phase modulation and optional feedback."""

    def __init__(self, frequency: float = 440.0, sample_rate: int = 44800, index: float = 1.0, feedback: float = 0.0):
        self.sample_rate = sample_rate
        self.index = index
        self.feedback = feedback

        self._frequency = frequency
        self._step = 2.0 * _math.pi * frequency / sample_rate
        self._phase = 0.0
        self._last = 0.0

        self.modulators: list[Operator] = []

    @property
    def frequency(self) -> float:
        return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        self._frequency = value
        self._step = 2.0 * _math.pi * value / self.sample_rate

    def add_modulator(self, op: Operator) -> None:
        self.modulators.append(op)

    def __next__(self) -> float:
        mod = sum(next(m) for m in self.modulators)
        mod += self.feedback * self._last

        value = _math.sin(self._phase + self.index * mod)

        self._last = value
        self._phase += self._step
        return value

    def reset(self) -> None:
        self._phase = 0.0
        self._last = 0.0

    def __iter__(self):
        return self


# ----------------------------------------------------------------------
# Mixing helper
# ----------------------------------------------------------------------

def mix_operators(operators: Sequence[Operator]) -> Generator[float, None, None]:
    """Average the output of multiple carriers."""
    n = len(operators)
    if n == 0:
        while True:
            yield 0.0
    while True:
        yield sum(next(op) for op in operators) / n


# ----------------------------------------------------------------------
# FMVoice (SynthesisSource subclass)
# ----------------------------------------------------------------------

class FMVoice(SynthesisSource):
    """
    4-operator FM voice (YM2612-style).

    Operators are pre-allocated and can be adjusted after creation.
    """

    def __init__(self, duration: float, algorithm: Algorithm | int = 0, sample_rate: int = 44800, feedback_level: float = 0.0, envelope: Envelope | None = None):
        if isinstance(algorithm, int):
            algorithm = ALGORITHMS[algorithm]

        self.sample_rate = sample_rate
        self.algorithm = algorithm

        # Pre-allocate 4 operators
        self.ops: list[Operator] = [Operator(frequency=440.0, sample_rate=sample_rate) for _ in range(4)]

        self._wire_algorithm(algorithm)
        self.set_feedback(feedback_level)

        # Create the generator from the carriers
        carriers = [self.ops[i] for i in algorithm.carriers]
        generator = mix_operators(carriers)

        super().__init__(generator, duration, sample_rate, envelope)

    # ----- internal -----

    def _wire_algorithm(self, algorithm: Algorithm) -> None:
        for op in self.ops:
            op.modulators.clear()

        for mod in algorithm.modulations:
            self.ops[mod.target].add_modulator(self.ops[mod.source])

        self.algorithm = algorithm

    # ----- public API -----

    def set_algorithm(self, algorithm: Algorithm | int) -> None:
        if isinstance(algorithm, int):
            algorithm = ALGORITHMS[algorithm]
        self._wire_algorithm(algorithm)
        # Note: changing algorithm after start does not rebuild the generator.
        # For full support you would also need to replace self._generator.

    def set_feedback(self, level: float) -> None:
        for op in self.ops:
            op.feedback = 0.0
        if self.algorithm.feedback is not None:
            self.ops[self.algorithm.feedback].feedback = level

    def set_frequency(self, op_index: int, frequency: float) -> None:
        self.ops[op_index].frequency = frequency

    def set_index(self, op_index: int, index: float) -> None:
        self.ops[op_index].index = index

    def seek(self, timestamp: float) -> None:
        """Reset operators when seeking."""
        for op in self.ops:
            op.reset()
        super().seek(timestamp)

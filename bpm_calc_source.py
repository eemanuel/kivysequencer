#!/usr/bin/env python
# script from online, saving for later. (unknown credits at the moment)
import wave
from string import capwords
from optparse import OptionParser


def ms_to_bpm(length, measures=1, beat=1):
    """Calculates beat per minute of a soundfile given the lenght in
    milliseconds, the number of measures and the beat, where 4/4 is 1.
    Returns bpm
    """
    bpm = round(60000 / ((float(length / beat) / measures) / 4), 2)
    return bpm


def wavduration(wavfile):
    """Returns the duration of a wavfile in milliseconds"""
    myfile = wave.open(wavfile, "r")
    frames = 1.0 * myfile.getnframes()
    sr = myfile.getframerate()
    time = 1.0 * (frames / sr)
    return int(round(time * 1000))


def delay_times(bpm=120):
    """Returns delay times for the specified bpm, in milliseconds"""
    result = []
    durations = [
        (1, "whole"),
        ((3.0 / 4), "dotted half"),
        ((1.0 / 2), "half"),
        ((3.0 / 8), "dotted quarter"),
        ((1.0 / 4), "quarter"),
        ((3.0 / 16), "dotted eight"),
        (round(((1.0 / 2) / 3), 5), "quarter triplet"),
        ((1.0 / 8), "eight"),
        ((3.0 / 32), "dotted sixteenth"),
        (round(((1.0 / 4) / 3), 5), "eight triplet"),
        ((1.0 / 16), "sixteenth"),
        ((3.0 / 64), "dotted thirty second"),
        (round(((1.0 / 8) / 3), 5), "sixteenth triplet"),
        ((1.0 / 32), "thirty second"),
    ]
    for duration, description in durations:
        title = capwords(description)
        delay = (duration * 4000) / (bpm / 60.0)
        frequency = 1000 / delay
        result.append({"title": title, "delay": delay, "frequency": frequency})
    return result


def delay_times_format(bpm=120):
    a = delay_times(bpm)
    a.sort()
    a.reverse()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "-f",
        "--file",
        dest="filename",
        default="none",
        help="wave FILE to load",
        metavar="FILE",
    )
    parser.add_option(
        "-b", "--bpm", dest="bpm", default="analize", help="beats per minute"
    )
    parser.add_option(
        "-B", "--bars", dest="bars", help="number of bars in the wav file"
    )
    parser.add_option(
        "-m", "--meter", dest="meter", help="as in 3/4 or 12/8, default 4/4"
    )

    (options, args) = parser.parse_args()

    # print options, args

    if options.meter:
        a = options.meter.split("/")
        meter = float(a[0]) / float(a[1])
    else:
        meter = 1

    if options.bars:
        bars = int(options.bars)
    else:
        bars = 1
    wavfile = options.filename

    if wavfile == "none":
        if options.bpm == "analize":
            bpm = 120
        else:
            bpm = float(options.bpm)
    else:

        if options.bpm != "analize":
            bpm = float(options.bpm)
            delay_times_format(bpm)
        else:
            bpm = 120

        wavduration = wavduration(wavfile)
        bpm = ms_to_bpm(wavduration, bars, meter)

    delay_times_format(bpm)

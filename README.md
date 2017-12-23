# Program Cozmo with his blocks

This is a simple Cozmo program built with the Cozmo SDK.  See
[this guide](http://cozmosdk.anki.com/docs/getstarted.html) if you need to set up
 your environment.

Place Cozmo's blocks in front of him to program a very simple virtual machine.
They should be about 5" in front of him and half an inch apart. For example, this
program will cause Cozmo to say "42":

    0x10 0x0 0x17  # Load 23 at 0x0
    0x10 0x1 0x13  # Load 19 at 0x1
    0x11 0x0 0x1   # Add 0x1 to 0x0, store at 0x0
    0x12 0x0       # Say value at 0x0
    0x13           # Done!

To load the program, place (or don't place) 3 cubes in front of Cozmo at a time.
Each cube represents a single bit with the cube to Cozmo's left being the least
significant bit.  For example, the following sequence encodes the number 42:

    ┌- Cubes
    |    ┌- Cozmo
    0    |         | 1              | 0
    1   ]OD        | 0    ]OD       | 0    ]OD
    0              | 1              | 0
    _______________|________________|_____________
    Sequence 1     | Sequence 2     |Sequence 3

The program will advance through sequences by asking you to tap cubes.  Since
this is one of the more tedious ways of programming a computer, you can redo a
bad bit sequence by not tapping to continue.

## License
MIT License - © Jason Snell 2017
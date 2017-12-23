#!/usr/bin/env python3
"""Program Cozmo with his blocks

Place Cozmo's blocks in front of him to program a very simple virtual machine.
They should be about 5" in front of him and half an inch apart.  You'll find the
*very* simple instruction set below.  For example, this program will cause Cozmo
to say "42":

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
"""

import sys
import asyncio
from collections import deque

import cozmo
from cozmo.util import degrees
from cozmo.objects import LightCube1Id, LightCube2Id, LightCube3Id


class TinyCPU:
    """The tiniest CPU

    This class implements a very simple CPU.  It takes a single robot argument
    it uses to manipulate Cozmo.  To build a program, pass in bytes via byte().
    To run the loaded program, simply call run().  Unfortunately, this CPU is
    stackless and doesn't currently support subroutines.  In fact, it only
    supports loading, adding, and saying numbers, for now.  Error handling is
    nonexistent, and poor programming will surely lead to sad kittens.

    Args:
        robot (cozmo.robot.Robot): instance of the robot.
    """
    MEM_SIZE = 256

    def __init__(self, robot: cozmo.robot.Robot):
        self.robot = robot
        self.memory = [0] * self.MEM_SIZE
        self.prog = deque([])

        self.INSTRUCTIONS = {
            0x10: self.ins_load,  # LOAD addr, val - Loads val into addr
            0x11: self.ins_add,   # ADD X, Y       - Add Y to X and store in X
            0x12: self.ins_say,   # SAY addr       - Say the value stored at attr
            0x13: self.ins_ret,   # RET            - Return
        }

    def byte(self, byte):
        """Append a byte onto the program queue"""
        self.prog.append(byte)

    def run(self):
        """Run the current loaded program"""
        while len(self.prog) > 0:
            ins = self.prog.popleft()
            self.INSTRUCTIONS[ins]()

    def ins_load(self):
        """Load instruction - addr is loaded with val"""
        addr = self.prog.popleft()
        val = self.prog.popleft()

        self.memory[addr] = val

    def ins_add(self):
        """Add instruction - x is added with y and the result is stored back to x"""
        x = self.prog.popleft()
        y = self.prog.popleft()

        self.memory[x] = self.memory[x] + self.memory[y]

    def ins_say(self):
        """Say instruction - Say the value at addr - perhaps a first in assembly"""
        addr = self.prog.popleft()

        self.robot.say_text(str(self.memory[addr])).wait_for_completed()

    def ins_ret(self):
        """Return instruction - no-op for now but might be useful someday with subroutines"""
        return


class Cozputer:
    """Program a tiny CPU with Cozmo's cubes
    See the description at the top of this file for more details.

    Args:
        robot (cozmo.robot.Robot): instance of the robot.
    """
    def __init__(self, robot: cozmo.robot.Robot):
        self.robot = robot
        self.cpu = TinyCPU(robot)

    def run(self):
        """Run this Cozmo program"""
        self.robot.set_head_angle(degrees(0)).wait_for_completed()

        while True:
            print("Set cubes and tap 3 times to continue (or fewer to run)...")
            if self.read_taps(3) != 3:
                break
            byte = self.read_byte()
            self.cpu.byte(byte)

        self.cpu.run()

    def read_taps(self, max_taps=3):
        """
        Read a number of taps on any cube.  Note that moving cubes around
        often registers as a tap.

        Args:
            max_taps: maximum number of taps to wait for, defaults to 3
        """
        taps = 0
        for _ in range(max_taps):
            try:
                self.robot.world.wait_for(cozmo.objects.EvtObjectTapped, timeout=10)
                if max_taps > 1:
                    print("%d " % (taps + 1), end="")
                    sys.stdout.flush()
                taps += 1
            except asyncio.TimeoutError:
                if max_taps > 1:
                    print("x ", end="")
                    sys.stdout.flush()

        if max_taps > 1:
            print("")
        return taps

    def read_byte(self):
        """
        Read a byte via Cozmo's cubes.  See the description at the top of this
        file for the interface.
        """
        byte = 0
        for i in range(3):
            self.robot.set_lift_height(0).wait_for_completed()
            byte |= self.read_bits() << i * 3
            self.robot.set_lift_height(1).wait_for_completed()
            self.clear_lights()

            if i < 2:
                print("Set cubes and tap 3 times to continue...")
                self.read_taps()

        print("Read byte: %x" % byte)
        return byte

    def clear_lights(self):
        """Turn all cube LEDs off"""
        self.robot.world.get_light_cube(LightCube1Id).set_lights_off()
        self.robot.world.get_light_cube(LightCube2Id).set_lights_off()
        self.robot.world.get_light_cube(LightCube3Id).set_lights_off()

    def read_bits(self):
        """Read a single triplet of bits"""
        bits = 0

        for obj in self.robot.world.visible_objects:
            if isinstance(obj, cozmo.objects.LightCube):
                obj.set_lights(cozmo.lights.blue_light)
                y = obj.pose.position.y
                if y > 30:
                    bits |= 1
                elif y < -30:
                    bits |= 1 << 2
                else:
                    bits |= 1 << 1

        print("Read bits: %d - tap a cube to continue or wait to redo" % bits)
        if self.read_taps(1) == 1:
            return bits
        else:
            return self.read_bits()


def boot(robot: cozmo.robot.Robot):
    puter = Cozputer(robot)
    puter.run()


cozmo.run_program(boot)

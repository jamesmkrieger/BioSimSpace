"""
@package biosimspace
@author  Lester Hedges
@brief   Base class and helper functions for the various sample modules.
"""

import Sire.Base
import Sire.Mol

from ..Protocol.protocol_type import ProtocolType

from operator import add, sub
import tempfile

try:
    pygtail = Sire.try_import("pygtail")
except ImportError:
    raise ImportError('Pygtail is not installed. Please install pygtail in order to use BioSimSpace.')

class Process(Sire.Base.Process):
    """ Base class for running different biomolecular simulation processes. """

    def __init__(self, system, protocol, name="process"):
        """ Constructor.

        Keyword arguments:

        system   -- The molecular system.
        protocol -- The protocol for the process.
        name     -- The name of the process.
        """

	# Don't allow user to create an instance of this base class.
        # Since we have multiple inheritance (the base inherits from Process,
        # which itself inherits from Sire.Base.Process) it's diffult to
        # use the "abc" library.
        if type(self) == Process:
            raise Exception("<Process> must be subclassed.")

	# Copy the passed system, protocol, and process name.
        self._system = system
        self._protocol = protocol
        self._name = name

        # Create a temporary working directory and store the directory name.
        self._tmp_dir = tempfile.TemporaryDirectory()

        # Files for redirection of stdout and stderr.
        self._stdout_file = "%s/%s.out" % (self._tmp_dir.name, name)
        self._stderr_file = "%s/%s.err" % (self._tmp_dir.name, name)

        # Create the files. This makes sure that the 'stdout' and 'stderr'
        # methods can be called when the files are empty.
        open(self._stdout_file, 'a').close()
        open(self._stderr_file, 'a').close()

        # Initialise lists to store the contents of stdout and stderr.
        self._stdout = []
        self._stderr = []

    def stdout(self, n=10):
        """ Print the last n lines of the stdout buffer.

            Keyword arguments:

            n -- The number of lines to print.
        """

        # Ensure that the number of lines is positive.
        if n < 0:
            raise ValueError("The number of lines must be positive!")

        # Append any new lines to the stdout list.
        for line in pygtail.Pygtail(self._stdout_file):
            self._stdout.append(line.rstrip())

        # Get the current number of lines.
        num_lines = len(self._stdout)

        # Set the line from which to start printing.
        if num_lines < n:
            start = 0
        else:
            start = num_lines - n

        # Print the lines.
        for x in range(start, num_lines):
            print(self._stdout[x])

    def stderr(self, n=10):
        """ Print the last n lines of the stderr buffer.

            Keyword arguments:

            n -- The number of lines to print.
        """

        # Ensure that the number of lines is positive.
        if n < 0:
            raise ValueError("The number of lines must be positive!")

        # Append any new lines to the stdout list.
        for line in pygtail.Pygtail(self._stderr_file):
            self._stderr.append(line.rstrip())

        # Get the current number of lines.
        num_lines = len(self._stderr)

        # Set the line from which to start printing.
        if num_lines < n:
            start = 0
        else:
            start = num_lines - n

        # Print the lines.
        for x in range(start, num_lines):
            print(self._stderr[x])

def _compute_box_size(system, tol=0.3, buffer=0.1):
    """ Compute the box size and origin from the atomic coordinates.

        Keyword arguments:

        system -- A Sire molecular system.
        tol    -- The tolerance for determining whether the box is square
                  and whether the origin lies at (0, 0, 0).
        buffer -- The percentage by which to expand the box to account for
                  periodic wrapping.
    """

    # Store the list of molecule indices.
    mol_nums = system.molNums()

    # Initialise the min and max box size for each dimension.
    box_min = [1000000]  * 3
    box_max = [-1000000] * 3

    # Loop over all of the molecules.
    for num in mol_nums:

        # Loop over all atoms in the molecule.
        for atom in system[num].atoms():

            # Extract the atomic coordinates.
            try:
                coord = atom.property("coordinates")

            except UserWarning:
               raise

            # Check coordinates against the current min/max.
            for x in range(0, 3):

               if coord[x] < box_min[x]:
                   box_min[x] = coord[x]

               elif coord[x] > box_max[x]:
                   box_max[x] = coord[x]

    # Calculate the base length of the simulation box.
    box_size = list(map(sub, box_max, box_min))

    # Calculate the centre of the box.
    box_origin = [x * 0.5 for x in list(map(add, box_min, box_max))]

    # Store the base length with the maximum size.
    max_size = max(box_size)

    # Loop over all box dimensions.
    for x in range(0, 3):

        # Assume the box is square if the base lengths are similar.
        if box_size[x] > (1 - tol) * max_size:
            box_size[x] = max_size

        # Assume the origin is at zero if the centre of mass is
        # close  to (0, 0, 0)
        if box_origin[x] / box_size[x] < tol:
            box_origin[x] = 0

    # Add a buffer to the box size to account for atom wrapping.
    box_size = [x * (1 + buffer) for x in box_size]

    return (tuple(box_size), tuple(box_origin))

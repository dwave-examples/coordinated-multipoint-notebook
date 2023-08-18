# Copyright 2023 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import unittest

def run_jn(jn, timeout):

    open_jn = open(jn, "r", encoding='utf-8')
    notebook = nbformat.read(open_jn, nbformat.current_nbformat)
    open_jn.close()

    preprocessor = ExecutePreprocessor(timeout=timeout, kernel_name='python3')
    preprocessor.allow_errors = True
    preprocessor.preprocess(notebook, {'metadata': {'path': os.path.dirname(jn)}})

    return notebook

def collect_jn_errors(nb):

    errors = []
    for cell in nb.cells:
        if 'outputs' in cell:
            for output in cell['outputs']:
                if output.output_type == 'error':
                    errors.append(output)

    return errors

def cell_text(nb, cell):
    return nb["cells"][cell]["outputs"][0]["text"]

jn_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jn_file = os.path.join(jn_dir, '01-coordinated-multipoint.ipynb')

class TestJupyterNotebook(unittest.TestCase):
    @unittest.skipIf(os.getenv('SKIP_INT_TESTS'), "Skipping integration test.")
    def test_jn(self):
        
        MAX_RUN_TIME = 150      # Runtime on my laptop is 65 seconds

        nb = run_jn(jn_file, MAX_RUN_TIME)
        errors = collect_jn_errors(nb)

        # Smoketest

        self.assertEqual(errors, [])

        #Test cell outputs:

        #Section Modeling a Network, imports
        self.assertEqual([], nb["cells"][2]["outputs"])
         
        #Section Modeling a Network, subsection Create a Network Graph, draw network
        cell_output = cell_text(nb, 4)
        self.assertTrue("Ratio of transmitters to receivers" in cell_output)

        #Section Modeling a Network, subsection Create Channels, create channels
        cell_output = cell_text(nb, 6)
        self.assertTrue("Channels are represented by" in cell_output) 

        #Section Decoding Transmissions (Classical), subsection Create Filters, filters
        cell_output = cell_text(nb, 8)
        self.assertTrue("Created filters" in cell_output) 

        #Section Decoding Transmissions (Classical), subsection Simulate Transmissions, signals
        cell_output = cell_text(nb, 10)
        self.assertTrue("First 10 transmitted symbols" in cell_output) 

        #Section Decoding Transmissions (Classical), subsection Decode Received Signals, apply filter
        cell_output = cell_text(nb, 12)
        self.assertTrue("filter_zero_forcing: decoded with a success rate" in cell_output)

        #Section Decoding Transmissions (Classical), subsection Scaling Up, timing
        cell_output = cell_text(nb, 15)
        self.assertTrue("For a network of" in cell_output)

        #Section Decoding Transmissions (Quantum), QPU selection
        cell_output = cell_text(nb, 17)
        self.assertTrue("Selected Advantage" in cell_output)

        #Section Decoding Transmissions (Quantum), Subsection BQM Representation, create & decode classically 
        cell_output = cell_text(nb, 19)
        self.assertTrue("Ratio of transmitters to receivers" in cell_output)

        #Section Decoding Transmissions (Quantum), Subsection Create BQM, bqm 
        cell_output = cell_text(nb, 21)
        self.assertTrue("BQM has" in cell_output)

        #Section Decoding Transmissions (Quantum), Subsection Decode Received Signal, sampleset 
        cell_output = cell_text(nb, 23)
        self.assertTrue("Decoded with a success rate of" in cell_output)

        #Section Decoding Transmissions (Quantum), Subsection Big_city Problems, loop comparison 
        cell_output = cell_text(nb, 25)
        self.assertTrue("Ratio of transmitters to receivers" in cell_output)

        #Section Decoding Transmissions (Quantum), Subsection Rough-Neighborhood, loop comparison 
        cell_output = cell_text(nb, 27)
        self.assertTrue("Ratio of transmitters to receivers" in cell_output)

        #Section Technical Supplement, Subsection Simulated Annealing, loop comparison 
        cell_output = cell_text(nb, 32)
        self.assertTrue("Ratio of transmitters to receivers" in cell_output)

        #Section Technical Supplement, Subsection Other Classical Algos, loop comparison 
        cell_output = cell_text(nb, 34)
        self.assertTrue("Ratio of transmitters to receivers" in cell_output)

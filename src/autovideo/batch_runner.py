"""
Batch runner for processing multiple video jobs.

This module defines a simple function to iterate over a batch job configuration
and collect the names of the output files that would be produced. The stub
does not perform any actual video building.
"""

from typing import List, Dict, Any


def run_batch(config: Dict[str, Any]) -> List[str]:
    """
    Process a batch configuration and return the expected output filenames.

    :param config: Dictionary containing a `jobs` key with a list of job
        definitions. Each job should include an `output` entry.
    :return: List of output file names extracted from the jobs.
    """
    outputs: List[str] = []
    for job in config.get("jobs", []):
        outputs.append(job.get("output", "output.mp4"))
    return outputs

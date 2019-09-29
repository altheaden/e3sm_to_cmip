#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: CommandLineTool
baseCommand: [python, /export/baldwin32/projects/e3sm_to_cmip/scripts/cwl_workflows/mpaso/mpaso_sbatch_render.py]
inputs:
  input_path:
    type: Directory
  tables_path:
    type: string
    inputBinding:
      prefix: --tables
  metadata_path:
    type: string
    inputBinding:
      prefix: --metadata
  num_workers:
    type: int
    inputBinding:
      prefix: --num_proc
  var_list:
    type: string
    inputBinding:
      prefix: --variables
  mapfile:
    type: string
    inputBinding:
      prefix: --map
  output_path:
    type: string
    inputBinding:
      prefix: --outdir
  timeout:
    type: int
    inputBinding:
      prefix: --timeout

outputs:
  sbatch_script:
    type: File
    outputBinding:
      glob: "run_mpaso_sbatch.sh"

arguments:
  - --input
  - $(inputs.input_path.path)

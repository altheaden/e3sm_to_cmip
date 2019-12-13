#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: Workflow

requirements:
  - class: ScatterFeatureRequirement
  - class: SubworkflowFeatureRequirement
  - class: InlineJavascriptRequirement

inputs:

  frequency: int
  timeout: string
  account: string
  partition: string

  atm_data_path: string
  std_var_list: string[]

  mpas_data_path: string
  mpas_var_list: string[]

  num_workers: int

  hrz_atm_map_path: string
  mpas_map_path: string 
  mpas_restart_path: string
  mpas_region_path: string
  mpas_namelist_path: string

  tables_path: string
  metadata_path: string
  

outputs:
  cmorized:
    type: 
      Directory[]
    outputSource: 
      step_run_mpaso/cmorized
  cmor_logs:
    type:
      Directory[]
    outputSource:
      step_run_mpaso/cmor_logs

steps:
  step_find_casename:
    run:
      find_casename.cwl
    in:
      atm_data_path: atm_data_path
    out:
      - casename
  
  step_find_start_end:
    run:
      find_start_end.cwl
    in:
      data_path: atm_data_path
    out:
      - start_year
      - end_year

  step_segments:
    run: 
      generate_segments.cwl
    in:
      start: step_find_start_end/start_year
      end: step_find_start_end/end_year
      frequency: frequency
    out:
      - segments_start
      - segments_end

  step_discover_atm_files:
    run: 
      discover_atm_files.cwl
    scatter:
      - start
      - end
    scatterMethod:
      dotproduct
    in:
      input: atm_data_path
      start: step_segments/segments_start
      end: step_segments/segments_end
    out:
      - atm_files
  
  step_extract_paths:
    run:
      file_to_string_list.cwl
    in:
      a_File: step_discover_atm_files/atm_files
    scatter:
      a_File
    out:
      - list_of_strings

  step_hrz_remap:
    run: 
      hrzremap.cwl
    scatter:
      - input_files
      - start_year
      - end_year
    scatterMethod:
      dotproduct
    in:
      account: account
      partition: partition
      timeout: timeout
      year_per_file: frequency
      casename: step_find_casename/casename
      start_year: step_segments/segments_start
      end_year: step_segments/segments_end
      map_path: hrz_atm_map_path
      input_files: step_extract_paths/list_of_strings
    out:
      - time_series_files
  
  step_run_mpaso:
    run:
      mpaso.cwl
    in:
      frequency: frequency
      start_year: step_find_start_end/start_year
      end_year: step_find_start_end/end_year
      data_path: mpas_data_path
      map_path: mpas_map_path
      namelist_path: mpas_namelist_path
      restart_path: mpas_restart_path
      psl_files: step_hrz_remap/time_series_files
      region_path: mpas_region_path
      tables_path: tables_path
      metadata_path: metadata_path
      cmor_var_list: mpas_var_list
      num_workers: num_workers
      timeout: timeout
      account: account
      partition: partition
    out:
      - cmorized
      - cmor_logs

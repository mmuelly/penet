"""Convert DICOM files to a single HDF5 file. Generate a list of
CTSeries objects, and dump the list to JSON and pickle files.

Typical usage might be:
  - Use this script to create series_list.pkl
  - Use scripts/split.py to split into train/val/test
  - Use scripts/create_hdf5.py to create HDF5 file for the series_list

Edited for Intermountain data
"""

import argparse
import json
import os
import pandas as pd
import pickle
import util

from ct import CTSeriesInt as CTSeries
from tqdm import tqdm


def convert(args):
    if os.path.exists(args.output_dir):
        raise ValueError('Output directory {} already exists. Converted dirs should be combined manually.'
                         .format(args.output_dir))
    os.makedirs(args.output_dir)
    directory = args.input_dir
    series_list = []
    subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]

    for study_dir in subfolders:
        study_name = study_dir.split("/")[-1]

        # Load info from file system
        try:
            series = CTSeries(study_name, study_dir)
        except RuntimeError as e:
            util.print_err('Error at {}: {}'.format(study_dir, e))
            continue
        except RuntimeWarning:
            # Ignore warnings (e.g. no slices found in a dir).
            continue
        """

        if series.series_number == contrast_series:
            if not args.include_unmasked and series.aneurysm_mask_path is None:
                continue
            mode = 'contrast'
        elif args.include_non_contrast and series.series_number == non_contrast_series:
            mode = 'non_contrast'
        else:
            # TODO: Only converting annotated contrast and non-contrast series for now.
            continue

        try:
            series.annotate(args.is_aneurysm, mode, annotation, require_aneurysm_range=args.require_range)
        except RuntimeWarning as w:
            util.print_err('Not converting series at {}:'.format(base_path), w)
            continue

        # Extend an existing series' aneurysm bounds if this is a duplicate annotation
        if args.is_aneurysm:
            found_duplicate = False
            for s in series_list:
                if s.study_name == series.study_name and s.series_number == series.series_number:
                    s.aneurysm_bounds = [min(s.aneurysm_bounds[0], series.aneurysm_bounds[0]),
                                         max(s.aneurysm_bounds[1], series.aneurysm_bounds[1])]
                    s.aneurysm_ranges.append(series.aneurysm_bounds)
                found_duplicate = True
            if found_duplicate:
                continue
        """

        series_list.append(series)

    # Write summary file for all series
    util.print_err('Collected {} series...'.format(len(series_list)))
    util.print_err('Dumping pickle file...')
    with open(os.path.join(args.output_dir, 'series_list.pkl'), 'wb') as pkl_file:
        pickle.dump(series_list, pkl_file)
    util.print_err('Dumping JSON file...')
    with open(os.path.join(args.output_dir, 'series_list.json'), 'w') as json_file:
        json.dump([dict(series) for series in series_list], json_file,
                  indent=4, sort_keys=True, default=util.json_encoder)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--input_dir', type=str, default="/mnt/bbq/intermountain/CTPA_RANDOM_DCM", \
                        help='Root directories holding CTA studies (e.g. "/data3/CTA/aneurysm_2003-06/").')
    parser.add_argument('--output_fmts', '-f', type=str, default='dcm,png,raw',
                        help='Format for output: "png" means window and write to PNG, \
                             "raw" means write raw Hounsfield Units to numpy int16 array file.')
    parser.add_argument('--csv_path', type=str, default='/data3/CTA/annotations/annotation.csv',
                        help='Path to CSV file of annotations.')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='Output directory for converted studies.')
    parser.add_argument('--init_id', type=int, default=1,
                        help='Initial ID for converted series (number 1-1000).')
    parser.add_argument('--max_series', type=int, default=-1,
                        help='Maximum number of series to convert. Defaults to -1 (no limit).')
    parser.add_argument('--require_range', action='store_true',
                        help='If flag is set, require aneurysm range annotation for aneurysm studies.')
    parser.add_argument('--include_unmasked', action='store_true',
                        help='If flag is set, include series without a corresponding mask.')
    parser.add_argument('--include_non_contrast', action='store_true',
                        help='If true, convert contrast and non-contrast studies. Else just convert contrast.')

    args_ = parser.parse_args()

    # Get modes to convert
    args_.output_fmts = util.args_to_list(args_.output_fmts, allow_empty=False, arg_type=str)
    if len(args_.output_fmts) > 3 or any([fmt not in ('dcm', 'png', 'raw') for fmt in args_.output_fmts]):
        raise ValueError('Invalid output formats: {}'.format(args_.output_fmts))

    print(json.dumps(vars(args_), indent=4, sort_keys=True))

    convert(args_)

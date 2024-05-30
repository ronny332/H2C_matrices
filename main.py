#!/usr/bin/env python3

import argparse
import logging as log
import os
import re

log.basicConfig(level=log.DEBUG, format='%(levelname)s - %(message)s')

error_number = 0

xml_head = """<?xml version="1.0"?>
<tSegment xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <q_scale_type>Nonlinear</q_scale_type>
  <intra_dc_precision>Dc10</intra_dc_precision>
  <qm_fixed>false</qm_fixed>
  <Name>{name}</Name>"""

xml_tail = '</tSegment>'


def create_matrix(hc_values, name=''):
    cce_matrix = re.split(r'[\n|\r\n]', xml_head.replace('{name}', name))

    for n, m_val in enumerate(hc_values):
        nam = 'Intra' if m_val < 64 else 'Inter'
        pos = n if n < 64 else n - 64
        cce_matrix.append(f'  <{nam}{pos}>{m_val}</{nam}{pos}>')

    cce_matrix.append(xml_tail)

    return '\r\n'.join(cce_matrix)


def error_out(msg):
    log.error(msg)
    quit(get_error_code())


def get_error_code():
    global error_number

    error_number += 1
    return error_number


def get_output_name(name):
    print(name)
    return name if "xml" in name else f"{name}.xml"


def is_uint8(value):
    return isinstance(value, int) and 0 <= value <= 255


def output_matrix(cce_matrix, output_file=''):
    if not output_file:
        print(cce_matrix)
    else:
        try:
            with open(output_file, 'w') as file:
                file.write(cce_matrix)
        except IOError as e:
            error_out(f'Unable to write file at "{file}"')


def parse_arguments():
    parser = argparse.ArgumentParser(description='HC Encoder matrices to CCE SP3 matrices converter')
    parser.add_argument('-i', '--input-file', type=str, help='Path to the matrix to read')
    parser.add_argument('-n', '--name', type=str, help='Name of newly created matrix')
    parser.add_argument('-o', '--output-file', type=str, help='Path to the matrix to write')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    if args.output_file:
        args.output_file = get_output_name(args.output_file)

    return args


def parse_input(file_path):
    if not file_path:
        error_out('input-file can\'t be empty')

    if not '.mtx' in file_path:
        error_out('only .mtx files are supported')

    if not (os.path.isfile(file_path) and os.access(file_path, os.R_OK)):
        error_out('input-file invalid or not readable')

    with open(file_path, 'r') as file:
        content = file.read()

        if len(content) == 0:
            error_out('input-file content can\'t be zero')

        matrix = re.sub(r'[\r\n]', '', content).strip().replace('  ', ' ').split(' ')

        if len(matrix) != 128:
            error_out(f'valid matrices have to have 128 values. the input has {len(matrix)} values')

        hc_matrix = []

        for m in matrix:
            try:
                num = int(m)
            except ValueError:
                error_out(f'got invalid matrix value {m}')

            if not is_uint8(num):
                error_out(f'matrix value not in spec: {m}. Should be of type uint8 (0 to 255)')

            hc_matrix.append(num)

        return hc_matrix


def main():
    args = parse_arguments()

    if args.verbose:
        log.info(f'parsing input from "{args.input_file}"')
    hc_values = parse_input(args.input_file)
    if args.verbose:
        log.info('creating new CCE compatible matrix')
    cce_matrix = create_matrix(hc_values, args.name if args.name else '')
    if args.verbose:
        log.info(f'output of newly generated matrix{'' if not args.output_file else f' to "{args.output_file}'}"')
    output_matrix(cce_matrix, args.output_file if "output_file" in args else "")


if __name__ == '__main__':
    main()

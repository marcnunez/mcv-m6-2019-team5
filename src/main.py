import argparse

from methods import optical_flow, stabilization
from optical_flow import block_matching, lucas_kanade

method_refs = {
    'optical_flow': optical_flow,
    'stabilization': stabilization,
}

optical_flow_refs = {
    'block_matching': BlockMatching,
    'lucas_kanade': lucas_kanade,
}


def main():
    parser = argparse.ArgumentParser(description='Search the picture passed in a picture database.')

    parser.add_argument('method', help='Method to use', choices=method_refs.keys())
    parser.add_argument('optical_flow', help='Optical flow method to use', choices=optical_flow_refs.keys())
    parser.add_argument('-d', '--debug', action='store_true', help='Show debug plots')

    args = parser.parse_args()

    method = method_refs.get(args.method)
    optical_flow_method = optical_flow_refs.get(args.tracking)

    method(optical_flow_method, debug=args.debug)


if __name__ == '__main__':
    main()

import argparse
import json
import sys
from pathlib import Path
from .api_generator import generate_api_infrastructure
from .config import load_project_config, write_default_project_config
from .feature_generator import generate_feature
from .platform_generator import generate_platform
from .schema import load_module_spec

def print_results(results):
    for path, status in results:
        print(f"[{status}] {path}")

def build_parser():
    parser = argparse.ArgumentParser(prog="react-clean-gen")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Generate the global platform and API infrastructure.")
    init.add_argument("target", type=Path)
    init.add_argument("--force", action="store_true")
    init.add_argument("--skip-api", action="store_true")
    gen = sub.add_parser("generate", help="Generate a feature only.")
    gen.add_argument("spec", type=Path)
    gen.add_argument("--target", type=Path, required=True)
    gen.add_argument("--force", action="store_true")
    show = sub.add_parser("show-config")
    show.add_argument("--target", type=Path, required=True)
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            target = args.target.resolve()
            target.mkdir(parents=True, exist_ok=True)
            config_path = write_default_project_config(target, force=args.force)
            config = load_project_config(target)  # one load, shared by init generators
            context = {"project_name": target.name or "react-app"}
            results = generate_platform(target, context, args.force)
            if not args.skip_api:
                results += generate_api_infrastructure(target, config["api"], args.force)
            print_results([(str(config_path), "present")] + results)
            print("\nNext: cd <target> && npm install && npm run dev")
            return 0
        if args.command == "generate":
            target = args.target.resolve()
            config = load_project_config(target)  # exactly one project-config load per module command
            spec = load_module_spec(args.spec.resolve())
            print_results(generate_feature(target, spec, config, args.force))
            print("\nFeature generated; platform and shared API files were not regenerated.")
            return 0
        if args.command == "show-config":
            print(json.dumps(load_project_config(args.target.resolve()), indent=2))
            return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1

if __name__ == "__main__":
    raise SystemExit(main())

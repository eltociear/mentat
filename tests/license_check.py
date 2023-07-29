import json
import subprocess

import fire

accepted_licenses = []


def main():
    licenses = json.loads(subprocess.check_output(["pip-licenses", "--format=json"]))
    for package in licenses:
        if "Name" not in package:
            raise ValueError(f"No name found for package {package}")
        elif "License" not in package:
            raise ValueError(f"License not found for package {package['Name']}")
        else:
            if package["License"] not in accepted_licenses:
                raise Exception(
                    f"Package {package['Name']} has license {package['License']}; if"
                    " this license is valid, add it to the accepted licenses list"
                )
    print("It's an older package list, sir, but it checks out")


if __name__ == "__main__":
    fire.Fire(main)
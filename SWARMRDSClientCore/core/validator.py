# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 15 January 2023
#
# Description: Validation system for generating the SWARM Firmware License
# =============================================================================
import machineid
import requests
import json
import sys
import os


def activate_license(license_key: str, account_id: str):
  machine_fingerprint = machineid.hashed_id('swarm-dev')
  validation = requests.post(
    "https://api.keygen.sh/v1/accounts/{}/licenses/actions/validate-key".format(account_id),
    headers={
      "Content-Type": "application/vnd.api+json",
      "Accept": "application/vnd.api+json"
    },
    data=json.dumps({
      "meta": {
        "scope": { "fingerprint": machine_fingerprint },
        "key": license_key
      }
    })
  ).json()

  if "errors" in validation:
    errs = validation["errors"]

    return False, "license validation failed: {}".format(
      map(lambda e: "{} - {}".format(e["title"], e["detail"]).lower(), errs)
    )

  # If the license is valid for the current machine, that means it has
  # already been activated. We can return early.
  if validation["meta"]["valid"]:
    return True, "license has already been activated on this machine"

  # Otherwise, we need to determine why the current license is not valid,
  # because in our case it may be invalid because another machine has
  # already been activated, or it may be invalid because it doesn't
  # have any activated machines associated with it yet and in that case
  # we'll need to activate one.
  validation_code = validation["meta"]["code"]
  activation_is_required = validation_code == 'FINGERPRINT_SCOPE_MISMATCH' or \
                           validation_code == 'NO_MACHINES' or \
                           validation_code == 'NO_MACHINE'

  if not activation_is_required:
    return False, "license {}".format(validation["meta"]["detail"])

  # If we've gotten this far, then our license has not been activated yet,
  # so we should go ahead and activate the current machine.
  activation = requests.post(
    "https://api.keygen.sh/v1/accounts/{}/machines".format(account_id),
    headers={
      "Authorization": "License {}".format(license_key),
      "Content-Type": "application/vnd.api+json",
      "Accept": "application/vnd.api+json"
    },
    data=json.dumps({
      "data": {
        "type": "machines",
        "attributes": {
          "fingerprint": machine_fingerprint
        },
        "relationships": {
          "license": {
            "data": { "type": "licenses", "id": validation["data"]["id"] }
          }
        }
      }
    })
  ).json()

  # If we get back an error, our activation failed.
  if "errors" in activation:
    errs = activation["errors"]

    return False, "license activation failed: {}".format(
      ','.join(map(lambda e: "{} - {}".format(e["title"], e["detail"]).lower(), errs))
    )

  return True, "license activated"


if __name__ == "__main__":
# Run from the command line:
#   python main.py some_license_key
    with open("../settings/LicenseKey.json", "r") as file:
        license_key = json.load(file)
    license_key = license_key["Key"]
    status, msg = activate_license(license_key)

    print(status, msg)
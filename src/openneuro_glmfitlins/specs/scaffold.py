"""Starter subjects/contrasts files written by stage 1 for the user to edit."""

import json
from pathlib import Path


def create_subjects_json(subj_list, studyid, taskname, specpath):
    subjects_file_path = Path(specpath) / f'{studyid}-{taskname}_subjects.json'
    subjects_data = {
        "Subjects": subj_list
    }
    with open(subjects_file_path, 'w') as f:
        json.dump(subjects_data, f, indent=4)
    print(f"\t\tSaved subjects file for task {taskname} to {subjects_file_path}")


def create_gencontrast_json(studyid, taskname, specpath):
    contrasts_file_path = Path(specpath) / f'{studyid}-{taskname}_contrasts.json'
    contrasts_data = {
        "Contrasts": [
            {
                "Name": "AvB",
                "ConditionList": ["trial_type.a", "trial_type.b"],
                "Weights": [1, -1],
                "Test": "t"
            },
            {
                "Name": "FacesvPlaces",
                "ConditionList": ["trial_type.faces", "trial_type.places"],
                "Weights": [1, -1],
                "Test": "t"
            }
        ]
    }
    with open(contrasts_file_path, 'w') as f:
        json.dump(contrasts_data, f, indent=4)
    print(f"\t\tSaved contrasts file for task {taskname} to {contrasts_file_path}")

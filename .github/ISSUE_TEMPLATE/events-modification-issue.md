---
name: Events Modification Issue
about: Describe issue in an event fix (src/openneuro_glmfitlins/events/datasets/)
title: ''
labels: ''
assignees: ''

---

# Brief Summary of Issue

The primary issue is...

## OpenNeuro Study

`ID`: ds000000

## Modify Events Issue

The below code has the issue...

```python
def ds002033(eventspath: str, task: str):
    """
    Process event data for ds002033 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset (regulate, learning, training, prelearning)
    
    Returns:
    modified events files
    """

    if task == "ChangeDetection":
        eventsdat = pd.read_csv(eventspath, sep='\t')

        # trial_type exists or contains non-null values
        if 'trial_type' not in eventsdat.columns or eventsdat['trial_type'].isnull().all():
            print("Creating 'trial_type' with remapped values removing spaces and camelcase")

            remap_dict = {}
            for val in eventsdat['Condition Name'].dropna().unique():
                first = val.split()[0]
                snake = ''
                for i, char in enumerate(first):
                    if char.isupper() and i != 0 and not first[i-1].isupper():
                        snake += '_'
                    snake += char.lower()
                remap_dict[val] = snake

            eventsdat['trial_type'] = eventsdat['Condition Name'].map(remap_dict)

            print("Unique trial types:", eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("'trial_type' already exists or is partially filled. Skipping modification.")
            return None
```


## Recommended Fix

The below code addresses the above problem by...

```python
def ds002033(eventspath: str, task: str):
    """
    Process event data for ds002033 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    eventspath (str): path to the events .tsv file
    task (str): task name for dataset (regulate, learning, training, prelearning)
    
    Returns:
    modified events files
    """

```

## Improvements from this modification

This modification improve [..] in the resulting events files

#!/usr/bin/python

''' A script to compile a tagging sheet from a RASA rule file. There rule
    file has to have a valid yaml format.

    How it works:
    1) provide a yaml file containing a list of RASA rules

    2) within the outer for-loop for i, line in enumerate(rule_contents)
    use if-statements to extract values of the target elements (rule, slots,
    intents, actions (utter)) identified in a line.

    3) compile a lists as datframe columns and save it to an Excel file.

     '''

import argparse
import re
import os
from typing_extensions import dataclass_transform
import pandas as pd
from tqdm import tqdm

def parse_rules(rule_contents):

    rule_line = re.compile('- rule:(.*?)')
    slot_line = re.compile('- slot_was_set:')
    intent_line = re.compile('- intent:(.*?)')
    response_line = re.compile('- action:(.*?)')
    steps_line = re.compile('steps:')

    rule_column = []
    intent_column = []
    slot_column = []
    entity_column = []
    response_column = []
    
    rule_column_long = []
    intent_column_long = []
    slot_column_long = []
    entity_column_long = []
    response_column_long = []

    entity_list = []
    slot_list = []

    rule_active = 0
    response_active = 0
    
    for i, line in enumerate(tqdm(rule_contents)):

        if rule_active:
            if re.search(slot_line, line):
                j = i + 1
                slots_active = 1
                while slots_active:
                    if (re.search(slot_line, rule_contents[j+1]) or  
                        re.search(steps_line, rule_contents[j+1])):
                        slots_active = 0
                    slot, entity = rule_contents[j].lower().split(':')
                    # some slot names are using dashes
                    try:
                        _, slot = slot.split('-')
                    except:
                        breakpoint()
                    slot = slot.strip()
                    entity = entity.strip()
                    slot_list.append(slot)
                    entity_list.append(entity)
                    j += 1

            if re.search(intent_line, line):
                _, intent = line.lower().split(':')
                intent = intent.strip()
        
            if re.search(response_line, line):
                _, response = line.lower().split(':')
                response = response.strip()

                # append the extracted elements to column lists
                # for optimization
                rule_column.append(rule)
                intent_column.append(intent)
                response_column.append(response)

                if len(slot_list) > 1:
                    slot_column.append(', '.join(slot_list))
                else:
                    slot_column.append(''.join(slot_list))

                if len(entity_list) > 1:
                    entity_column.append(', '.join(entity_list))
                else:
                    entity_column.append(''.join(entity_list))
                
                # append the extracted elements to column lists
                # for validation
                # all follow-up responses are appended here
                response_active = 1
                
                j = i
                counter = 1
                while response_active:

                    # to account for the end of the file
                    if j+1 == len(rule_contents):
                        response_active = 0
                        continue

                    if re.search(rule_line, rule_contents[j+1]):
                        response_active = 0

                    _, response = rule_contents[j].lower().split(':')
                    response = response.strip()
                    j += 1

                    if counter == 1:
                        rule_column_long.append(rule)
                        intent_column_long.append(intent)
                        response_column_long.append(response)
                        
                        if len(slot_list) > 1:
                            slot_column_long.append(', '.join(slot_list))
                        else:
                            slot_column_long.append(''.join(slot_list))

                        if len(entity_list) > 1:
                            entity_column_long.append(', '.join(entity_list))
                        else:
                            entity_column_long.append(''.join(entity_list))
                    else:
                        rule_column_long.append(rule)
                        intent_column_long.append('')
                        response_column_long.append(response)
                        slot_column_long.append('')
                        entity_column_long.append('')
                    counter += 1

                # reset variables for the loop
                rule = ''
                response = ''
                intent = ''
                entity_list = []
                slot_list = []

                # rule was rased
                rule_active = 0
        else:
            if re.search(rule_line, line):
                _, rule = line.lower().split(':')
                rule = rule.strip()
                rule_active = 1

    # create data frames from lists
    data_frame_validation = pd.DataFrame(columns = ['rule', 'utter', 'utter_indom', 'intent', 'intent_indom',
                'entities', 'entities_indom', 'slots', 'slots_indom', 'comments'])

    data_frame_validation['rule']  = rule_column_long
    data_frame_validation['utter']  = response_column_long
    data_frame_validation['utter_indom']  = [0] * len(rule_column_long)
    data_frame_validation['intent']  = intent_column_long
    data_frame_validation['intent_indom']  = [0] * len(rule_column_long)
    data_frame_validation['entities']  = entity_column_long
    data_frame_validation['entities_indom']  = [0] * len(rule_column_long)
    data_frame_validation['slots']  = slot_column_long
    data_frame_validation['slots_indom']  = [0] * len(rule_column_long)
    data_frame_validation['comments']  = [''] * len(rule_column_long)

    data_frame_optimization = pd.DataFrame(columns = ['rule', 'utter', 'intent', 'intent_inlu', 'entities',
                'entities_inlu', 'keywords', 'examples', 'comments'])
    
    data_frame_optimization['rule']  = rule_column
    data_frame_optimization['utter']  = response_column
    data_frame_optimization['intent']  = intent_column
    data_frame_optimization['intent_inlu']  = [0] * len(rule_column)
    data_frame_optimization['entities']  = entity_column
    data_frame_optimization['entities_inlu']  = [0] * len(rule_column)
    data_frame_optimization['keywords']  = [''] * len(rule_column)
    data_frame_optimization['examples']  = [''] * len(rule_column)
    data_frame_optimization['comments']  = [''] * len(rule_column)
    
    return data_frame_validation, data_frame_optimization

def write_tagging_sheet(tagging_sheet_path, data_frame_validation, data_frame_optimization):

    writer = pd.ExcelWriter(tagging_sheet_path, engine = 'openpyxl')
    data_frame_validation.to_excel(writer, sheet_name = 'validation', index = False)
    data_frame_optimization.to_excel(writer, sheet_name = 'nlu_optimization', index = False)

    writer.save()

def main(args):

    ''' The file_location is a file containing a rule list, read its contents and
        parse single elements to a dataframe. '''

    file_location = args.file

    if os.path.isfile(file_location):
        
        with open(file_location, 'r', encoding='utf-8') as f:
            rule_contents = f.readlines()
        
        data_frame_validation, data_frame_optimization = parse_rules(rule_contents)
        rules_file_path, _ = os.path.split(file_location)
        tagging_sheet_path = os.path.join(rules_file_path, 'bafza_bot.xlsx')
        
        write_tagging_sheet(tagging_sheet_path, data_frame_validation, data_frame_optimization)

    else:
        print('Given file not found. Check for any typos in the path/file name.')

if __name__ == "__main__":

    ''' Parse rules YAML. '''

    parser = argparse.ArgumentParser(description='Parse rules into a \
        tagging sheet.')

    parser.add_argument('-f', '--file', required=True, help="YAML \
        file containing the rules.")

    args = parser.parse_args()

    main(args)

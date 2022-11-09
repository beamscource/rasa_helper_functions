
# %%
import pandas as pd
import seaborn as sns
from tqdm import tqdm
import numpy as np
import re

# PARSING INTENT REPORT
# %%
def parse_intent_report(report_contents):
    intent_line = re.compile('  "(.*?)": {\n')
    precision_line = re.compile('    "precision": (.*?),\n')
    recall_line = re.compile('    "recall": (.*?),\n')
    f1_line = re.compile('    "f1-score": (.*?),\n')
    num_tested_line = re.compile('    "support": (.*?),\n')
    # confused_with_line_empty = re.compile('    "confused_with": {}\n')
    # confused_with_line = re.compile('"confused_with": {\n')
    intent_column = []
    precision_column = []
    recall_column = []
    f1_column = []
    num_tested_column = []
    for i, line in enumerate(tqdm(report_contents)):
        if re.search(intent_line, line):
            intent = re.findall(intent_line, line)[0]
            continue
        if re.search(precision_line, line):
            precision = "{:.2f}".format(float(re.findall(precision_line, line)[0]))
            precision = re.sub('\.', ',', precision)
            continue
        if re.search(recall_line, line):
            recall = "{:.2f}".format(float(re.findall(recall_line, line)[0]))
            recall = re.sub('\.', ',', recall)
            continue
        if re.search(f1_line, line):
            f1 = "{:.2f}".format(float(re.findall(f1_line, line)[0]))
            f1 = re.sub('\.', ',', f1)
            continue
        if re.search(num_tested_line, line):
            num_tested = int(re.findall(num_tested_line, line)[0])
            # append the extracted elements to column lists
            # for the data frame
            intent_column.append(intent)
            num_tested_column.append(num_tested)
            f1_column.append(f1)
            precision_column.append(precision)
            recall_column.append(recall)
            continue
    # create data frame from lists
    data_frame = pd.DataFrame(columns = ['intent', 'num_test_examples', 'f1_score', 'precision', 'recall'])
    data_frame['intent']  = intent_column
    data_frame['num_test_examples']  = num_tested_column
    data_frame['f1_score']  = f1_column
    data_frame['precision']  = precision_column
    data_frame['recall']  = recall_column
    # data_frame['errors']  = error_column
    # data_frame['confused_with']  = confused_with_column
    return data_frame

# %%
report_file = '/home/eugen/projects/intent_report.json'
with open(report_file, 'r',  encoding='utf-8') as f:
    report_contents = f.readlines()

# %%
df_report = parse_intent_report(report_contents)

# PARSING INTENT ERRORS
# %%
def parse_intent_errors(error_contents):
    example_line = re.compile('    "text": "(.*?)",\n')
    intent_line = re.compile('    "intent": "(.*?)",\n')
    confused_with_line = re.compile('      "name": "(.*?)",\n')
    confidence_line = re.compile('      "confidence": (.*?)\n')
    intent_column = []
    example_column = []
    confused_with_column = []
    confidence_column = []
    for i, line in enumerate(tqdm(error_contents)):
        if re.search(example_line, line):
            example = re.findall(example_line, line)[0]
            continue
        if re.search(intent_line, line):
            intent = re.findall(intent_line, line)[0]
            continue
        if re.search(confused_with_line, line):
            confused_with = re.findall(confused_with_line, line)[0]
            continue
        if re.search(confidence_line, line):
            confidence = "{:.2f}".format(float(re.findall(confidence_line, line)[0]))
            confidence = re.sub('\.', ',', confidence)
            # append the extracted elements to column lists
            # for the data frame
            intent_column.append(intent)
            example_column.append(example)
            confused_with_column.append(confused_with)
            confidence_column.append(confidence)
            continue
    # create data frame from lists
    data_frame = pd.DataFrame(columns = ['intent', 'confused_example', 'confused_with', 'confidence'])
    data_frame['intent']  = intent_column
    data_frame['confused_example']  = example_column
    data_frame['confused_with']  = confused_with_column
    data_frame['confidence']  = confidence_column
    return data_frame

# %%
errors_file = '/home/eugen/projects/intent_errors.json'
with open(errors_file, 'r',  encoding='utf-8') as f:
    error_contents = f.readlines()

# %%
df_errors = parse_intent_errors(error_contents)

# %%
# merge intent report + errors
df_intent = pd.merge(df_report, df_errors, on='intent', how='left')

# %%

writer = pd.ExcelWriter('/home/eugen/projects/intent_error_report.xlsx', engine = 'openpyxl')
df_intent_complete.to_excel(writer, sheet_name = 'intent_error_report', index = False)
writer.save()

# NLU CORPUS ANALYSIS

# PARSING NLU FILE

# %%
def parse_nlu(nlu_contents):
    intent_line = re.compile('- intent:(.*?)')
    example_line = re.compile('    - ')
    literal_line = re.compile('\[(.+?)]')
    entity_line = re.compile('\{(.+?)\}')
    intent_column = []
    entity_column = []
    literal_column = []
    example_column = []
    for i, line in enumerate(tqdm(nlu_contents)):
        if re.search(intent_line, line):
            _, intent = line.lower().split(':')
            intent = intent.strip()
            continue
        if re.search(example_line, line):
            literal_list = []
            entity_list = []
            _, example = line.split('- ', 1)
            literals_tag = re.findall(literal_line, line)
            for literal in literals_tag:
                literal = re.sub('[\[\]]', '', literal)
                literal_list.append(literal)
            annotations_tags = re.findall(entity_line, line)
            for annotation in annotations_tags:
                entity = re.findall('"entity": "(.*?)"', annotation)
                # _, entity = entity.split(':', 1)
                # entity = re.sub('[\[\]:"\' \{\}]', '', entity)
                entity_list.append(entity[0])
            if len(literal_list) != len(entity_list):
                breakpoint()
            # append the extracted elements to column lists
            # for the data frame
            intent_column.extend([intent]*len(entity_list))
            # clean example from annotations ?
            example = re.sub(entity_line, '', example)
            example = re.sub('[\[\]\n]', '', example)
            example_column.extend([example]*len(entity_list))
            entity_column.extend(entity_list)
            literal_column.extend(literal_list)
    # create data frame from lists
    data_frame = pd.DataFrame(columns = ['intent', 'entity', 'literal', 'example'])
    data_frame['intent']  = intent_column
    data_frame['entity']  = entity_column
    data_frame['literal']  = literal_column
    data_frame['example']  = example_column
    return data_frame

# %%
nlu_file = '/home/eugen/projects/nlu.yml'

with open(nlu_file, 'r',  encoding='utf-8') as f:
    nlu_contents = f.readlines()
# %%
df_nlu = parse_nlu(nlu_contents)
# line 3112 in nlu.yml from ubitec has an annotation error

# %%
def write_tagging_sheet(tagging_sheet_path, data_frame):

    writer = pd.ExcelWriter(tagging_sheet_path, engine = 'openpyxl')
    data_frame.to_excel(writer, sheet_name = 'nlu_data', index = False)

    writer.save()

# %%
# filter the data frame based on list of employed entities

entities_rules = [
    '',
]

df_filtered = df_nlu[df_nlu['entity'].isin(entities_rules)]

# %%
df_nlu.shape[0]
df_filtered.shape[0]

# %%
# 1. issue: unbalanced number of examples per intent
examples_per_intent_count_sorted = df_nlu.groupby(['intent'])['example'].nunique().reset_index(name='count').sort_values(['count'], ascending=False)
examples_per_intent_count = df_nlu.groupby(['intent'])['example'].nunique().reset_index(name="total_examples")
df_intent_complete = pd.merge(examples_per_intent_count, df_intent, on='intent', how='left')

plot = sns.distplot(examples_per_intent_count, norm_hist=False, kde=False,  bins=60)
plot.set(xlabel='Example count per intent', ylabel='Frequency')
# %%
# 2. issue: unbalanced number of entities per intent (which are unsed anyway)
# only 35 entities are currenty used whereas 75 are defined in the domain
entity_per_intent_counts_sorted = df_nlu.groupby(['intent'])['entity'].nunique().reset_index(name='count').sort_values(['count'], ascending=False)
entity_per_intent_counts = df_nlu.groupby(['intent'])['entity'].nunique()
#df.groupby(['intent'])['entity'].count()

# plot intent count distribution
plot = sns.distplot(entity_per_intent_counts, norm_hist=False, kde=False,  bins=60)
plot.set(xlabel='Entity count per intent', ylabel='Frequency')

# %%
# 3. unbalanced and very low number of literals per entity category
literal_per_entity_count = df_nlu.groupby(['entity'])['literal'].value_counts()
# counting literals only for entities that are used in dialogue rules
literal_per_entity_count_rules = df_filtered.groupby(['entity'])['literal'].value_counts()


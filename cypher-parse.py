import re
import pandas as pd
import numpy as np
from itertools import product

# Known shortcoming; for the * symbol, it would be much better to check for the length of the variable relationship.
def cleanup_arrowheads(left, right):
    if left[0] in ['<','>']:
        left = left[1:]
    if right[len(right)-1] in ['<','>']:
        right = right[:-1]
    return left, right


def correct_cypher(row):
    schema_str = row['schema']
    cypher_statement = row['statement']
    correct_statement = row['correct_query']

    new_cypher = cypher_statement

    node_pattern = r'\(([\w]+)?((?::`?(?:[\w$]+\s*)+`?)+)?(\s{(.*?)})?\)'
    arrow_pattern = r'<?-(\[([\w]+)?((?::?\|?[\w$`!]+)+)?(\s{(.*?)})?\*?([\d.*]+)?\])?->?'
    sp = r'\s*' # keyboard space pattern

    rel_pattern = node_pattern+r'(?:'+sp+arrow_pattern+sp+node_pattern+r')+'

    relationships = []
    matches = list(re.finditer(rel_pattern, cypher_statement))
    if matches:
        for match in matches:
            relationship = match if isinstance(match, str) else match.group()

            if relationship.count('-') > 2:
                relation_bits = relationship.split('-')
                # Remove potential heading or trailing arrow directions left from cut
                left, right = cleanup_arrowheads(relation_bits[0], relation_bits[2])
                middle = relation_bits[1]
                relationship = left + '-' + middle + '-' + right

                # Add the rest of the relationship to matches for later processing:
                i = 3
                while i<len(relation_bits):
                    # Remove potential heading or trailing arrow directions left from cut
                    left, right = cleanup_arrowheads(relation_bits[i-1], relation_bits[i+1])
                    middle = relation_bits[i]
                    matches.append(left + '-' + middle + '-' + right)
                    i += 2

            print(relationship)
            relationships.append(relationship)

            extracted_data = extract_data(relationship, node_pattern, arrow_pattern, cypher_statement)
            schemas = extract_schemas(schema_str)

            l_type_known = extracted_data['l_node']['type'] != []
            r_type_known = extracted_data['r_node']['type'] != []
            rel_type_known = extracted_data['arrow']['type'] != []
            direction = extracted_data['arrow']['direction']

            if direction == 0:
                print('No direction given - no problem for matching.')
            else:
                if l_type_known and r_type_known and rel_type_known:
                    if direction == 1:
                        given = list(product(
                            extracted_data['l_node']['type'],
                            extracted_data['arrow']['type'],
                            extracted_data['r_node']['type']
                        ))
                    else:
                        given = list(product(
                            extracted_data['r_node']['type'],
                            extracted_data['arrow']['type'],
                            extracted_data['l_node']['type']
                        ))
                    if any(item in schemas for item in given):
                        print('Relationship in schema!')
                    else:
                        if '*' not in extracted_data['arrow']['label']:
                            print('Needs fixing.')
                            print(extracted_data['arrow']['label'])
                            new_rel = fix_rel(
                                extracted_data['l_node']['node'],
                                extracted_data['arrow']['arrow'],
                                extracted_data['r_node']['node'],
                                direction
                            )
                            new_cypher = new_cypher.replace(relationship, new_rel)

                # Needs cases where other ways are known
                elif l_type_known and rel_type_known:
                    in_schema = False
                    if direction == 1:
                        for schema in schemas:
                            if schema[0] in extracted_data['l_node']['type'] and schema[1] in extracted_data['arrow']['type']:
                                in_schema = True

                    if direction == -1:
                        for schema in schemas:
                            if schema[2] in extracted_data['l_node']['type'] and schema[1] in extracted_data['arrow']['type']:
                                in_schema = True
                    if in_schema:
                        print('Relationship in schema!')
                    else:
                        if '*' not in extracted_data['arrow']['label']:
                            print('Needs fixing.')
                            print(extracted_data['arrow']['label'])
                            new_rel = fix_rel(
                                extracted_data['l_node']['node'],
                                extracted_data['arrow']['arrow'],
                                extracted_data['r_node']['node'],
                                direction
                            )
                            new_cypher = new_cypher.replace(relationship, new_rel)

                elif r_type_known and rel_type_known:
                    in_schema = False
                    if direction == 1:
                        for schema in schemas:
                            if schema[2] in extracted_data['r_node']['type'] and schema[1] in extracted_data['arrow']['type']:
                                in_schema = True

                    if direction == -1:
                        for schema in schemas:
                            if schema[0] in extracted_data['r_node']['type'] and schema[1] in extracted_data['arrow']['type']:
                                in_schema = True
                    if in_schema:
                        print('Relationship in schema!')
                    else:
                        if '*' not in extracted_data['arrow']['label']:
                            print('Needs fixing.')
                            print(extracted_data['arrow']['label'])
                            new_rel = fix_rel(
                                extracted_data['l_node']['node'],
                                extracted_data['arrow']['arrow'],
                                extracted_data['r_node']['node'],
                                direction
                            )
                            new_cypher = new_cypher.replace(relationship, new_rel)

                elif l_type_known and r_type_known:
                    in_schema = False
                    if direction == 1:
                        for schema in schemas:
                            if schema[0] in extracted_data['l_node']['type'] and schema[2] in extracted_data['r_node']['type']:
                                in_schema = True
                    if direction == -1:
                        for schema in schemas:
                            if schema[2] in extracted_data['l_node']['type'] and schema[0] in extracted_data['r_node']['type']:
                                in_schema = True
                    if in_schema:
                        print('Relationship in schema!')
                    else:
                        if '*' not in extracted_data['arrow']['label']:
                            print('Needs fixing.')
                            print(extracted_data['arrow']['label'])
                            new_rel = fix_rel(
                                extracted_data['l_node']['node'],
                                extracted_data['arrow']['arrow'],
                                extracted_data['r_node']['node'],
                                direction
                            )
                            new_cypher = new_cypher.replace(relationship, new_rel)
                else:
                    print('Not enough information.')


    print()
    return new_cypher


def fix_rel(l_node, arrow, r_node, direction):
    if direction == 1:
        return l_node + '<' + arrow[:-1] + r_node
    else:
        return l_node + arrow[1:] + '>' + r_node


def extract_schemas(schema_str):
    schema_pattern = r'\(.*?\)'
    schemas_matches = list(re.finditer(schema_pattern, schema_str))
    schemas = []
    if len(schemas_matches) != 0:
        for match in schemas_matches:
            # Remove parentheses
            match = match.group()[1:-1]
            # Then split and add schema
            schema_bits = match.split(', ')
            schemas.append(tuple(schema_bits))
    return schemas


def extract_data(relationship, node_pattern, arrow_pattern, statement):
    extracted_data = {}
    nodes = list(re.finditer(node_pattern, relationship))
    extracted_data['relationship'] = relationship
    extracted_data['l_node'] = {
        'node': nodes[0].group(),
        'label': extract_node_label(nodes[0].group(), statement)
    }
    extracted_data['arrow'] = {
        'arrow': re.search(arrow_pattern, relationship).group()

    }
    extracted_data['r_node'] = {
        'node': nodes[1].group(),
        'label': extract_node_label(nodes[1].group(), statement)
    }
    extracted_data['arrow']['label'], extracted_data['arrow']['direction'] = extract_rel_label(extracted_data['arrow']['arrow'], statement)
    extracted_data['arrow']['type'] = get_type(extracted_data['arrow']['label'])
    extracted_data['l_node']['type'] = get_type(extracted_data['l_node']['label'])
    extracted_data['r_node']['type'] = get_type(extracted_data['r_node']['label'])
    return extracted_data


def detect_arrow_direction(arrow):
    if arrow[0] == '<' and arrow[-1] != '>':
        return -1
    elif arrow[0] != '<' and arrow[-1] == '>':
        return 1
    else:
        return 0


def get_type(labels):
    types = []
    for label in labels:
        typ = label[1:]
        if typ[0] == '!':
            typ = typ[1:]
        if len(typ.split('*')) != 1:
            typ = typ.split('*')[0]
        if typ[0] == '`':
            typ = typ[1:-1]
        types.append(typ)
    return types


# TODO: if a relationship type is not specified, just like the nodes, look for the type elsewhere
def extract_rel_label(arrow, cypher_statement):
    direction = detect_arrow_direction(arrow)
    type_pattern = r'(:|\|)!?(([\w$]+)|(`(.*?)`))([\d.*]+)?'

    def group(res):
        type = res.group()
        return type
    # if there is a ':' symbol, the node type is in the arrow; if not, it should be somewhere else in the cypher.
    if ':' in arrow:
        return list(map(group, list(re.finditer(type_pattern, arrow)))), direction
    else:
        return [], direction


def extract_node_label(node, cypher_statement):
    type_pattern = r'(?::[\w$]+)|(?::`(?:[\w$]+\s*)+`)'

    def group(res):
        type = res.group()
        return type
    if ':' in node:
        return list(map(group, list(re.finditer(type_pattern, node))))
    elif node == '()':
        return []
    else:
        node_name = node[1:-1]
        specific_node_pattern = '\('+node_name+'((?::`?(?:[\w$]+\s*)+`?)+)?(\s{(.*?)})?\)'
        matches = list(re.finditer(specific_node_pattern, cypher_statement))
        if len(matches) != 0:
            match = str(matches[0].group())
            if len(match.split(':')) != 1:
                return list(map(group, list(re.finditer(type_pattern, match))))
            else:
                return []

        else:
            return []


def main():
    test_dataset = pd.read_csv('examples.csv')
    test_dataset['attempt'] = test_dataset[['statement','schema', 'correct_query']].apply(lambda x: correct_cypher(x), axis=1)
    test_dataset['verification'] = test_dataset[['attempt', 'correct_query']].apply(lambda y: y['attempt'] == y['correct_query'], axis=1)
    test_dataset.to_csv('attempts.csv', index=False)


if __name__ == '__main__':
    main()

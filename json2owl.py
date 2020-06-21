"""
@author: Li Xi
@file: json2owl.py
@time: 2020/6/20 21:04
@desc:

transfer json file to owl file based on owl template

Content to be added:
{declaration_events}
{declaration_sub_events}
{declaration_event_relations}
{declaration_sub_event_relations}
{declaration_is_sub_relations}
{declaration_event_info}
{declaration_relation_info}
{event_individual}
{sub_event_individual}
{event_relations_individual}
{sub_event_relations_individual}
{is_sub_relations_individual}
{event_info_individual}
{relation_info_individual}

"""

import json
import os

from owl_helper import *


def get_event_correspond(sub_event_ids, json_content):
    """
    use sub event relations to get events those corresponded
    :param sub_event_ids:
    :param json_content:
    :return: a dict
    Exx is event and exx is sub event:
    {
        "E01": [e01],
        "E02': [e02, e03],
        "E03": [e04]
    }
    """
    # get event cluster (并列 -> same)
    # 思路：等于-1时表示自己为根节点，不等于-1时，值指向根节点的事件id，因此每个根节点代表一个event cluster
    same_event_list = {x: -1 for x in sub_event_ids}
    for from_e in json_content:
        for to_e in json_content[from_e]:
            label = json_content[from_e][to_e]
            if label == '并列关系':
                tmp_from = from_e
                # 循环找根节点
                while same_event_list[tmp_from] != -1:
                    tmp_from = same_event_list[tmp_from]
                same_event_list[to_e] = tmp_from
    # 整理event cluster结构
    event_cluster = {e: [] for e in sub_event_ids if same_event_list[e] == -1}
    for e in sub_event_ids:
        if same_event_list[e] != -1:
            event_cluster[same_event_list[e]].append(e)
    # 按格式输出
    event = {}
    event_index = 0
    for e in event_cluster:
        event_index += 1
        event_label = "E" + str(event_index).zfill(2)
        event[event_label] = [e] + event_cluster[e]

    return event


def get_event(event_correspond, sub_events):
    """
    根据event_correspond和sub_events获取event信息
    根据event_correspond获取event对应的sub event信息（有多个时选第一个）
    抽取sub event的三元组信息作为event的信息
    :param event_correspond:
    :param sub_events:
    :return: a dict
    {
        'E01': {
            "has_trigger":,
            'has_trigger_object':,
            'has_trigger_subject'
        }, ......
    }
    """
    ret = {}
    for event in event_correspond:
        sub = event_correspond[event][0]
        keys = ['has_trigger', 'has_trigger_object', 'has_trigger_subject']
        ret[event] = {}
        for k in keys:
            if k in sub_events[sub]:
                ret[event][k] = sub_events[sub][k]
    return ret


def get_sub_event(json_content):
    """
    把json格式的事件信息选取需要的部分作为sub event 信息
    主要用于整理sub event id和去除空白信息
    :param json_content:
    :return:
    """
    ret = {}
    for sentence in json_content:
        for event in sentence["event_graph"]:
            ret[event["child_event_id"]] = {}
            for k in event:
                if k != "child_event_id" and event[k] != "":
                    ret[event["child_event_id"]]["has_{}".format(k)] = event[k]
    return ret


def get_event_relation(event_correspond, json_content):
    """
    获取event之间的relation，在owl中用"R-xx-xx"表示
    将event id转为sub event id （有多个时选取第一个）获取对应relation
    也可以理解为，从sub event relation中去除"冗余sub event"对应的relation
    （event对应多个sub event时，只保留第一个sub event 对应的relation信息）
    :param event_correspond:
    :param json_content:
    :return: 两种格式的dict，一个用于表示relation数据结构，另一个relation属性（event的属性）
    第一种：relation数据结构，在relation属性定义中使用
    {
        "R-01-02": {
            'has_label': "xx关系"
            'has_to': E02
        }, .....
    }

    第二种：relation属性（event的属性）,在event属性定义中使用
    {
        'E01': [ ('is_from_of', 'R-01-02'),
                 ('is_from_of', 'R-01-03'),
                 .......],
        ........
    }
    """

    event_relations = {}
    event_relations_for_event = {}

    event_to_sub = {e: event_correspond[e][0] for e in event_correspond}
    sub_to_event = {event_correspond[e][0]: e for e in event_correspond}  # 可能没有

    # 遍历每个event
    for event in event_correspond:
        event_relations_for_event[event] = []
        # 获取每个event 关联的第一个sub event（有多个时）
        sub_event = event_to_sub[event]
        # 有对应relation的时候
        if sub_event in json_content:
            for to_e in json_content[sub_event]:
                if to_e in sub_to_event:
                    label = json_content[sub_event][to_e]
                    if label == '并列关系':
                        continue
                    label = label if label == '因果关系' else '时序关系'

                    # 有对应的subevent to event，即from to都在event中
                    from_event = sub_to_event[sub_event]
                    to_event = sub_to_event[to_e]
                    relation_id = "R-{}-{}".format(from_event[1:], to_event[1:])
                    event_relations[relation_id] = {
                        'has_label': label,
                        'has_to': to_event
                    }

                    event_relations_for_event[event].append(
                        ('is_from_of', relation_id)
                    )

    return event_relations, event_relations_for_event


def get_sub_relation(json_content):
    """
    获取sub event 之间的对应关系
    :param json_content:
    :return: 格式参考 get_event_relation
    """
    sub_relation = {}
    relation_for_event = {}

    for from_e in json_content:
        relation_for_event[from_e] = []
        for to_e in json_content[from_e]:
            label = json_content[from_e][to_e]
            if label == '并列关系':
                continue
            label = label if label == '因果关系' else '时序关系'
            relation_id = "r-{}-{}".format(from_e[1:], to_e[1:])

            sub_relation[relation_id] = {
                'has_label': label,
                'has_to': to_e
            }
            relation_for_event[from_e].append(
                ('is_from_of', relation_id)
            )
    return sub_relation, relation_for_event


def get_is_sub_relation(event_correspond):
    """
    获取event和sub event的对应关系
    :param event_correspond:
    :return: 格式参考 get_event_relation
    """
    is_sub_relation = {}
    is_sub_relation_for_event = {}
    for event in event_correspond:
        is_sub_relation_for_event[event] = []
        for sub_event in event_correspond[event]:
            relation_id = 's-{}-{}'.format(event[1:], sub_event[1:])
            is_sub_relation[relation_id] = {
                'has_label': '子事件关系 ',
                'has_to': sub_event
            }
            is_sub_relation_for_event[event].append(
                ('is_from_of', relation_id)
            )
    return is_sub_relation, is_sub_relation_for_event


def get_event_info(json_content):
    """
    从json文件中读取事件属性并去重
    :param json_content:
    :return: a list of property
    """
    event_info = set()
    for sentence in json_content:
        for event in sentence["event_graph"]:
            for k in event:
                if k != "child_event_id" and event[k].strip() != "":
                    event_info.add(event[k])
    return list(event_info)


def get_event_individual(event, event_relations, is_sub_relations):
    """
    输出event_individual信息
    包含：
        对象声明
        event相关属性定义
        event relation相关属性定义（R）
        is sub event relation相关属性定义（s）
    :param event:
    :param event_relations:
    :param is_sub_relations:
    :return: a list of command
    """

    ret = []
    for k in event:
        ret.append(add_class_assertion("event", k))
        for item_k in event[k]:
            ret.append(add_object_property_assertion(item_k, k, event[k][item_k]))
        if k in event_relations:
            for item in event_relations[k]:
                ret.append(add_object_property_assertion(item[0], k, item[1]))
        if k in is_sub_relations:
            for item in is_sub_relations[k]:
                ret.append(add_object_property_assertion(item[0], k, item[1]))
    return ret


def get_sub_event_individual(sub_events, sub_event_relations):
    """
    输出event_relations_individual信息
    包含：
        对象声明
        event相关属性定义
        sub event relation相关属性定义（r）
    :param sub_events:
    :param sub_event_relations:
    :return: a list of command
    """
    ret = []
    for k in sub_events:
        ret.append(add_class_assertion("sub_event", k))
        for item_k in sub_events[k]:
            ret.append(add_object_property_assertion(item_k, k, sub_events[k][item_k]))
        if k in sub_event_relations:
            for item in sub_event_relations[k]:
                ret.append(add_object_property_assertion(item[0], k, item[1]))
    return ret


def get_event_relations_individual(event_relations):
    """
    输出event_relations_individual信息
    :param event_relations:
    :return: a list of command
    """
    ret = []
    for k in event_relations:
        ret.append(add_class_assertion("relation", k))
        for item_k in event_relations[k]:
            ret.append(add_object_property_assertion(item_k, k, event_relations[k][item_k]))
    return ret


def get_sub_event_relations_individual(sub_event_relations):
    """
    输出sub_event_relations_individual信息
    :param sub_event_relations:
    :return: a list of command
    """
    ret = []
    for k in sub_event_relations:
        ret.append(add_class_assertion("relation", k))
        for item_k in sub_event_relations[k]:
            ret.append(add_object_property_assertion(item_k, k, sub_event_relations[k][item_k]))
    return ret


def get_is_sub_relations_individual(is_sub_relations):
    """
    输出is_sub_relations_individual信息
    :param is_sub_relations:
    :return: a list of command
    """
    ret = []
    for k in is_sub_relations:
        ret.append(add_class_assertion('relation', k))
        for item_k in is_sub_relations[k]:
            ret.append(add_object_property_assertion(item_k, k, is_sub_relations[k][item_k]))
    return ret


def solve(json_file_path):
    # read json file
    with open(os.path.join('json', json_file_path), 'r', encoding='utf-8') as f:
        json_content = json.loads(f.read())

    sub_events = get_sub_event(json_content['event_element'])
    event_correspond = get_event_correspond(sub_events.keys(), json_content['event_relation'])
    sub_event_relations, sub_event_relation_for_event = get_sub_relation(json_content['event_relation'])
    is_sub_relations, is_sub_relations_for_event = get_is_sub_relation(event_correspond)
    event_info = get_event_info(json_content['event_element'])
    relation_info = ["时序关系", "子事件关系", "因果关系"]
    events = get_event(event_correspond, sub_events)
    event_relations, event_relations_for_event = get_event_relation(event_correspond, json_content['event_relation'])

    declaration_events = "\n".join([add_declaration_named_individual(item) for item in event_correspond.keys()])
    declaration_sub_events = "\n".join([add_declaration_named_individual(item) for item in sub_events.keys()])
    declaration_event_relations = "\n".join([add_declaration_named_individual(item) for item in event_relations.keys()])
    declaration_sub_event_relations = "\n".join(
        [add_declaration_named_individual(item) for item in sub_event_relations.keys()])
    declaration_is_sub_relations = "\n".join(
        [add_declaration_named_individual(item) for item in is_sub_relations.keys()])
    declaration_event_info = "\n".join([add_declaration_named_individual(item) for item in event_info])
    declaration_relation_info = "\n".join([add_declaration_named_individual(item) for item in relation_info])

    event_individual = "\n".join(get_event_individual(events, event_relations_for_event, is_sub_relations_for_event))
    sub_event_individual = "\n".join(get_sub_event_individual(sub_events, sub_event_relation_for_event))
    event_relations_individual = "\n".join(get_event_relations_individual(event_relations))
    sub_event_relations_individual = "\n".join(get_sub_event_relations_individual(sub_event_relations))
    is_sub_relations_individual = "\n".join(get_is_sub_relations_individual(is_sub_relations))
    event_info_individual = "\n".join([add_class_assertion('event_info', item) for item in event_info])
    relation_info_individual = "\n".join([add_class_assertion('relation_info', item) for item in relation_info])

    # read template
    with open('template.owl', 'r', encoding='utf-8') as f:
        template = f.read()

    # format output
    output = template.format(
        declaration_events=declaration_events,
        declaration_sub_events=declaration_sub_events,
        declaration_event_relations=declaration_event_relations,
        declaration_sub_event_relations=declaration_sub_event_relations,
        declaration_is_sub_relations=declaration_is_sub_relations,
        declaration_event_info=declaration_event_info,
        declaration_relation_info=declaration_relation_info,
        event_individual=event_individual,
        sub_event_individual=sub_event_individual,
        event_relations_individual=event_relations_individual,
        sub_event_relations_individual=sub_event_relations_individual,
        is_sub_relations_individual=is_sub_relations_individual,
        event_info_individual=event_info_individual,
        relation_info_individual=relation_info_individual
    )

    # store owl file
    with open(os.path.join('owl', json_file_path[:-4] + 'owl'), 'w', encoding='utf-8') as f:
        f.write(output)


if __name__ == "__main__":
    # load json file

    files = os.listdir('json')
    for file_name in files:
        try:
            solve(file_name)
        except Exception as e:
            print(file_name)

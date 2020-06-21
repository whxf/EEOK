"""
@author: Li Xi
@file: owl_helper.py
@time: 2020/6/20 20:34
@desc:
make owl content
"""


def add_declaration_named_individual(individual_name):
    """

    :param individual_name: string type
    :return: a string of declaration_named_individual owl format content

    e.g. : Declaration(NamedIndividual(:死亡))
    """
    return "Declaration(NamedIndividual(:{individual_name}))".format(
        individual_name=individual_name)


def add_class_assertion(class_name, individual_name):
    """

    :param class_name: string type
    :param individual_name: string type
    :return: a string of class_assertion owl format content

    e.g. : ClassAssertion(:relation :s-04-05)
    """
    return "ClassAssertion(:{class_name} :{individual_name})".format(
        class_name=class_name,
        individual_name=individual_name)


def add_object_property_assertion(property_name, object_name, property_content):
    """

    :param property_name: string type
    :param object_name: string type
    :param property_content: string type
    :return: a string of object_property_assertion owl format content

    e.g. : ObjectPropertyAssertion(:has_label :s-04-05 :子事件关系)
    """
    return "ObjectPropertyAssertion(:{property_name} :{object_name} :{property_content})".format(
        property_name=property_name,
        object_name=object_name,
        property_content=property_content)


if __name__ == "__main__":
    # test
    print(add_declaration_named_individual("发生"))
    print(add_class_assertion("event", "e01"))
    print(add_object_property_assertion("has_trigger", "e01", "发生"))

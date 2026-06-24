def serialize_category(category):
    return {
        "category_id": category.id,
        "category_name": category.category_name,
    }


def serialize_term_list_item(term):
    return {
        "term_id": term.id,
        "term_name": term.term_name,
        "difficulty": term.difficulty,
        "description": term.description,
        "example_text": term.example_text,
        "category": serialize_category(term.category),
    }


def serialize_term_detail(term):
    data = serialize_term_list_item(term)
    data["example_text"] = term.example_text
    return data


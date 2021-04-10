import json
from dataclasses import dataclass
from typing import List


@dataclass
class Item:
    title: str
    url: str

    def as_dict(self):
        return {
            'title': self.title,
            'url': self.url
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


db_file = 'items.json'


def add_new_items(items: List[Item]):
    with open(db_file, 'r') as f:
        old_items = [Item.from_dict(data) for data in json.load(f)]
    new_items = [item for item in items if item not in old_items]
    with open(db_file, 'w') as f:
        json.dump(
            [item.as_dict() for item in old_items + new_items],
            f,
            indent=4
        )
    return new_items

# def get_new_items() -> List[Item]:
#     with open(db_file, 'r+') as f:
#         items = [Item.from_dict(data) for data in json.load(f)]
#         new_items = [item for item in items if not item.sent]
#         for item in new_items:¬
#             item.sent = True
#         json.dump([item.as_dict() for item in items], f)
#     return items

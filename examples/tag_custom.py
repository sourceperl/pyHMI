""" Add a data class to Tag to handle a dummy database export. """

from dataclasses import dataclass
from random import randint
import time
from typing import Optional
from pyHMI.Tag import Tag
from pyHMI.DS import GetCmd


def int_lottery():
    return randint(0, 100)


@dataclass
class DB:
    export: bool = False
    metric: str = ''


class eTag(Tag):
    def __init__(self, *args, db: Optional[DB] = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db = db if db else DB()


class Tags:
    def __init__(self) -> None:
        self.MY_TAG1 = eTag(1, src=GetCmd(int_lottery), db=DB(export=True, metric='my_metric1'))
        self.MY_TAG2 = eTag(2, src=GetCmd(int_lottery))
        self.MY_TAG3 = eTag(3, src=GetCmd(int_lottery), db=DB(export=True, metric='my_metric3'))
        self.MY_TAG4 = eTag(4, src=GetCmd(int_lottery))
        self.MY_TAG5 = eTag(5, src=GetCmd(int_lottery))


def main():
    # init
    tags = Tags()
    # export loop
    while True:
        for tag_name, tag in vars(tags).items():
            if isinstance(tag, eTag):
                if tag.db.export:
                    graphite_msg = f'{tag.db.metric} {tag.value}'
                    print(f'export {tag_name} graphite message is "{graphite_msg}"')
        time.sleep(1.0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

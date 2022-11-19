import os
import yaml

CATALOG_LIST_PATH = "/etc/yunohost/apps_catalog.yml"
assert os.path.exists(CATALOG_LIST_PATH), f"Catalog list yaml file '{CATALOG_LIST_PATH} does not exists"


def reset():
    with open(CATALOG_LIST_PATH, "w") as f:
        catalog_list = [{"id": "default", "url": "https://app.yunohost.org/default/"}]
        yaml.safe_dump(catalog_list, f, default_flow_style=False)


def add():
    with open(CATALOG_LIST_PATH) as f:
        catalog_list = yaml.load(f, Loader=yaml.FullLoader)
        ids = [catalog["id"] for catalog in catalog_list]
        if "custom" not in ids:
            catalog_list.append({"id": "custom", "url": None})
            with open(CATALOG_LIST_PATH, "w") as f:
                yaml.safe_dump(catalog_list, f, default_flow_style=False)


def override():
    with open(CATALOG_LIST_PATH, "w") as f:
        catalog_list = [{"id": "custom", "url": None}]
        yaml.safe_dump(catalog_list, f, default_flow_style=False)

import json
def save_chunks(chunks,path):
    """
    将chunks列表保存为JSON文件
    :param chunks: chunks
    :param path: 保存路径
    :return: None
    """
    with open(path,"w",encoding="utf-8") as f:
        json.dump(
            chunks,
            f,
            ensure_ascii=False,
            indent=2
        )

def load_chunks(path):
    """
    从JSON文件加载chunk列表
    :param path: JSON文件路径
    :return: chunks
    """
    with open(path,"r",encoding="utf-8") as f:
        return json.load(f)
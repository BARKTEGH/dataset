import json
import re
train_path = "E:\Project_all\数据集\SemEval2010_task8_all_data\SemEval2010_task8_training/TRAIN_FILE.TXT"
train_save_raw_path = "./tmp/train_raw.json"
train_save_path = "./tmp/train.json"

test_path = "E:\Project_all\数据集\SemEval2010_task8_all_data\SemEval2010_task8_testing_keys/TEST_FILE_FULL.TXT"
test_save_raw_path = "./tmp/test_raw.json"
test_save_path = "./tmp/test.json"


"""
输入文件格式为：
8001	"The most common <e1>audits</e1> were about <e2>waste</e2> and recycling."
Message-Topic(e1,e2)
Comment: Assuming an audit = an audit document.

8002	"The <e1>company</e1> fabricates plastic <e2>chairs</e2>."
Product-Producer(e2,e1)
Comment: (a) is satisfied

8003	"The school <e1>master</e1> teaches the lesson with a <e2>stick</e2>."
Instrument-Agency(e2,e1)
Comment:

"""


def totacred(path, save_path):
    from feature import Feature
    fe = Feature()
    fe.save(path, save_path)


# 处理test文件
def process_simple(path, save_path):
    with open(path, 'r') as file:
        data = []
        lines = file.readlines()
        for i in range(int(len(lines)/4)):
            example = lines[i*4:i*4+4]
            id = example[0].strip("\n").split("	")[0]
            sentence_raw = example[0].strip("\n").split("	")[1].strip("\"")
            label = example[1].strip("\n")
            entity1 = re.search("<e1>(.*?)</e1>", sentence_raw).group(1)
            entity2 = re.search("<e2>(.*?)</e2>", sentence_raw).group(1)
            sentence = re.sub("<e1>|</e1>|<e2>|</e2>", "", sentence_raw)
            # 保证e1始终是出于支配地位
            m = re.search("\((.*?),(.*?)\)", label)
            if m:
                first, last = m.group(1, 2)
                if first == "e2":
                    entity1, entity2 = entity2, entity1
            label = re.sub("\(.*?\)", "", label)
            example_json = {"id": id,
                            "suj_text": entity1,
                            "obj_text": entity2,
                            "sentText": sentence,
                            "label": label}
            data.append(example_json)
    json.dump(data, open(save_path, 'w', encoding="UTF-8"))


def main():

    process_simple(path=train_path,save_path=train_save_raw_path)
    totacred(path=train_save_raw_path,save_path=train_save_path)

    process_simple(path=test_path, save_path=test_save_raw_path)
    totacred(path=test_save_raw_path, save_path=test_save_path)


if __name__ == "__main__":

    main()